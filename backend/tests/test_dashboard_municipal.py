"""Spec: docs/sdd/fase-2/requirements/secretario/dashboard-municipal.md e business-rules (RN-DMS-01 a 07)."""

import pytest

from app.database import get_connection
from app.features.acesso import censo
from app.features.dashboard_municipal import servico
from tests.test_declaracao import ambiente  # noqa: F401 — fixture compartilhada
from tests.test_plano import _emitir, _plano
from tests.test_revisao_planos import _co_entidade

URL = "/gestao/secretario/dashboard"


def _escolas_da_rede(co_municipio):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT score, qt_mat_esp FROM escolas WHERE co_municipio = ? AND rede = ? AND score IS NOT NULL",
            (co_municipio, censo.rede_da_gestao(co_municipio)),
        ).fetchall()
    finally:
        conn.close()


def test_score_da_rede_pondera_por_alunos_esp_e_eixos_vao_do_mais_critico(ambiente):
    cliente, diretora, _ = ambiente
    dados = cliente.get(URL, headers=cliente.headers_secretaria).json()
    escolas = _escolas_da_rede(censo.escola(_co_entidade(cliente, diretora)).co_municipio)

    esperado = sum(e["score"] * e["qt_mat_esp"] for e in escolas) / sum(e["qt_mat_esp"] for e in escolas)
    assert dados["score"] == pytest.approx(esperado) and dados["ponderacao"] == "alunos_esp"
    assert dados["cobertura"]["escolasMunicipais"] == len(escolas) < dados["escolasMunicipio"]
    assert [e["score"] for e in dados["eixos"]] == sorted(e["score"] for e in dados["eixos"])
    assert {e["eixo"] for e in dados["eixos"]} == {"I", "II", "III", "IV"}


def test_prioridades_somam_o_que_falta_ao_score_da_rede(ambiente, monkeypatch):
    cliente, _, _ = ambiente
    monkeypatch.setattr(servico, "PRIORIDADES", 10_000)
    dados = cliente.get(URL, headers=cliente.headers_secretaria).json()
    pesos = [p["peso"] for p in dados["prioridades"]]
    assert pesos == sorted(pesos, reverse=True)
    assert sum(pesos) == pytest.approx(10 - dados["score"])
    assert len(pesos) == dados["escolasNoRanking"]
    assert dados["escolasNoRanking"] + dados["escolasSemAlunosEsp"] == dados["cobertura"]["escolasMunicipais"]
    # Contagem pequena não sai da tela da escola.
    assert not any(p["alunosEsp"] is not None and p["alunosEsp"] < 5 for p in dados["prioridades"])
    assert any(p["alunosEsp"] is None for p in dados["prioridades"])


def test_cobertura_e_andamento_vem_do_que_as_escolas_enviaram(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    antes = cliente.get(URL, headers=cliente.headers_secretaria).json()["cobertura"]
    assert antes["comDeclaracao"] == antes["comPlanoEnviado"] == antes["aguardandoAnalise"] == 0
    assert antes["escolasComBarreiras"] <= antes["escolasMunicipais"]

    _emitir(cliente, diretora)
    _emitir(cliente, outra)
    codigo = _plano(cliente, diretora).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": codigo, "acao": "Pedir à secretaria o profissional de AEE.", "horizonte": "LOA"}, headers=diretora)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora)

    monkeypatch.setattr(servico, "PRIORIDADES", 10_000)
    dados = cliente.get(URL, headers=cliente.headers_secretaria).json()
    cobertura = dados["cobertura"]
    assert (cobertura["comDeclaracao"], cobertura["comPlanoEnviado"], cobertura["aguardandoAnalise"]) == (2, 1, 1)
    assert cobertura["planoMaisAntigo"] is not None
    escola = next((p for p in dados["prioridades"] if p["coEntidade"] == _co_entidade(cliente, diretora)), None)
    if escola:  # a escola de teste pode não ter aluno ESP e ficar fora do ranking
        assert escola["declaracao"] is True and escola["plano"] == "aguardando_analise"


def test_so_o_secretario_ve_e_so_a_propria_rede(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.get(URL, headers=diretora).status_code == 403
    assert cliente.get(URL).status_code == 401
    # O município vem do vínculo: parâmetro na URL não troca a rede.
    propria = cliente.get(URL, headers=cliente.headers_secretaria).json()
    outra = cliente.get(f"{URL}?co_municipio=5300108", headers=cliente.headers_secretaria).json()
    assert outra["municipio"] == propria["municipio"] and outra["score"] == propria["score"]
