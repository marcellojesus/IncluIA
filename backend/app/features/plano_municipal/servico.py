"""Spec: docs/sdd/fase-2/requirements/secretario/plano-estrategico-municipal.md (SPM-RF-01 a 08; RN-SPM-01 a 06).

O secretário compõe o plano da rede a partir da base calculada (planos escolares aceitos e barreiras
do Censo). A IA sugere; só o que o secretário inclui entra no rascunho. Confirmar congela uma versão,
que fica visível a cada diretor apenas nas ações que atendem a própria escola (RN-SPM-03).
"""

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.plano.modelos import HORIZONTES
from app.features.plano.servico import ErroPlano, _campo, _responsavel
from app.features.plano_municipal import base as base_rede
from app.features.plano_municipal.modelos import COBERTURAS, PRIORIDADES, AcaoMunicipal, SugestaoMunicipal, VersaoPlanoMunicipal

LIMITE_ACOES = 80


@dataclass
class EstadoMunicipal:
    base: base_rede.BaseDaRede
    sugestoes: list[SugestaoMunicipal]
    acoes: list[AcaoMunicipal]
    versoes: list[VersaoPlanoMunicipal] = field(default_factory=list)


def estado(sessao: Session, co_municipio: int) -> EstadoMunicipal:
    return EstadoMunicipal(
        base=base_rede.montar(sessao, co_municipio),
        sugestoes=list(sessao.scalars(
            select(SugestaoMunicipal)
            .where(SugestaoMunicipal.co_municipio == co_municipio, SugestaoMunicipal.estado == "pendente")
            .order_by(SugestaoMunicipal.criado_em)
        )),
        acoes=list(sessao.scalars(select(AcaoMunicipal).where(AcaoMunicipal.co_municipio == co_municipio).order_by(AcaoMunicipal.criado_em))),
        versoes=list(sessao.scalars(
            select(VersaoPlanoMunicipal).where(VersaoPlanoMunicipal.co_municipio == co_municipio).order_by(VersaoPlanoMunicipal.versao)
        )),
    )


@dataclass(frozen=True)
class EscolaAtendida:
    co_entidade: int
    item_ids: tuple[str, ...] = ()
    cobertura: str = "total"


@dataclass(frozen=True)
class DadosAcaoMunicipal:
    codigos: tuple[str, ...]
    acao: str
    justificativa: str | None
    responsavel: str | None
    prazo: str | None
    horizonte: str
    custo_estimado: str | None
    premissas: str | None
    prioridade: str
    escolas: tuple[EscolaAtendida, ...]


def _escolas_validas(base: base_rede.BaseDaRede, escolas: tuple[EscolaAtendida, ...]) -> list[dict]:
    """Só escolas da rede municipal do secretário; itens só dos planos aceitos dessas escolas."""
    itens = base.itens_por_id()
    resultado = []
    vistas = set()
    for e in escolas:
        if e.co_entidade not in base.escolas:
            raise ErroPlano("Escola fora da rede municipal.", 404)
        if e.cobertura not in COBERTURAS:
            raise ErroPlano("Cobertura deve ser total ou parcial.")
        if e.co_entidade in vistas:
            continue
        vistas.add(e.co_entidade)
        for item_id in e.item_ids:
            if item_id not in itens or itens[item_id].co_entidade != e.co_entidade:
                raise ErroPlano("Ação escolar não pertence ao plano aceito desta escola.", 404)
        resultado.append({"co_entidade": e.co_entidade, "item_ids": list(e.item_ids), "cobertura": e.cobertura})
    return resultado


def _escolas_atuais(base: base_rede.BaseDaRede, escolas: list[dict]) -> list[dict]:
    """Escolas de uma sugestão conferidas com a base de agora: se a escola teve novo plano aceito
    depois da sugestão, os itens antigos saem (a escola fica, com os itens que ainda existem)."""
    itens = base.itens_por_id()
    atuais = []
    for e in escolas:
        if e["co_entidade"] not in base.escolas:
            continue
        validos = [i for i in e.get("item_ids") or [] if i in itens and itens[i].co_entidade == e["co_entidade"]]
        atuais.append({"co_entidade": e["co_entidade"], "item_ids": validos, "cobertura": e.get("cobertura", "total")})
    return atuais


def _limpo(base: base_rede.BaseDaRede, dados: DadosAcaoMunicipal) -> tuple[dict, bool]:
    if dados.horizonte not in HORIZONTES:
        raise ErroPlano("Escolha o horizonte: LOA (exercício corrente) ou PPA (até quatro anos).")
    if dados.prioridade not in PRIORIDADES:
        raise ErroPlano("Escolha a prioridade: alta, média ou baixa.")
    if not dados.codigos or any(base.barreira(c) is None for c in dados.codigos):
        raise ErroPlano("Indique ao menos uma barreira identificada na rede.", 404)
    acao, m1 = _campo(dados.acao, obrigatorio=True)
    justificativa, m2 = _campo(dados.justificativa)
    prazo, m3 = _campo(dados.prazo, maximo=100)
    custo, m4 = _campo(dados.custo_estimado, maximo=200)
    premissas, m5 = _campo(dados.premissas)
    return {
        "codigos": list(dict.fromkeys(dados.codigos)), "acao": acao, "justificativa": justificativa,
        "responsavel": _responsavel(dados.responsavel), "prazo": prazo, "horizonte": dados.horizonte, "custo_estimado": custo,
        "premissas": premissas, "prioridade": dados.prioridade, "escolas": _escolas_validas(base, dados.escolas),
    }, any((m1, m2, m3, m4, m5))


def _conferir_limite(sessao: Session, co_municipio: int) -> None:
    total = sessao.scalar(select(func.count()).select_from(AcaoMunicipal).where(AcaoMunicipal.co_municipio == co_municipio))
    if total >= LIMITE_ACOES:
        raise ErroPlano(f"O plano municipal já tem {LIMITE_ACOES} ações. Revise as existentes antes de incluir outras.", 409)


def incluir_acao(sessao: Session, *, co_municipio: int, autor_id: str, dados: DadosAcaoMunicipal) -> bool:
    _conferir_limite(sessao, co_municipio)
    campos, mascarou = _limpo(base_rede.montar(sessao, co_municipio), dados)
    sessao.add(AcaoMunicipal(co_municipio=co_municipio, origem="secretario", autor_id=autor_id, fontes=[], **campos))
    sessao.commit()
    return mascarou


def _acao(sessao: Session, co_municipio: int, acao_id: str) -> AcaoMunicipal:
    acao = sessao.get(AcaoMunicipal, acao_id)
    if acao is None or acao.co_municipio != co_municipio:
        raise ErroPlano("Ação não encontrada.", 404)
    return acao


def editar_acao(sessao: Session, *, co_municipio: int, acao_id: str, dados: DadosAcaoMunicipal) -> bool:
    acao = _acao(sessao, co_municipio, acao_id)
    campos, mascarou = _limpo(base_rede.montar(sessao, co_municipio), dados)
    for campo, valor in campos.items():
        setattr(acao, campo, valor)
    if acao.origem == "ia":
        acao.editada = True
    sessao.commit()
    return mascarou


def remover_acao(sessao: Session, *, co_municipio: int, acao_id: str) -> None:
    sessao.delete(_acao(sessao, co_municipio, acao_id))
    sessao.commit()


def _sugestao(sessao: Session, co_municipio: int, sugestao_id: str) -> SugestaoMunicipal:
    sugestao = sessao.get(SugestaoMunicipal, sugestao_id)
    if sugestao is None or sugestao.co_municipio != co_municipio or sugestao.estado != "pendente":
        raise ErroPlano("Sugestão não encontrada.", 404)
    return sugestao


def aceitar_sugestao(
    sessao: Session, *, co_municipio: int, autor_id: str, sugestao_id: str, dados: DadosAcaoMunicipal | None = None
) -> bool:
    """RN-SPM-04: a sugestão vira ação só com a escolha do secretário; com `dados`, entra já editada."""
    sugestao = _sugestao(sessao, co_municipio, sugestao_id)
    _conferir_limite(sessao, co_municipio)
    c = sugestao.conteudo
    if dados is not None:
        campos, mascarou = _limpo(base_rede.montar(sessao, co_municipio), dados)
    else:
        campos = {k: c.get(k) for k in ("acao", "justificativa", "responsavel", "prazo", "custo_estimado", "premissas")}
        campos.update(
            codigos=[sugestao.codigo], horizonte=c.get("horizonte") if c.get("horizonte") in HORIZONTES else "PPA",
            prioridade=c.get("prioridade") if c.get("prioridade") in PRIORIDADES else "media",
            escolas=_escolas_atuais(base_rede.montar(sessao, co_municipio), c.get("escolas") or []),
        )
        mascarou = False
    sessao.add(AcaoMunicipal(
        co_municipio=co_municipio, origem="ia", editada=dados is not None, sugestao_id=sugestao.id, autor_id=autor_id,
        fontes=list(c.get("fontes") or []), **campos,
    ))
    sugestao.estado = "aceita"
    sessao.commit()
    return mascarou


def descartar_sugestao(sessao: Session, *, co_municipio: int, sugestao_id: str) -> None:
    _sugestao(sessao, co_municipio, sugestao_id).estado = "descartada"
    sessao.commit()


CAMPOS_CONGELADOS = (
    "codigos", "acao", "justificativa", "responsavel", "prazo", "horizonte", "custo_estimado", "premissas", "prioridade", "fontes",
    "escolas", "origem", "editada",
)


def confirmar(sessao: Session, *, co_municipio: int, autor_id: str, confirmado: bool) -> VersaoPlanoMunicipal:
    """SPM-RF-06 e 08: congela uma versão. Não é aprovação orçamentária, financiamento nem execução."""
    if not confirmado:
        raise ErroPlano("Confirme a versão do plano municipal.")
    atual = estado(sessao, co_municipio)
    if not atual.acoes:
        raise ErroPlano("Inclua ao menos uma ação no plano municipal.", 409)
    numero = (sessao.scalar(select(func.max(VersaoPlanoMunicipal.versao)).where(VersaoPlanoMunicipal.co_municipio == co_municipio)) or 0) + 1
    versao = VersaoPlanoMunicipal(
        co_municipio=co_municipio, versao=numero, confirmada_por=autor_id,
        acoes=[{"id": a.id, **{c: getattr(a, c) for c in CAMPOS_CONGELADOS}} for a in atual.acoes],
        base={"planos": [{"co_entidade": co, "versao": v} for co, v in sorted(atual.base.planos.items())]},
    )
    sessao.add(versao)
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="plano_municipal_confirmado", alvo_tipo="plano_municipal", alvo_id=str(co_municipio), resultado="ok",
        detalhe=f"município {co_municipio} v{numero}; {len(atual.acoes)} ação(ões)",
    ))
    sessao.commit()
    return versao


def versao(sessao: Session, co_municipio: int, numero: int) -> VersaoPlanoMunicipal:
    v = sessao.scalar(
        select(VersaoPlanoMunicipal).where(VersaoPlanoMunicipal.co_municipio == co_municipio, VersaoPlanoMunicipal.versao == numero)
    )
    if v is None:
        raise ErroPlano("Versão não encontrada.", 404)
    return v


def acoes_da_escola(sessao: Session, co_municipio: int, co_entidade: int) -> tuple[VersaoPlanoMunicipal | None, list[dict]]:
    """RN-SPM-03: o diretor vê só as ações da última versão confirmada que atendem a própria escola."""
    ultima = sessao.scalar(
        select(VersaoPlanoMunicipal).where(VersaoPlanoMunicipal.co_municipio == co_municipio).order_by(VersaoPlanoMunicipal.versao.desc())
    )
    if ultima is None:
        return None, []
    return ultima, [a for a in ultima.acoes if any(e["co_entidade"] == co_entidade for e in a.get("escolas") or [])]
