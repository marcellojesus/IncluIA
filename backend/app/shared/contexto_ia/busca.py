"""Busca híbrida na base normativa (AD-08, camada C3): palavra-chave (FTS5) + vetor, fundidas por
RRF (Reciprocal Rank Fusion). Sem embeddings — base gerada sem eles, modelo diferente do da consulta
ou falha da API — segue só por palavra-chave e registra o motivo.

A pergunta chega como `TextoProtegido`: o vetor é gerado pelo `ai_client`, depois do Guardião.
"""

import re
import unicodedata
from dataclasses import dataclass

from app.shared import ai_client
from app.shared.contexto_ia.base_normativa import BaseNormativa
from app.shared.guardiao_lgpd import TextoProtegido

_CANDIDATOS = 20  # resultados de cada busca antes da fusão
_K_RRF = 60
# Peso da palavra-chave na fusão com o vetor. Com peso 1, um trecho mediano nas duas listas passava
# à frente do 1º lugar do vetor; com 0,5, a híbrida empatou com o vetor puro no conjunto de
# avaliação (7 de 8 em 1º lugar, 8 de 8 entre os 3 primeiros). Provisório: são só 8 perguntas.
PESO_PALAVRA_CHAVE = 0.5

_PALAVRAS_VAZIAS = frozenset(
    """
    a ao aos as com como da das de do dos e ela ele em entre essa esse esta este eu foi ha isso
    ja mais mas me meu minha na nao nas nem no nos nossa nosso num numa o os ou para pela pelo
    pode podem podemos por qual quais quando que quem se sem ser seu sua tem temos ter um uma
    uns umas vai voce aqui ali sobre ate precisa preciso precisamos fazer faz existe existem
    escola escolas aluno alunos aluna alunas estudante estudantes
    """.split()
)
_MARCADOR = re.compile(r"\[[A-Z_]+\]")


@dataclass(frozen=True)
class ResultadoBusca:
    ids: tuple[str, ...]
    modo: str
    """"hibrida" ou "palavra_chave"."""
    motivo: str | None = None
    """Por que a busca vetorial não entrou, quando não entrou."""


def consulta_fts(texto: str) -> str | None:
    """Pergunta → expressão FTS5: termos relevantes, sem acento, com prefixo, unidos por OR.
    Marcadores do guardião ("[NOME]") e palavras vazias saem."""
    sem_marcadores = _MARCADOR.sub(" ", texto)
    normalizado = "".join(
        c for c in unicodedata.normalize("NFD", sem_marcadores.lower()) if unicodedata.category(c) != "Mn"
    )
    termos = dict.fromkeys(t for t in re.findall(r"[a-z0-9]+", normalizado) if len(t) > 2 and t not in _PALAVRAS_VAZIAS)
    return " OR ".join(f"{t}*" for t in termos) or None


def fundir(*listas: list[str], pesos: tuple[float, ...] | None = None, k: int = _K_RRF) -> list[str]:
    """RRF: soma de peso/(k + posição) de cada lista; empate desfeito pela primeira aparição."""
    pesos = pesos or (1.0,) * len(listas)
    pontuacao: dict[str, float] = {}
    for peso, lista in zip(pesos, listas, strict=True):
        for posicao, item in enumerate(lista):
            pontuacao[item] = pontuacao.get(item, 0.0) + peso / (k + posicao + 1)
    return sorted(pontuacao, key=lambda item: -pontuacao[item])


async def buscar(base: BaseNormativa, pergunta: TextoProtegido) -> ResultadoBusca:
    if not isinstance(pergunta, TextoProtegido):
        raise TypeError("A pergunta precisa passar pelo Guardião LGPD (AD-05)")

    expressao = consulta_fts(str(pergunta))
    por_palavra = base.buscar_palavra_chave(expressao, _CANDIDATOS) if expressao else []

    motivo = None
    if base.matriz is None:
        motivo = base.meta.get("embeddings_motivo_ausencia") or "base sem embeddings"
    elif base.meta.get("embeddings_modelo") != ai_client.MODELO_EMBEDDING:
        motivo = "modelo de embedding da base diferente do da consulta"
    else:
        try:
            vetor = await ai_client.gerar_embedding_consulta(pergunta)
        except RuntimeError:
            motivo = "API de embeddings indisponível"
        else:
            por_vetor = base.buscar_vetor(vetor, _CANDIDATOS)
            return ResultadoBusca(tuple(fundir(por_palavra, por_vetor, pesos=(PESO_PALAVRA_CHAVE, 1.0))), "hibrida")

    return ResultadoBusca(tuple(por_palavra), "palavra_chave", motivo)
