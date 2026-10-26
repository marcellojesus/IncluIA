"""Spec: docs/sdd/fase-2/requirements/diretor/plano-acao-escolar.md e business-rules (RN-PAE-00 a 05).

O plano parte de uma Declaração emitida e registra a versão usada. A IA propõe; só ações aceitas
ou escritas pelo diretor entram no rascunho; submeter congela uma versão para a secretaria.
"""

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.declaracao.modelos import Declaracao
from app.features.declaracao.servico import TAMANHO_MAXIMO_TEXTO, TAMANHO_MINIMO_TEXTO, ErroDeclaracao, escola_com_barreiras
from app.features.plano.modelos import HORIZONTES, AcaoPlano, ItemVersaoPlano, Plano, SugestaoPlano, VersaoPlano
from app.shared.guardiao_lgpd import TextoBloqueado, proteger

ErroPlano = ErroDeclaracao
LIMITE_ACOES = 40


@dataclass
class EstadoPlano:
    plano: Plano
    base: Declaracao
    ultima_declaracao: int
    sugestoes: list[SugestaoPlano]
    acoes: list[AcaoPlano]
    versoes: list[VersaoPlano] = field(default_factory=list)

    @property
    def desatualizado(self) -> bool:
        return self.base.versao < self.ultima_declaracao

    @property
    def em_analise(self) -> VersaoPlano | None:
        return next((v for v in reversed(self.versoes) if v.estado == "aguardando_analise"), None)

    @property
    def motivo_para_nao_submeter(self) -> str | None:
        if self.em_analise:
            return f"A versão {self.em_analise.versao} está em análise pela secretaria."
        if not self.acoes:
            return "Inclua ao menos uma ação no plano."
        return None


def _ultima_declaracao(sessao: Session, co_entidade: int) -> Declaracao | None:
    return sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade).order_by(Declaracao.versao.desc()))


def estado(sessao: Session, co_entidade: int) -> EstadoPlano:
    """PAE-RF-00: sem Declaração emitida, o plano não começa."""
    ultima = _ultima_declaracao(sessao, co_entidade)
    if ultima is None:
        raise ErroPlano("Emita a Declaração de Obstáculos para começar o Plano de Ação.", 409)
    plano = sessao.get(Plano, co_entidade)
    if plano is None:
        plano = Plano(co_entidade=co_entidade, declaracao_versao=ultima.versao)
        sessao.add(plano)
        sessao.commit()
    base = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade, Declaracao.versao == plano.declaracao_versao))
    sugestoes = list(sessao.scalars(
        select(SugestaoPlano)
        .where(SugestaoPlano.co_entidade == co_entidade, SugestaoPlano.estado == "pendente", SugestaoPlano.declaracao_versao == plano.declaracao_versao)
        .order_by(SugestaoPlano.criado_em)
    ))
    acoes = list(sessao.scalars(select(AcaoPlano).where(AcaoPlano.co_entidade == co_entidade).order_by(AcaoPlano.criado_em)))
    versoes = list(sessao.scalars(select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade).order_by(VersaoPlano.versao)))
    return EstadoPlano(plano, base, ultima.versao, sugestoes, acoes, versoes)


def item_da_base(atual: EstadoPlano, codigo: str):
    for item in atual.base.itens:
        if item.codigo == codigo:
            return item
    raise ErroPlano("Esta barreira não está na Declaração usada como base.", 404)


def atualizar_base(sessao: Session, co_entidade: int) -> None:
    """Passa a usar a Declaração emitida mais recente; as ações ficam, as sugestões antigas saem."""
    atual = estado(sessao, co_entidade)
    atual.plano.declaracao_versao = atual.ultima_declaracao
    for sugestao in atual.sugestoes:
        sugestao.estado = "descartada"
    sessao.commit()


# --- Ações ---------------------------------------------------------------------------------------

@dataclass(frozen=True)
class DadosAcao:
    codigo: str
    acao: str
    relacao: str | None
    responsavel: str | None
    prazo: str | None
    horizonte: str
    custo_estimado: str | None
    premissas: str | None


AVISO_MASCARA = "Trechos com dados pessoais foram trocados por marcadores como [NOME]. Confira o texto da ação."
AVISO_RESPONSAVEL = "Indique o cargo ou órgão responsável (por exemplo, \"direção da escola\"), não o nome da pessoa."


def _campo(texto: str | None, *, obrigatorio: bool = False, minimo: int = TAMANHO_MINIMO_TEXTO, maximo: int = TAMANHO_MAXIMO_TEXTO) -> tuple[str | None, bool]:
    """Texto do diretor pelo Guardião LGPD (AD-05): mascarado, com aviso; dado de risco alto bloqueia."""
    texto = (texto or "").strip()
    if not texto:
        if obrigatorio:
            raise ErroPlano("Descreva a ação antes de salvar.")
        return None, False
    if obrigatorio and len(texto) < minimo:
        raise ErroPlano("O texto da ação está curto demais.")
    if len(texto) > maximo:
        raise ErroPlano(f"O texto passa de {maximo} caracteres.")
    resultado = proteger(texto)
    if resultado.bloqueado:
        raise ErroPlano(str(TextoBloqueado(resultado.motivos_bloqueio, inicio="A ação não foi salva")), 422)
    return resultado.texto_mascarado, bool(resultado.trechos)


def _responsavel(texto: str | None) -> str | None:
    """RN-PAE: responsável é cargo ou órgão. Nome de pessoa é recusado, não mascarado (a ação perderia sentido)."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if len(texto) > 200:
        raise ErroPlano("O responsável passa de 200 caracteres.")
    resultado = proteger(texto)
    if resultado.trechos:
        raise ErroPlano(AVISO_RESPONSAVEL, 422)
    return texto


def _limpo(dados: DadosAcao) -> tuple[dict, bool]:
    """Campos da ação prontos para gravar e se algum trecho foi mascarado (para avisar o diretor)."""
    if dados.horizonte not in HORIZONTES:
        raise ErroPlano("Escolha o horizonte: LOA (exercício corrente) ou PPA (até quatro anos).")
    acao, m1 = _campo(dados.acao, obrigatorio=True)
    relacao, m2 = _campo(dados.relacao)
    prazo, m3 = _campo(dados.prazo, maximo=100)
    custo, m4 = _campo(dados.custo_estimado, maximo=200)
    premissas, m5 = _campo(dados.premissas)
    campos = {
        "acao": acao, "relacao": relacao, "responsavel": _responsavel(dados.responsavel), "prazo": prazo,
        "horizonte": dados.horizonte, "custo_estimado": custo, "premissas": premissas,
    }
    return campos, any((m1, m2, m3, m4, m5))


def _conferir_limite(sessao: Session, co_entidade: int) -> None:
    total = sessao.scalar(select(func.count()).select_from(AcaoPlano).where(AcaoPlano.co_entidade == co_entidade))
    if total >= LIMITE_ACOES:
        raise ErroPlano(f"O plano já tem {LIMITE_ACOES} ações. Revise as existentes antes de incluir outras.", 409)


def incluir_acao(sessao: Session, *, co_entidade: int, autor_id: str, dados: DadosAcao) -> bool:
    """Devolve se algum trecho foi mascarado."""
    atual = estado(sessao, co_entidade)
    item_da_base(atual, dados.codigo)
    _conferir_limite(sessao, co_entidade)
    campos, mascarou = _limpo(dados)
    sessao.add(AcaoPlano(co_entidade=co_entidade, codigo=dados.codigo, origem="diretor", autor_id=autor_id, fontes=[], **campos))
    sessao.commit()
    return mascarou


def editar_acao(sessao: Session, *, co_entidade: int, acao_id: str, dados: DadosAcao) -> bool:
    """Devolve se algum trecho foi mascarado."""
    acao = sessao.get(AcaoPlano, acao_id)
    if acao is None or acao.co_entidade != co_entidade:
        raise ErroPlano("Ação não encontrada.", 404)
    item_da_base(estado(sessao, co_entidade), dados.codigo)
    campos, mascarou = _limpo(dados)
    for campo, valor in campos.items():
        setattr(acao, campo, valor)
    acao.codigo = dados.codigo
    if acao.origem == "ia":
        acao.editada = True  # PAE-RF-05: alteração do diretor identificável
    sessao.commit()
    return mascarou


def remover_acao(sessao: Session, *, co_entidade: int, acao_id: str) -> None:
    acao = sessao.get(AcaoPlano, acao_id)
    if acao is None or acao.co_entidade != co_entidade:
        raise ErroPlano("Ação não encontrada.", 404)
    sessao.delete(acao)
    sessao.commit()


def aceitar_sugestao(sessao: Session, *, co_entidade: int, autor_id: str, sugestao_id: str, dados: DadosAcao | None = None) -> bool:
    """RN-PAE-01: a sugestão vira ação só com a escolha explícita do diretor. Com `dados`, ela entra
    já editada por ele ("Editar e incluir"), marcada como editada (PAE-RF-05). Devolve se houve máscara."""
    sugestao = sessao.get(SugestaoPlano, sugestao_id)
    if sugestao is None or sugestao.co_entidade != co_entidade or sugestao.estado != "pendente":
        raise ErroPlano("Sugestão não encontrada.", 404)
    _conferir_limite(sessao, co_entidade)
    c = sugestao.conteudo
    if dados is not None:
        if dados.codigo != sugestao.codigo:
            item_da_base(estado(sessao, co_entidade), dados.codigo)
        campos, mascarou = _limpo(dados)
        codigo = dados.codigo
    else:
        campos = {
            "acao": c["acao"], "relacao": c.get("relacao"), "responsavel": c.get("responsavel"), "prazo": c.get("prazo"),
            "horizonte": c.get("horizonte") if c.get("horizonte") in HORIZONTES else "PPA",
            "custo_estimado": c.get("custo_estimado"), "premissas": c.get("premissas"),
        }
        mascarou, codigo = False, sugestao.codigo
    acao = AcaoPlano(
        co_entidade=co_entidade, codigo=codigo, fontes=list(c.get("fontes") or []), origem="ia", editada=dados is not None,
        sugestao_id=sugestao.id, autor_id=autor_id, **campos,
    )
    sugestao.estado = "aceita"
    sessao.add(acao)
    sessao.commit()
    return mascarou


def descartar_sugestao(sessao: Session, *, co_entidade: int, sugestao_id: str) -> None:
    sugestao = sessao.get(SugestaoPlano, sugestao_id)
    if sugestao is None or sugestao.co_entidade != co_entidade or sugestao.estado != "pendente":
        raise ErroPlano("Sugestão não encontrada.", 404)
    sugestao.estado = "descartada"
    sessao.commit()


# --- Submissão -----------------------------------------------------------------------------------

def submeter(sessao: Session, *, co_entidade: int, autor_id: str, confirmado: bool) -> VersaoPlano:
    """PAE-RF-06 e RN-PAE-04: confirmação explícita; a versão enviada fica congelada."""
    if not confirmado:
        raise ErroPlano("Confirme o envio do plano à secretaria.")
    atual = estado(sessao, co_entidade)
    motivo = atual.motivo_para_nao_submeter
    if motivo:
        raise ErroPlano(motivo, 409)
    barreiras = {i.codigo: i.barreira for i in atual.base.itens}
    numero = (sessao.scalar(select(func.max(VersaoPlano.versao)).where(VersaoPlano.co_entidade == co_entidade)) or 0) + 1
    escola = escola_com_barreiras(co_entidade).escola
    versao = VersaoPlano(
        co_entidade=co_entidade, co_municipio=escola["co_municipio"], versao=numero,
        declaracao_versao=atual.base.versao, submetida_por=autor_id,
    )
    sessao.add(versao)
    sessao.flush()
    for ordem, a in enumerate(atual.acoes):
        sessao.add(ItemVersaoPlano(
            versao_id=versao.id, ordem=ordem, codigo=a.codigo, barreira=barreiras.get(a.codigo, a.codigo), acao=a.acao,
            relacao=a.relacao, responsavel=a.responsavel, prazo=a.prazo, horizonte=a.horizonte, custo_estimado=a.custo_estimado,
            premissas=a.premissas, fontes=list(a.fontes or []), origem=a.origem, editada=a.editada, acao_id=a.id,
        ))
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="plano_submetido", alvo_tipo="plano", alvo_id=versao.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}; declaração v{atual.base.versao}; {len(atual.acoes)} ação(ões)",
    ))
    sessao.commit()
    sessao.refresh(versao)
    return versao


def versao_do_plano(sessao: Session, co_entidade: int, numero: int) -> VersaoPlano:
    versao = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.versao == numero))
    if versao is None:
        raise ErroPlano("Versão do plano não encontrada.", 404)
    return versao
