"""Publicação do Plano de Ação aceito (decisões do responsável em 2026-10-26).

- Quem publica é o diretor, depois que a secretaria aceitou a versão, com prévia e checagem de dados
  pessoais pelo Guardião LGPD local (mesmo modelo da Declaração).
- O plano só aparece na página pública junto com a Declaração publicada: ele responde aos obstáculos
  relatados, e sem a Declaração revelaria indiretamente o que a escola optou por não publicar.
- O texto público fica congelado; a versão pode ser retirada pelo diretor ou pela administração.
- Aceitar não é financiamento (RN-SFR-05): a página pública diz isso.
"""

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.declaracao.publicacao import _DADO_REMOVIDO, _IMPUTACAO, _MARCADOR, MOTIVOS_RETIRADA
from app.features.declaracao.publicacao import publicada as declaracao_publicada
from app.features.plano.fontes import citacoes
from app.features.plano.modelos import ItemVersaoPlano, VersaoPlano
from app.features.declaracao.servico import escola_com_barreiras
from app.features.plano.servico import ErroPlano
from app.shared.banco_gestao import agora
from app.shared.contexto_ia.barreiras import celula_pequena
from app.shared.guardiao_lgpd import proteger, verificar_regras
from app.shared.guardiao_lgpd.contexto_escolar import menciona_estudante_individual

CAMPOS_PUBLICOS = ("acao", "relacao", "responsavel", "prazo", "custo_estimado")


@dataclass(frozen=True)
class PontoDeAtencao:
    item: str
    """Ação a que o ponto se refere (texto curto), ou "Plano inteiro"."""
    mensagem: str
    bloqueia: bool


MOTIVOS_LGPD = ("dado_pessoal", "pedido_de_titular")

# Responsável ligado ao atendimento de estudantes com deficiência: expõe o profissional e, em escola
# com poucas matrículas da educação especial, também o estudante (revisão do AgLGPD, 2026-10-26).
# Diretor e secretaria são agentes públicos no exercício da função: não geram aviso.
_CARGO_ATENDIMENTO = re.compile(
    r"\b(?:professor[a]?(?:\(a\))? (?:do|da) (?:aee|sala de recursos)|int[eé]rprete|cuidador[a]?|monitor[a]?|"
    r"profissional de apoio|acompanhante)\b",
    re.IGNORECASE,
)


def _texto_publico(texto: str | None, pequena: bool) -> tuple[str | None, list[str], bool]:
    """(texto para o público, mensagens de atenção, bloqueia)."""
    if not texto:
        return None, [], False
    resultado = proteger(texto)
    if resultado.bloqueado:
        return None, ["Há dado sensível (saúde, documento ou situação pessoal). Edite a ação e envie nova versão à secretaria."], True
    if pequena and menciona_estudante_individual(texto):
        return None, [
            "A escola tem poucas matrículas da educação especial e o texto fala de um estudante: a comunidade saberia quem é. "
            "Reescreva de forma coletiva (por exemplo, “estudantes com mobilidade reduzida”) e envie nova versão."
        ], True
    mensagens = []
    if _IMPUTACAO.search(texto):
        mensagens.append("O texto parece atribuir culpa (“recusou”, “descaso”…). O plano descreve ações, sem culpar pessoas ou órgãos.")
    if resultado.trechos or _MARCADOR.search(texto):
        mensagens.append(f"Há trecho com possível dado pessoal; na versão pública ele aparece como “{_DADO_REMOVIDO}”.")
    return _MARCADOR.sub(_DADO_REMOVIDO, resultado.texto_mascarado), mensagens, False


def _preparar(item: ItemVersaoPlano, pequena: bool) -> tuple[dict, list[PontoDeAtencao]]:
    legiveis = citacoes(set(item.fontes or []))
    publico: dict = {
        "codigo": item.codigo, "barreira": item.barreira, "horizonte": item.horizonte,
        "fontes": [legiveis[f] for f in item.fontes or [] if f in legiveis],  # citação legível, congelada com o texto
    }
    pontos = []
    rotulo = (item.acao or "")[:80]
    for campo in CAMPOS_PUBLICOS:
        texto, mensagens, bloqueia = _texto_publico(getattr(item, campo), pequena)
        publico[campo] = texto
        pontos += [PontoDeAtencao(rotulo, m, bloqueia) for m in mensagens]
    if item.responsavel and _CARGO_ATENDIMENTO.search(item.responsavel):
        if pequena:
            pontos.append(PontoDeAtencao(
                rotulo, "Com poucas matrículas da educação especial, indicar o profissional de atendimento como responsável identifica "
                "ele e o estudante. Indique a equipe ou o órgão (ex.: “direção da escola”) e envie nova versão.", True,
            ))
        else:
            pontos.append(PontoDeAtencao(
                rotulo, "O responsável é um profissional de atendimento que costuma ser uma só pessoa na escola: mesmo sem nome, fica "
                "identificável. Considere indicar a equipe ou o órgão.", False,
            ))
    return publico, pontos


def ultima_aceita(sessao: Session, co_entidade: int) -> VersaoPlano | None:
    return sessao.scalar(
        select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.estado == "aceito").order_by(VersaoPlano.versao.desc())
    )


def _versao(sessao: Session, co_entidade: int, numero: int) -> VersaoPlano:
    versao = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.versao == numero))
    if versao is None:
        raise ErroPlano("Versão não encontrada.", 404)
    return versao


def motivo_para_nao_publicar(sessao: Session, co_entidade: int, versao: VersaoPlano) -> str | None:
    if versao.estado != "aceito":
        return "Só um plano aceito pela secretaria pode ser publicado."
    aceita = ultima_aceita(sessao, co_entidade)
    if aceita is None or aceita.versao != versao.versao:
        return "Só a versão aceita mais recente pode ser publicada."
    if versao.publicada_em and not versao.retirada_em:
        return "Esta versão já está publicada."
    if versao.retirada_em:
        # Como na Declaração: versão retirada não volta ao ar (a retirada pode ter sido por dado pessoal ou
        # pedido de titular). O texto corrigido sai como nova versão, enviada e aceita de novo.
        return "Esta versão foi retirada da página pública. Para publicar de novo, envie uma nova versão à secretaria."
    if declaracao_publicada(sessao, co_entidade) is None:
        return "Publique a Declaração de Obstáculos antes: o plano aparece ao público junto com ela."
    return None


def previa(sessao: Session, co_entidade: int, numero: int) -> tuple[VersaoPlano, list[dict], list[PontoDeAtencao], str | None]:
    versao = _versao(sessao, co_entidade, numero)
    if versao.publicada_em and not versao.retirada_em:
        return versao, [i.publico for i in versao.itens if i.publico], [], motivo_para_nao_publicar(sessao, co_entidade, versao)
    pequena = celula_pequena(escola_com_barreiras(co_entidade).escola)
    itens, pontos = [], []
    for item in versao.itens:
        publico, achados = _preparar(item, pequena)
        itens.append(publico)
        pontos += achados
    # Um dado pode estar partido entre ações: o conjunto do que vai ao público também é conferido.
    conjunto = "\n".join(getattr(i, campo) for i in versao.itens for campo in CAMPOS_PUBLICOS if getattr(i, campo))
    if conjunto and (verificar_regras(conjunto).bloqueado or (pequena and menciona_estudante_individual(conjunto))):
        pontos.append(PontoDeAtencao("Plano inteiro", "A combinação dos textos identifica um estudante ou tem dado sensível. Edite as ações e envie nova versão.", True))
    motivo = motivo_para_nao_publicar(sessao, co_entidade, versao)
    if motivo is None and any(p.bloqueia for p in pontos):
        motivo = "Há dado sensível no plano; ele não pode ser publicado nesta versão."
    return versao, itens, pontos, motivo




def _limpar_cache_publico(co_entidade: int) -> None:
    from app.features.declaracao.router_publico import limpar_cache  # importação tardia: o router público lê este módulo

    limpar_cache(co_entidade)


def publicar(sessao: Session, *, co_entidade: int, numero: int, autor_id: str, aprovado: bool) -> VersaoPlano:
    if not aprovado:
        raise ErroPlano("Revise a versão pública e confirme a aprovação para publicar.")
    versao, itens, pontos, motivo = previa(sessao, co_entidade, numero)
    if motivo:
        raise ErroPlano(motivo, 409)
    for item, publico in zip(versao.itens, itens, strict=True):
        item.publico = publico
    # Uma versão publicada por vez: a anterior sai da página pública.
    for anterior in sessao.scalars(
        select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.publicada_em.is_not(None), VersaoPlano.retirada_em.is_(None))
    ):
        anterior.retirada_em = agora()
        anterior.retirada_por = autor_id
        anterior.retirada_motivo = "substituida"
    versao.publicada_em = agora()
    versao.publicada_por = autor_id
    versao.retirada_em = versao.retirada_por = versao.retirada_motivo = None
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="plano_publicado", alvo_tipo="plano", alvo_id=versao.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}; {len(pontos)} ponto(s) de atenção",
    ))
    sessao.commit()
    _limpar_cache_publico(co_entidade)
    return versao


def retirar(sessao: Session, *, co_entidade: int, numero: int, autor_id: str, motivo: str) -> VersaoPlano:
    if motivo not in MOTIVOS_RETIRADA:
        raise ErroPlano("Escolha o motivo da retirada.")
    versao = _versao(sessao, co_entidade, numero)
    if versao.publicada_em is None or versao.retirada_em is not None:
        raise ErroPlano("Esta versão não está publicada.", 409)
    _marcar_retirada(sessao, versao, autor_id, motivo)
    sessao.commit()
    _limpar_cache_publico(co_entidade)
    return versao


def _marcar_retirada(sessao: Session, versao: VersaoPlano, autor_id: str, motivo: str) -> None:
    versao.retirada_em = agora()
    versao.retirada_por = autor_id
    versao.retirada_motivo = motivo
    if motivo in MOTIVOS_LGPD:
        # O texto público congelado sai do banco; o original segue guardado para a secretaria.
        for item in versao.itens:
            item.publico = None
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="plano_retirado", alvo_tipo="plano", alvo_id=versao.id, resultado="ok",
        detalhe=f"escola {versao.co_entidade} v{versao.versao}; {motivo}",
    ))


def retirar_com_a_declaracao(sessao: Session, *, co_entidade: int, autor_id: str, motivo: str) -> None:
    """Declaração retirada por dado pessoal ou pedido de titular leva junto o plano publicado: senão ele
    voltaria sozinho ao ar quando outra Declaração fosse publicada (revisão do AgLGPD, M2). Quem chama faz o commit."""
    if motivo not in MOTIVOS_LGPD:
        return
    for versao in sessao.scalars(
        select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.publicada_em.is_not(None), VersaoPlano.retirada_em.is_(None))
    ):
        _marcar_retirada(sessao, versao, autor_id, motivo)


def publicado(sessao: Session, co_entidade: int) -> VersaoPlano | None:
    """Versão publicada e não retirada, para a página pública. Só é exibida se houver Declaração publicada."""
    if declaracao_publicada(sessao, co_entidade) is None:
        return None
    return sessao.scalar(
        select(VersaoPlano)
        .where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.publicada_em.is_not(None), VersaoPlano.retirada_em.is_(None))
        .order_by(VersaoPlano.versao.desc())
    )
