"""Spec: docs/sdd/fase-2/requirements/secretario/fila-revisao-planos.md e business-rules (RN-SFR-01 a 06).

O secretário vê só as versões enviadas pelas escolas do município do seu vínculo; rascunhos e
sugestões da IA nunca aparecem. A decisão vale para uma versão exata (RN-SFR-03) e só a versão
mais recente, ainda em análise, pode ser decidida. Aceitar não é financiamento (RN-SFR-05).
"""

from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.declaracao.modelos import Declaracao
from app.features.plano.modelos import ApontamentoPlano, VersaoPlano
from app.features.plano.servico import ErroPlano
from app.shared.banco_gestao import agora
from app.shared.guardiao_lgpd import TextoBloqueado, proteger

DECISOES = {"aceitar": "aceito", "ajustes": "ajustes_solicitados", "reprovar": "reprovado"}
COMENTARIO_MINIMO = 10
COMENTARIO_MAXIMO = 2000
_EXIGE_COMENTARIO = {
    "ajustes": "Escreva a orientação de ajuste para a escola.",
    "reprovar": "Escreva o motivo da reprovação.",
}


@dataclass
class LinhaFila:
    co_entidade: int
    ultima: VersaoPlano
    ultima_declaracao: int
    versoes: int


def ultima_declaracao(sessao: Session, co_entidade: int) -> int:
    return sessao.scalar(select(Declaracao.versao).where(Declaracao.co_entidade == co_entidade).order_by(Declaracao.versao.desc())) or 0


def fila(sessao: Session, co_municipio: int) -> list[LinhaFila]:
    """RN-SFR-02: só escolas com ao menos uma versão enviada; em análise primeiro, depois as mais recentes.
    O filtro é só por município: vale porque o piloto vincula apenas escolas da rede municipal (acesso/servico).
    Se outras redes entrarem, gravar a rede na versão e filtrar por ela também."""
    por_escola: dict[int, list[VersaoPlano]] = {}
    for v in sessao.scalars(select(VersaoPlano).where(VersaoPlano.co_municipio == co_municipio).order_by(VersaoPlano.versao)):
        por_escola.setdefault(v.co_entidade, []).append(v)
    linhas = [LinhaFila(co, vs[-1], ultima_declaracao(sessao, co), len(vs)) for co, vs in por_escola.items()]
    linhas.sort(key=lambda l: l.ultima.submetida_em, reverse=True)
    linhas.sort(key=lambda l: l.ultima.estado != "aguardando_analise")
    return linhas


def versoes_da_escola(sessao: Session, co_municipio: int, co_entidade: int) -> list[VersaoPlano]:
    """Escola de outra rede, ou sem versão enviada, responde como inexistente (RN-07 do acesso)."""
    versoes = list(sessao.scalars(
        select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.co_municipio == co_municipio).order_by(VersaoPlano.versao)
    ))
    if not versoes:
        raise ErroPlano("Plano não encontrado.", 404)
    return versoes


def versao(versoes: list[VersaoPlano], numero: int) -> VersaoPlano:
    for v in versoes:
        if v.versao == numero:
            return v
    raise ErroPlano("Versão não encontrada.", 404)


def _comentario(decisao: str, texto: str | None) -> tuple[str | None, bool]:
    """Comentário do secretário pelo Guardião LGPD (AD-05): mascarado, com aviso; dado de risco alto bloqueia."""
    texto = (texto or "").strip()
    if not texto:
        if decisao in _EXIGE_COMENTARIO:
            raise ErroPlano(_EXIGE_COMENTARIO[decisao])
        return None, False
    if decisao in _EXIGE_COMENTARIO and len(texto) < COMENTARIO_MINIMO:
        raise ErroPlano("O comentário está curto demais para orientar a escola.")
    if len(texto) > COMENTARIO_MAXIMO:
        raise ErroPlano(f"O comentário passa de {COMENTARIO_MAXIMO} caracteres.")
    return _pelo_guardiao(texto)


def _pelo_guardiao(texto: str) -> tuple[str, bool]:
    resultado = proteger(texto)
    if resultado.bloqueado:
        raise ErroPlano(str(TextoBloqueado(
            resultado.motivos_bloqueio, inicio="A decisão não foi registrada",
            orientacao="Reescreva a orientação sem dados que identifiquem estudantes ou profissionais.",
        )), 422)
    return resultado.texto_mascarado, bool(resultado.trechos)


@dataclass(frozen=True)
class Marcacao:
    """Barreira (sem item) ou ação (com item) apontada para ajuste, com nota opcional."""

    codigo: str
    item_id: str | None = None
    texto: str | None = None


APONTAMENTOS_MAXIMO = 60
APONTAMENTO_MAXIMO = 500


def _apontamentos(sessao: Session, alvo: VersaoPlano, decisao: str, marcacoes: list[Marcacao]) -> tuple[list[ApontamentoPlano], bool]:
    """Só ajustes e reprovação apontam itens. O código deve ser de barreira da Declaração base; o
    item, da própria versão (nunca de outra escola)."""
    if not marcacoes:
        return [], False
    if decisao == "aceitar":
        raise ErroPlano("Aceitar não leva apontamentos de ajuste.")
    if len(marcacoes) > APONTAMENTOS_MAXIMO:
        raise ErroPlano(f"Marque no máximo {APONTAMENTOS_MAXIMO} pontos de ajuste.")
    base = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == alvo.co_entidade, Declaracao.versao == alvo.declaracao_versao))
    codigos = {i.codigo for i in base.itens} if base else set()
    itens = {i.id: i for i in alvo.itens}
    mascarou = False
    apontamentos = []
    for m in marcacoes:
        if m.item_id is not None:
            item = itens.get(m.item_id)
            if item is None:
                raise ErroPlano("Ação apontada não pertence a esta versão.", 404)
            codigo = item.codigo
        elif m.codigo in codigos:
            codigo = m.codigo
        else:
            raise ErroPlano("Barreira apontada não está na Declaração usada pelo plano.", 404)
        texto = (m.texto or "").strip() or None
        if texto:
            if len(texto) > APONTAMENTO_MAXIMO:
                raise ErroPlano(f"A nota de ajuste passa de {APONTAMENTO_MAXIMO} caracteres.")
            texto, m_ = _pelo_guardiao(texto)
            mascarou = mascarou or m_
        apontamentos.append(ApontamentoPlano(versao_id=alvo.id, codigo=codigo, item_id=m.item_id, texto=texto))
    return apontamentos, mascarou


def decidir(
    sessao: Session, *, secretario_id: str, co_municipio: int, co_entidade: int, numero: int, decisao: str, comentario: str | None,
    marcacoes: list[Marcacao] | None = None,
) -> bool:
    """SFR-RF-04 e 05; RN-SFR-03 e 04. Devolve se algum texto da secretaria teve trechos mascarados."""
    if decisao not in DECISOES:
        raise ErroPlano("Escolha aceitar, solicitar ajustes ou reprovar.")
    versoes = versoes_da_escola(sessao, co_municipio, co_entidade)
    alvo = versao(versoes, numero)
    if alvo is not versoes[-1]:
        raise ErroPlano("Esta versão foi substituída por uma mais nova; decida sobre a versão atual.", 409)
    if alvo.estado != "aguardando_analise":
        raise ErroPlano("Esta versão já foi decidida.", 409)
    texto, mascarou = _comentario(decisao, comentario)
    apontamentos, mascarou_notas = _apontamentos(sessao, alvo, decisao, marcacoes or [])
    mascarou = mascarou or mascarou_notas
    # Atualização condicional: entre dois secretários decidindo ao mesmo tempo, só o primeiro grava.
    gravadas = sessao.execute(
        update(VersaoPlano)
        .where(VersaoPlano.id == alvo.id, VersaoPlano.estado == "aguardando_analise")
        .values(estado=DECISOES[decisao], decidida_por=secretario_id, decidida_em=agora(), comentario=texto)
    ).rowcount
    if gravadas != 1:
        sessao.rollback()
        raise ErroPlano("Esta versão já foi decidida.", 409)
    sessao.add_all(apontamentos)
    sessao.add(EventoAuditoria(
        ator_id=secretario_id, acao=f"plano_{DECISOES[decisao]}", alvo_tipo="plano", alvo_id=alvo.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}; {len(apontamentos)} apontamento(s)",  # sem textos
    ))
    sessao.commit()
    sessao.expire_all()
    return mascarou
