"""Gera data/base_normativa.db, a base normativa somente leitura usada pela IA (AD-08).

Uso (a partir de backend/, com o .venv ativo):
    python -m etl.base_normativa.construir                  # busca por palavra-chave + vetores
    python -m etl.base_normativa.construir --sem-embeddings # só busca por palavra-chave (FTS5)

Lê os documentos marcados com "incluir" em corpus.json (textos em base/legislacao/), divide por
dispositivo, grava os trechos com índice FTS5, os embeddings (se disponíveis) e o mapa curado
barreira → dispositivos. Se a API de embeddings falhar, a base é gerada só com FTS5 e o motivo
fica registrado em `meta` — o backend usa a busca por palavra-chave nesse caso.
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from etl.base_normativa import embeddings
from etl.base_normativa.parser import Trecho, dividir
from etl.config import BASE_DIR, BASE_NORMATIVA_PATH

PASTA = Path(__file__).resolve().parent
CORPUS = PASTA / "corpus.json"
MAPA = PASTA / "mapa_barreira_norma.json"
TEXTOS = BASE_DIR / "base" / "legislacao"
SAIDA = BASE_NORMATIVA_PATH

_ESQUEMA = """
CREATE TABLE meta (chave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE documentos (
    id TEXT PRIMARY KEY, titulo TEXT NOT NULL, citacao TEXT NOT NULL, tipo TEXT NOT NULL,
    fonte_url TEXT NOT NULL, consultado_em TEXT NOT NULL, situacao TEXT NOT NULL, escopo TEXT
);
CREATE TABLE trechos (
    id TEXT PRIMARY KEY, documento_id TEXT NOT NULL REFERENCES documentos(id), artigo TEXT NOT NULL,
    paragrafo TEXT, inciso TEXT, citacao TEXT NOT NULL, capitulo TEXT, secao TEXT, contexto TEXT,
    texto TEXT NOT NULL, nota TEXT, alterado_por TEXT, ordem INTEGER NOT NULL
);
CREATE VIRTUAL TABLE trechos_fts USING fts5(
    id UNINDEXED, citacao, secao, contexto, texto, tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE embeddings (trecho_id TEXT PRIMARY KEY REFERENCES trechos(id), vetor BLOB NOT NULL);
CREATE TABLE metodologia_barreiras (
    codigo TEXT PRIMARY KEY, eixo TEXT NOT NULL, eixo_nome TEXT NOT NULL, barreira TEXT NOT NULL,
    regra TEXT NOT NULL, texto_exibido TEXT NOT NULL, pontos_texto TEXT NOT NULL, pontos_max REAL NOT NULL
);
CREATE TABLE mapa_barreira (
    barreira TEXT NOT NULL, eixo TEXT NOT NULL, trecho_id TEXT NOT NULL REFERENCES trechos(id),
    PRIMARY KEY (barreira, trecho_id)
);
"""


def carregar_trechos() -> tuple[list[dict], list[Trecho]]:
    documentos = [d for d in json.loads(CORPUS.read_text(encoding="utf-8"))["documentos"] if d["incluir"]]
    trechos: list[Trecho] = []
    for doc in documentos:
        arquivo = TEXTOS / doc["arquivo"]
        if not arquivo.exists():
            raise FileNotFoundError(f"Texto de {doc['id']} não encontrado: {arquivo}")
        trechos += dividir(doc["id"], doc["citacao"], arquivo.read_text(encoding="utf-8"))
    ids = [t.id for t in trechos]
    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        raise ValueError(f"Identificadores de trecho repetidos: {sorted(duplicados)}")
    return documentos, trechos


def resolver_mapa(trechos: list[Trecho]) -> list[tuple[str, str, str]]:
    """(barreira, eixo, trecho_id) a partir dos prefixos do mapa; prefixo sem trecho é erro."""
    mapa = json.loads(MAPA.read_text(encoding="utf-8"))
    linhas = []
    for eixo, item in mapa["eixos"].items():
        for prefixo in item["dispositivos"]:
            alvos = [t.id for t in trechos if t.id == prefixo or t.id.startswith(prefixo + "-")]
            if not alvos:
                raise ValueError(f"Dispositivo do mapa sem trecho na base: {prefixo}")
            linhas += [(barreira, eixo, alvo) for barreira in item["barreiras"] for alvo in alvos]
    return linhas


METODOLOGIA = BASE_DIR / "metodologia_barreiras.md"
_EIXO = re.compile(r"^### Eixo ([IV]+) — (.+)$")
_LINHA_BARREIRA = re.compile(r"^\| (B-[IV]+-\d{2}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$")
_VERSAO_METODOLOGIA = re.compile(r"Versão (\d+\.\d+)")


def carregar_metodologia() -> tuple[str, list[tuple]]:
    """Camada C2 do AD-08: as linhas das tabelas da §3 de metodologia_barreiras.md, por código."""
    texto = METODOLOGIA.read_text(encoding="utf-8")
    versao = _VERSAO_METODOLOGIA.search(texto)
    linhas, eixo, eixo_nome = [], None, None
    for linha in texto.splitlines():
        if m := _EIXO.match(linha.strip()):
            eixo, eixo_nome = m.group(1), m.group(2).strip()
        elif (m := _LINHA_BARREIRA.match(linha.strip())) and eixo:
            codigo, barreira, regra, exibido, pontos = (g.strip() for g in m.groups())
            pontos_max = float(re.search(r"\d+,\d+", pontos).group().replace(",", "."))
            linhas.append((codigo, eixo, eixo_nome, barreira, regra.replace("`", ""), exibido.strip('"'), pontos, pontos_max))
    if not linhas or not versao:
        raise ValueError("Metodologia de barreiras sem tabelas de regras ou sem versão")
    return versao.group(1), linhas


def _versao(trechos: list[Trecho]) -> str:
    """Muda quando muda qualquer texto, o corpus, o mapa ou a metodologia: identifica a versão da base."""
    h = hashlib.sha256()
    for parte in (CORPUS.read_bytes(), MAPA.read_bytes(), METODOLOGIA.read_bytes(), *(t.texto_busca.encode() for t in trechos)):
        h.update(parte)
    return h.hexdigest()[:12]


def construir(com_embeddings: bool, saida: Path = SAIDA) -> dict:
    documentos, trechos = carregar_trechos()
    mapa = resolver_mapa(trechos)
    metodologia_versao, metodologia = carregar_metodologia()

    meta = {
        "versao": _versao(trechos),
        "metodologia_barreiras_versao": metodologia_versao,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trechos": str(len(trechos)),
        "embeddings_modelo": "",
        "embeddings_dimensao": "",
        "embeddings_motivo_ausencia": "desativado (--sem-embeddings)",
    }
    vetores = None
    if com_embeddings:
        try:
            vetores = embeddings.gerar([t.texto_busca for t in trechos])
            meta.update(
                embeddings_modelo=embeddings.MODELO,
                embeddings_dimensao=str(embeddings.DIMENSAO),
                embeddings_motivo_ausencia="",
            )
        except embeddings.EmbeddingsIndisponiveis as exc:
            meta["embeddings_motivo_ausencia"] = str(exc)

    saida.parent.mkdir(parents=True, exist_ok=True)
    temporario = saida.with_suffix(".tmp")
    temporario.unlink(missing_ok=True)
    conn = sqlite3.connect(temporario)
    try:
        conn.executescript(_ESQUEMA)
        conn.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
        conn.executemany(
            "INSERT INTO documentos VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (d["id"], d["titulo"], d["citacao"], d["tipo"], d["fonte_url"], d["consultado_em"], d["situacao"], d.get("escopo"))
                for d in documentos
            ],
        )
        conn.executemany(
            "INSERT INTO trechos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (t.id, t.documento_id, t.artigo, t.paragrafo, t.inciso, t.citacao, t.capitulo, t.secao,
                 t.contexto, t.texto, t.nota, t.alterado_por, t.ordem)
                for t in trechos
            ],
        )
        conn.executemany(
            "INSERT INTO trechos_fts VALUES (?, ?, ?, ?, ?)",
            [(t.id, t.citacao, t.secao, t.contexto, t.texto) for t in trechos],
        )
        if vetores is not None:
            conn.executemany(
                "INSERT INTO embeddings VALUES (?, ?)",
                [(t.id, v.tobytes()) for t, v in zip(trechos, vetores)],
            )
        conn.executemany("INSERT INTO mapa_barreira VALUES (?, ?, ?)", mapa)
        conn.executemany("INSERT INTO metodologia_barreiras VALUES (?, ?, ?, ?, ?, ?, ?, ?)", metodologia)
        conn.commit()
    finally:
        conn.close()
    os.replace(temporario, saida)
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sem-embeddings", action="store_true", help="gera só a busca por palavra-chave")
    args = parser.parse_args()
    load_dotenv()

    meta = construir(com_embeddings=not args.sem_embeddings)
    print(f"Base normativa {meta['versao']} gravada em {SAIDA.relative_to(BASE_DIR)}: {meta['trechos']} trechos.")
    if meta["embeddings_modelo"]:
        print(f"Embeddings: {meta['embeddings_modelo']} ({meta['embeddings_dimensao']} dimensões).")
    else:
        print(f"Sem embeddings ({meta['embeddings_motivo_ausencia']}): a busca usará só palavras-chave.", file=sys.stderr)


if __name__ == "__main__":
    main()
