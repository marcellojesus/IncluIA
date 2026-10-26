"""Spec: docs/sdd/fase-2/arquitetura.md AD-08 — base normativa como artefato do ETL.

Roda sem rede (base gerada com --sem-embeddings). Os textos legais ficam em base/legislacao/,
fora do Git; sem eles, os testes que dependem do corpus são pulados.
"""

import json
import re
import sqlite3

import pytest

from etl.base_normativa import construir as etl
from etl.base_normativa.parser import dividir

pytestmark = pytest.mark.skipif(not etl.TEXTOS.exists(), reason="textos legais ausentes em base/legislacao/")


@pytest.fixture(scope="module")
def trechos():
    return {t.id: t for t in etl.carregar_trechos()[1]}


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("base") / "base_normativa.db"
    etl.construir(com_embeddings=False, saida=caminho)
    conn = sqlite3.connect(caminho)
    yield conn
    conn.close()


# --- Divisão por dispositivo -------------------------------------------------------------------

@pytest.mark.parametrize(
    "trecho_id, citacao",
    [
        ("LBI-art28-XII", "Lei 13.146/2015 (LBI), Art. 28, XII"),
        ("LBI-art28-p2-I", "Lei 13.146/2015 (LBI), Art. 28, § 2º, I"),
        ("LBI-art27-pu", "Lei 13.146/2015 (LBI), Art. 27, parágrafo único"),
        ("D12686-art1-p3", "Decreto 12.686/2025 (PNEEI), Art. 1º, § 3º"),
        ("D12686-art4A", "Decreto 12.686/2025 (PNEEI), Art. 4º-A"),
        ("D12686-art11-p1-IV", "Decreto 12.686/2025 (PNEEI), Art. 11, § 1º, IV"),
        ("D12686-art19A", "Decreto 12.686/2025 (PNEEI), Art. 19-A"),
    ],
)
def test_dispositivos_viram_trechos_com_citacao(trechos, trecho_id, citacao):
    assert trechos[trecho_id].citacao == citacao


def test_inciso_carrega_o_caput_como_contexto(trechos):
    trecho = trechos["LBI-art28-XII"]
    assert trecho.contexto.startswith("Incumbe ao poder público")
    assert trecho.texto.startswith("oferta de ensino da Libras, do Sistema Braille")


def test_caput_que_so_introduz_incisos_nao_vira_trecho(trechos):
    assert "LBI-art28" not in trechos
    assert "LBI-art28-p2" not in trechos  # § 2º só introduz os incisos I e II


def test_nota_editorial_sai_do_texto_legal(trechos):
    trecho = trechos["D12686-art14-p2"]
    assert "Redação dada" not in trecho.texto
    assert trecho.alterado_por == "Decreto nº 12.773, de 2025"
    for t in trechos.values():
        assert "*" not in t.texto and "Redação dada" not in t.texto and "Incluído pel" not in t.texto


def test_artigo_vetado_nao_entra(trechos):
    assert not any(t.id.startswith("LBI-art29") for t in trechos.values())


def test_decreto_alterador_resumido_fica_fora(trechos):
    assert not any(t.documento_id == "D12773" for t in trechos.values())


def test_incisos_embutidos_no_paragrafo():
    markdown = "**Art. 11.** Caput.\n\n§ 1º Etapas: I - primeira; II - segunda; e III - terceira."
    ids = [t.id for t in dividir("X", "Lei X", markdown)]
    assert ids == ["X-art11", "X-art11-p1-I", "X-art11-p1-II", "X-art11-p1-III"]


# --- Base gerada -------------------------------------------------------------------------------

def test_busca_por_palavra_chave_encontra_o_dispositivo(base):
    linhas = base.execute(
        "SELECT id FROM trechos_fts WHERE trechos_fts MATCH ? ORDER BY bm25(trechos_fts) LIMIT 3",
        ("braille",),
    ).fetchall()
    assert "LBI-art28-XII" in [l[0] for l in linhas]


def test_busca_ignora_acento(base):
    com = base.execute("SELECT count(*) FROM trechos_fts WHERE trechos_fts MATCH 'acessibilidade'").fetchone()[0]
    assert com > 0
    sem_acento = base.execute("SELECT count(*) FROM trechos_fts WHERE trechos_fts MATCH 'intérprete'").fetchone()[0]
    assert sem_acento == base.execute("SELECT count(*) FROM trechos_fts WHERE trechos_fts MATCH 'interprete'").fetchone()[0]


def test_meta_registra_versao_e_ausencia_de_embeddings(base):
    meta = dict(base.execute("SELECT chave, valor FROM meta"))
    assert re.fullmatch(r"[0-9a-f]{12}", meta["versao"])
    assert meta["embeddings_modelo"] == ""
    assert meta["embeddings_motivo_ausencia"]
    assert base.execute("SELECT count(*) FROM embeddings").fetchone()[0] == 0


def test_versao_so_muda_com_o_conteudo(trechos):
    lista = list(trechos.values())
    assert etl._versao(lista) == etl._versao(lista)


# --- Mapa barreira → norma ---------------------------------------------------------------------

def test_mapa_cobre_todas_as_barreiras_da_metodologia(base):
    metodologia = (etl.BASE_DIR / "metodologia_barreiras.md").read_text(encoding="utf-8")
    barreiras = set(re.findall(r"\| (B-[IV]+-\d{2}) \|", metodologia))
    assert barreiras, "nenhuma barreira encontrada na metodologia"
    mapeadas = {l[0] for l in base.execute("SELECT DISTINCT barreira FROM mapa_barreira")}
    assert barreiras == mapeadas


def test_mapa_segue_o_eixo_da_legislacao(base):
    def trechos_de(barreira):
        return {l[0] for l in base.execute("SELECT trecho_id FROM mapa_barreira WHERE barreira = ?", (barreira,))}

    assert "LBI-art28-XII" in trechos_de("B-III-02")
    assert {"LBI-art28-p2-I", "LBI-art28-p2-II"} <= trechos_de("B-III-01")
    assert trechos_de("B-IV-01") == {"D12686-art1-p3", "D12686-art8"}
    assert not any(t.startswith("D12686-art1-") and t != "D12686-art1-p3" for t in trechos_de("B-IV-01"))


def test_prefixo_do_mapa_sem_trecho_e_erro(trechos, tmp_path, monkeypatch):
    mapa = json.loads(etl.MAPA.read_text(encoding="utf-8"))
    mapa["eixos"]["I"]["dispositivos"].append("D12686-art99")
    falso = tmp_path / "mapa.json"
    falso.write_text(json.dumps(mapa), encoding="utf-8")
    monkeypatch.setattr(etl, "MAPA", falso)
    with pytest.raises(ValueError, match="art99"):
        etl.resolver_mapa(list(trechos.values()))


def test_avaliacao_aponta_para_trechos_existentes(trechos):
    avaliacao = json.loads((etl.PASTA / "avaliacao.json").read_text(encoding="utf-8"))
    for item in avaliacao["perguntas"]:
        assert item["esperado"] in trechos, item
