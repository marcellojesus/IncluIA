"""Publicação da Declaração de Obstáculos (DO-RF-08, RN-DO-07; PRD, "Publicação da Declaração").

Publicar é separado de emitir. A partir da versão emitida mais recente, o sistema monta a versão
pública com frases fixas, faz a checagem assistida de dados pessoais com o Guardião LGPD (local,
AD-05: o texto não vai a nenhuma IA em nuvem para ser checado) e só publica com aprovação
explícita do diretor. A versão publicada fica congelada (texto_publico) e aparece na página
pública da escola com número e data. Nada disso altera Censo, score ou faixa (RN-DO-04).
"""

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.declaracao.modelos import Declaracao, DeclaracaoItem
from app.features.declaracao.servico import ErroDeclaracao, escola_com_barreiras, versao
from app.shared.banco_gestao import agora
from app.shared.contexto_ia.barreiras import celula_pequena
from app.shared.guardiao_lgpd import proteger, verificar_regras
from app.shared.guardiao_lgpd.contexto_escolar import menciona_estudante_individual

_MARCADOR = re.compile(r"\[[A-Z_]+\]")
_DADO_REMOVIDO = "[dado pessoal removido]"


@dataclass(frozen=True)
class PontoDeAtencao:
    codigo: str
    barreira: str
    mensagem: str
    bloqueia: bool


@dataclass(frozen=True)
class ItemPublico:
    codigo: str
    eixo: str
    barreira: str
    dado_censo: str
    posicao: str
    texto_publico: str


def _frase(posicao: str, texto: str | None) -> str:
    """Frases fixas do protótipo v2: o público distingue relato, divergência e ausência de relato."""
    if posicao == "obstaculo":
        return f"A escola relata: {texto}"
    if posicao == "divergencia":
        return f"A escola informa que o dado do Censo não reflete sua realidade: {texto}"
    return "A escola não apresentou relato nesta versão."


# Cargo de pessoa única na escola ou na rede e linguagem que atribui culpa (RN-DO-08): sem nome, a
# pessoa ainda é identificável. Viram ponto de atenção; a redação final é do diretor.
_CARGO_UNICO = re.compile(
    r"\b(?:diretor[a]?|vice[- ]diretor[a]?|coordenador[a]?|secret[aá]ri[oa]|prefeit[oa]|"
    r"professor[a]? (?:do|da) (?:aee|sala de recursos)|int[eé]rprete|cuidador[a]?|monitor[a]?)\b",
    re.IGNORECASE,
)
_IMPUTACAO = re.compile(
    r"\b(?:recusou|recusa(?:m|ram)?|negou|negaram|n[aã]o quis|n[aã]o quiseram|omiss[aoõ]\w*|descaso|culpa\w*|"
    r"neglig\w*|irrespons\w*|incompet\w*)\b",
    re.IGNORECASE,
)


def _preparar(item: DeclaracaoItem, celula_pequena: bool) -> tuple[str, list[PontoDeAtencao]]:
    """Texto público do item e os pontos que o diretor precisa ver antes de publicar."""
    if item.posicao == "sem_relato" or not item.texto:
        return _frase(item.posicao, None), []
    pontos: list[PontoDeAtencao] = []
    resultado = proteger(item.texto)
    if resultado.bloqueado:
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            "O texto tem dado sensível (saúde, documento ou situação pessoal). Retifique a posição e emita nova versão antes de publicar.",
            True,
        ))
    if celula_pequena and menciona_estudante_individual(item.texto):
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            "A escola tem poucas matrículas da educação especial e o texto fala de um estudante: a comunidade saberia quem é. "
            "Retifique com redação coletiva (por exemplo, “estudantes com mobilidade reduzida”) e emita nova versão.",
            True,
        ))
    if _CARGO_UNICO.search(item.texto):
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            "O texto cita um cargo que costuma ter uma só pessoa (diretor, coordenador, secretário, intérprete…): mesmo sem nome, ela é identificável.",
            False,
        ))
    if _IMPUTACAO.search(item.texto):
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            "O texto parece atribuir culpa (“recusou”, “descaso”…). A Declaração descreve fatos e tentativas da escola, sem culpar pessoas ou órgãos.",
            False,
        ))
    if len(_MARCADOR.findall(item.texto)) >= 2:
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            "O texto tem vários trechos removidos, o que dificulta a leitura e sugere um caso individual. Considere reescrever o trecho.",
            False,
        ))
    if resultado.trechos and not resultado.bloqueado:
        tipos = ", ".join(sorted({t.tipo.lower().replace("_", " ") for t in resultado.trechos}))
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            f"O filtro encontrou possível dado pessoal ({tipos}); na versão pública ele aparece como “{_DADO_REMOVIDO}”.", False,
        ))
    if _MARCADOR.search(item.texto):
        pontos.append(PontoDeAtencao(
            item.codigo, item.barreira,
            f"O texto tem trecho de dado pessoal removido no registro; na versão pública ele aparece como “{_DADO_REMOVIDO}”. "
            "Se preferir outra redação, retifique a posição e emita nova versão.",
            False,
        ))
    publico = _MARCADOR.sub(_DADO_REMOVIDO, resultado.texto_mascarado)
    return _frase(item.posicao, publico), pontos


def previa(sessao: Session, co_entidade: int, numero: int) -> tuple[Declaracao, list[ItemPublico], list[PontoDeAtencao]]:
    declaracao = versao(sessao, co_entidade, numero)
    pequena = celula_pequena(escola_com_barreiras(co_entidade).escola)
    itens, pontos = [], []
    for item in declaracao.itens:
        if declaracao.publicada_em and item.texto_publico:
            itens.append(ItemPublico(item.codigo, item.eixo, item.barreira, item.dado_censo, item.posicao, item.texto_publico))
            continue
        texto, achados = _preparar(item, pequena)
        itens.append(ItemPublico(item.codigo, item.eixo, item.barreira, item.dado_censo, item.posicao, texto))
        pontos += achados
    # O conjunto dos textos também é conferido: um dado pode estar partido entre itens.
    conjunto = "\n".join(i.texto for i in declaracao.itens if i.texto)
    if not declaracao.publicada_em and conjunto and verificar_regras(conjunto).bloqueado:
        pontos.append(PontoDeAtencao("conjunto", "Declaração inteira", "A combinação dos textos tem dado sensível. Revise as posições e emita nova versão.", True))
    return declaracao, itens, pontos


def publicar(sessao: Session, *, co_entidade: int, numero: int, autor_id: str, aprovado: bool) -> Declaracao:
    if not aprovado:
        raise ErroDeclaracao("Revise a versão pública e confirme a aprovação para publicar.")
    ultima = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade).order_by(Declaracao.versao.desc()))
    if ultima is None or ultima.versao != numero:
        raise ErroDeclaracao("Só a versão emitida mais recente pode ser publicada.", 409)
    if ultima.publicada_em is not None:
        raise ErroDeclaracao("Esta versão já está publicada.", 409)

    declaracao, itens, pontos = previa(sessao, co_entidade, numero)
    bloqueios = [p for p in pontos if p.bloqueia]
    if bloqueios:
        raise ErroDeclaracao(
            "A versão não pode ser publicada: " + "; ".join(f"{p.codigo} ({p.barreira})" for p in bloqueios)
            + " tem dado sensível. Retifique e emita nova versão.",
            409,
        )
    publicos = {i.codigo: i.texto_publico for i in itens}
    for item in declaracao.itens:
        item.texto_publico = publicos[item.codigo]
    declaracao.publicada_em = agora()
    declaracao.publicada_por = autor_id
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="declaracao_publicada", alvo_tipo="declaracao", alvo_id=declaracao.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}; {len(pontos)} ponto(s) de atenção",
    ))
    sessao.commit()
    return declaracao


MOTIVOS_RETIRADA = ("decisao_da_escola", "dado_pessoal", "pedido_de_titular", "erro_de_conteudo", "outro")


def retirar(sessao: Session, *, co_entidade: int, numero: int, autor_id: str, motivo: str) -> Declaracao:
    """Tira a versão da página pública (revisão do AgLGPD: sem retirada, um vazamento ficaria no ar e
    um pedido de titular, LGPD art. 18, não teria como ser atendido). A versão emitida continua
    guardada e visível à secretaria."""
    if motivo not in MOTIVOS_RETIRADA:
        raise ErroDeclaracao("Escolha o motivo da retirada.")
    declaracao = versao(sessao, co_entidade, numero)
    if declaracao.publicada_em is None or declaracao.retirada_em is not None:
        raise ErroDeclaracao("Esta versão não está publicada.", 409)
    declaracao.retirada_em = agora()
    declaracao.retirada_por = autor_id
    declaracao.retirada_motivo = motivo
    from app.features.plano.publicacao import retirar_com_a_declaracao  # importação tardia: o plano depende da declaração

    retirar_com_a_declaracao(sessao, co_entidade=co_entidade, autor_id=autor_id, motivo=motivo)
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="declaracao_retirada", alvo_tipo="declaracao", alvo_id=declaracao.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}; {motivo}",
    ))
    sessao.commit()
    return declaracao


def publicada(sessao: Session, co_entidade: int) -> Declaracao | None:
    """Última versão publicada e não retirada da escola, para a página pública (sem autoria nem relato)."""
    return sessao.scalar(
        select(Declaracao)
        .where(Declaracao.co_entidade == co_entidade, Declaracao.publicada_em.is_not(None), Declaracao.retirada_em.is_(None))
        .order_by(Declaracao.versao.desc())
    )
