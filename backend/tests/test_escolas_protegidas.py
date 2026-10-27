"""Spec: docs/business-rules/escolas.md RN-06 (pendência 13 da arquitetura; revisão do AgLGPD de 2026-10-27).

Escola com 1 a 4 matrículas da educação especial: a área pública não mostra a contagem, o Eixo IV
nem a classe exclusiva, e o score público não depende de onde esses estudantes estudam.
"""

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.features.escolas import service
from app.main import app

cliente = TestClient(app)


def _linha(sql, *args):
    conn = get_connection()
    try:
        return conn.execute(sql, args).fetchone()
    finally:
        conn.close()


def _pequena():
    return _linha("SELECT * FROM escolas WHERE qt_mat_esp BETWEEN 1 AND 4 AND in_especial_exclusiva = 1 LIMIT 1")


def test_escola_pequena_nao_expoe_contagem_eixo_iv_nem_classe_exclusiva():
    escola = cliente.get(f"/escolas/{_pequena()['co_entidade']}").json()
    assert escola["alunosEsp"] is None and escola["statusEixoIV"] == "omitido"
    assert escola["especialExclusiva"] is False and escola["dadosProtegidos"] is True


def test_score_publico_nao_depende_da_taxa_de_classe_comum_da_escola(monkeypatch):
    linha = dict(_pequena())
    media = 0.7
    com_taxa_zero = service._score_publico({**linha, "score": linha["score"] - 1.5 * linha["v_taxa_cc"], "v_taxa_cc": 0.0}, media)
    com_taxa_um = service._score_publico({**linha, "score": linha["score"] + 1.5 * (1 - linha["v_taxa_cc"]), "v_taxa_cc": 1.0}, media)
    assert com_taxa_zero == pytest.approx(com_taxa_um)


def test_media_ignora_as_escolas_pequenas():
    linha = _pequena()
    conn = get_connection()
    try:
        media = service._media_da_taxa(conn, linha["co_municipio"], linha["sg_uf"])
    finally:
        conn.close()
    esperada = _linha(
        "SELECT AVG(qt_mat_esp_cc * 1.0 / qt_mat_esp) FROM escolas WHERE co_municipio = ? AND qt_mat_esp >= 5", linha["co_municipio"]
    )[0]
    assert media == pytest.approx(esperada if esperada is not None else media)


def test_escola_comum_fica_como_estava_e_ranking_usa_o_score_publico():
    comum = _linha("SELECT * FROM escolas WHERE qt_mat_esp >= 5 LIMIT 1")
    escola = cliente.get(f"/escolas/{comum['co_entidade']}").json()
    assert escola["alunosEsp"] == comum["qt_mat_esp"] and escola["score"] == pytest.approx(comum["score"])
    assert escola["dadosProtegidos"] is False

    lista = cliente.get(f"/municipios/{comum['co_municipio']}/escolas").json()
    melhor = max(lista, key=lambda e: e["score"])
    assert melhor["rankingMunicipal"] == 1
    assert [e["score"] for e in lista] == sorted(e["score"] for e in lista)
