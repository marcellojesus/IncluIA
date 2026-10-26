"""Leitura da base normativa (data/base_normativa.db), artefato somente leitura do ETL (AD-08).

Carregada uma vez por processo: trechos, metodologia de barreiras (camada C2), mapa barreira →
dispositivos e, se a base tiver, a matriz de embeddings. A busca por palavra-chave abre uma conexão
somente leitura por consulta.
"""

import logging
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from etl.config import BASE_NORMATIVA_PATH

logger = logging.getLogger("contexto_ia")


class BaseNormativaIndisponivel(RuntimeError):
    """O arquivo da base não existe ou não pôde ser lido; rode etl.base_normativa.construir."""


@dataclass(frozen=True)
class TrechoNormativo:
    id: str
    artigo: str
    citacao: str
    contexto: str | None
    texto: str
    alterado_por: str | None
    ordem: int


@dataclass(frozen=True)
class RegraBarreira:
    codigo: str
    eixo: str
    eixo_nome: str
    barreira: str
    regra: str
    texto_exibido: str
    pontos_texto: str
    pontos_max: float


@dataclass(frozen=True)
class BaseNormativa:
    caminho: Path
    meta: dict[str, str]
    trechos: dict[str, TrechoNormativo]
    metodologia: dict[str, RegraBarreira]
    mapa: dict[str, tuple[str, ...]]
    """Barreira → identificadores de trecho, na ordem do texto legal."""
    ids_vetores: tuple[str, ...]
    matriz: np.ndarray | None

    def buscar_palavra_chave(self, consulta_fts: str, limite: int) -> list[str]:
        """Falha da consulta devolve lista vazia; o log leva só o tipo do erro, porque a mensagem do
        FTS5 ("syntax error near …") repete termos da pergunta."""
        conn = sqlite3.connect(f"file:{self.caminho}?mode=ro", uri=True)
        try:
            linhas = conn.execute(
                "SELECT id FROM trechos_fts WHERE trechos_fts MATCH ? ORDER BY bm25(trechos_fts) LIMIT ?",
                (consulta_fts, limite),
            ).fetchall()
        except sqlite3.Error as exc:
            logger.warning("Falha na busca por palavra-chave: %s", type(exc).__name__)
            return []
        finally:
            conn.close()
        return [linha[0] for linha in linhas]

    def buscar_vetor(self, vetor: np.ndarray, limite: int) -> list[str]:
        if self.matriz is None:
            return []
        similaridades = self.matriz @ vetor
        return [self.ids_vetores[i] for i in np.argsort(-similaridades)[:limite]]


def carregar(caminho: Path = BASE_NORMATIVA_PATH) -> BaseNormativa:
    return _carregar(Path(caminho))


@lru_cache(maxsize=2)
def _carregar(caminho: Path) -> BaseNormativa:
    if not caminho.exists():
        raise BaseNormativaIndisponivel(f"Base normativa não encontrada em {caminho.name}")
    conn = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        meta = dict(conn.execute("SELECT chave, valor FROM meta"))
        trechos = {
            linha[0]: TrechoNormativo(*linha)
            for linha in conn.execute(
                "SELECT id, artigo, citacao, contexto, texto, alterado_por, ordem FROM trechos ORDER BY ordem"
            )
        }
        metodologia = {
            linha[0]: RegraBarreira(*linha)
            for linha in conn.execute(
                "SELECT codigo, eixo, eixo_nome, barreira, regra, texto_exibido, pontos_texto, pontos_max "
                "FROM metodologia_barreiras"
            )
        }
        mapa: dict[str, list[str]] = {}
        for barreira, trecho_id in conn.execute(
            "SELECT m.barreira, m.trecho_id FROM mapa_barreira m JOIN trechos t ON t.id = m.trecho_id ORDER BY t.ordem"
        ):
            mapa.setdefault(barreira, []).append(trecho_id)
        vetores = conn.execute(
            "SELECT e.trecho_id, e.vetor FROM embeddings e JOIN trechos t ON t.id = e.trecho_id ORDER BY t.ordem"
        ).fetchall()
    except sqlite3.Error as exc:
        raise BaseNormativaIndisponivel(f"Base normativa ilegível ({type(exc).__name__})") from None
    finally:
        conn.close()

    matriz = np.vstack([np.frombuffer(v, dtype=np.float32) for _, v in vetores]) if vetores else None
    return BaseNormativa(
        caminho=caminho,
        meta=meta,
        trechos=trechos,
        metodologia=metodologia,
        mapa={b: tuple(ids) for b, ids in mapa.items()},
        ids_vetores=tuple(i for i, _ in vetores),
        matriz=matriz,
    )
