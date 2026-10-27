"""Spec: impacto-fase-1.md PUB-01: barreiras da escola na ficha pública, sem contagem de célula pequena."""

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app

cliente = TestClient(app)


def _escola(sql):
    conn = get_connection()
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def test_barreiras_da_escola_sao_publicas_e_ordenadas_por_pontos():
    dados = cliente.get("/escolas/33055238/barreiras").json()
    assert dados["censoVersao"] and dados["metodologiaVersao"]
    pontos = [b["pontos"] for b in dados["barreiras"]]
    assert pontos and pontos == sorted(pontos, reverse=True)


def test_celula_pequena_nao_revela_se_ha_classe_exclusiva():
    """Com 1 a 4 alunos, o eixo IV é o mesmo item fixo com ou sem classe exclusiva (revisão do AgLGPD)."""
    com = _escola("SELECT co_entidade FROM escolas WHERE qt_mat_esp BETWEEN 1 AND 4 AND qt_mat_esp_cc < qt_mat_esp LIMIT 1")
    sem = _escola("SELECT co_entidade FROM escolas WHERE qt_mat_esp BETWEEN 1 AND 4 AND qt_mat_esp_cc = qt_mat_esp LIMIT 1")
    eixo_iv = [[b for b in cliente.get(f"/escolas/{co}/barreiras").json()["barreiras"] if b["eixo"] == "IV"] for co in (com, sem)]
    assert eixo_iv[0] == eixo_iv[1]
    [item] = eixo_iv[0]
    assert item["pontos"] is None and "omitido" in item["dadoCenso"]


def test_escola_inexistente():
    assert cliente.get("/escolas/1/barreiras").status_code == 404
