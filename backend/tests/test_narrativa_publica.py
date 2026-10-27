"""Spec: docs/requirements/diagnostico-ia.md e impacto-fase-1.md (opção 2): narrativa pública, sem login, guardada por edição."""

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.features.diagnostico_ia import router, service
from app.features.diagnostico_ia.cache import calcular_chave
from app.main import app
from app.shared import ai_client

MUNICIPIO = 3303302  # Niterói
URL = f"/municipios/{MUNICIPIO}/narrativa"


@pytest.fixture
def cliente(monkeypatch):
    chaves = [calcular_chave(MUNICIPIO, eixo) for eixo in service.EIXOS_ROMANOS]

    def limpar():
        conn = get_connection()
        try:
            conn.executemany("DELETE FROM cache_diagnosticos WHERE chave = ?", [(c,) for c in chaves])
            conn.commit()
        finally:
            conn.close()

    limpar()
    service._falhou_em.clear()
    router.limitar_geracao.zerar()
    router._geracoes.clear()
    yield TestClient(app)
    limpar()


def _provedor(chamadas):
    async def responder(_sistema, _mensagens):
        chamadas.append(1)
        return {"situacao": "Situação crítica", "analise": "Leitura do eixo.", "alertaLegal": None, "referenciaMunicipio": None}

    return responder


def test_narrativa_e_publica_e_gerada_uma_vez_por_edicao(cliente, monkeypatch):
    chamadas = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor(chamadas))])
    primeira = cliente.get(URL)
    assert primeira.status_code == 200
    dados = primeira.json()
    assert len(dados["eixos"]) == 4 and dados["censoVersao"] and "recomendacoes" not in dados["eixos"][0]
    assert {e["modeloUsado"] for e in dados["eixos"]} == {"teste"}

    assert cliente.get(URL).json() == dados
    assert len(chamadas) == 4, "a segunda visita lê a narrativa guardada, sem IA"


def test_falha_da_ia_nao_e_guardada_e_espera_antes_de_tentar_de_novo(cliente, monkeypatch):
    async def fora_do_ar(*_args):
        raise RuntimeError("provedor fora")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("fora", fora_do_ar)])
    dados = cliente.get(URL).json()
    assert {e["modeloUsado"] for e in dados["eixos"]} == {"dados_brutos"}
    assert service.guardada(MUNICIPIO) is None

    chamadas = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor(chamadas))])
    cliente.get(URL)
    assert chamadas == [], "dentro da espera, visitantes não disparam nova chamada"


def test_geracao_tem_limite_por_ip(cliente, monkeypatch):
    async def fora_do_ar(*_args):
        raise RuntimeError("provedor fora")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("fora", fora_do_ar)])
    respostas = [cliente.get(URL).status_code for _ in range(router.limitar_geracao.limite + 1)]
    assert respostas[-1] == 429


def test_geracao_tem_teto_diario_global(cliente, monkeypatch):
    async def fora_do_ar(*_args):
        raise RuntimeError("provedor fora")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("fora", fora_do_ar)])
    monkeypatch.setattr(router, "GERACOES_POR_DIA", 1)
    assert cliente.get(URL).status_code == 200
    router.limitar_geracao.zerar()  # outro IP, mesmo teto
    assert cliente.get(URL).status_code == 429


def test_chat_e_login_da_fase_1_sairam_do_ar(cliente):
    assert cliente.post(f"/municipios/{MUNICIPIO}/diagnostico").status_code in (404, 405)
    assert cliente.post(f"/municipios/{MUNICIPIO}/diagnostico/I/chat", json={"mensagem": "oi"}).status_code in (404, 405)
    assert cliente.post("/auth/login", json={"email": "a@b.c", "senha": "x"}).status_code == 404
    assert cliente.post("/auth/registrar", json={}).status_code == 404
