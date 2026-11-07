"""Spec: docs/sdd/fase-2/arquitetura.md AD-02 (envio de e-mail pelo Brevo) e
requirements/acesso-gestao-ativa.md (falha fechado sem provedor)."""

import logging

import httpx
import pytest

from app.features.acesso import seguranca
from app.shared import email as envio
from app.shared.ambiente import problemas_da_gestao

_EMAIL = "diretora.teste@exemplo.gov.br"


@pytest.fixture
def brevo(monkeypatch):
    """Brevo configurado; devolve a lista de requisições que teriam saído."""
    monkeypatch.setenv("EMAIL_MODO", "brevo")
    monkeypatch.setenv("BREVO_API_KEY", "chave-de-teste")
    monkeypatch.setenv("EMAIL_REMETENTE", "nao-responda@exemplo.org")
    monkeypatch.delenv("EMAIL_REMETENTE_NOME", raising=False)
    enviadas: list[dict] = []
    resposta = {"status": 201}

    def postar(url, *, headers, json, timeout):
        enviadas.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return httpx.Response(resposta["status"], request=httpx.Request("POST", url))

    monkeypatch.setattr(envio._httpx, "post", postar)
    return enviadas, resposta


def test_envia_codigo_pelo_brevo_so_com_o_necessario(brevo):
    enviadas, _ = brevo
    envio.enviar_codigo(_EMAIL, "123456")
    [req] = enviadas
    assert req["url"] == "https://api.brevo.com/v3/smtp/email"
    assert req["headers"]["api-key"] == "chave-de-teste"
    corpo = req["json"]
    # Minimização: só destinatário, remetente, assunto e texto. Sem nome da pessoa, sem HTML
    # (nada de pixel de abertura ou link rastreado), sem tags ou parâmetros extras.
    assert set(corpo) == {"sender", "to", "subject", "textContent"}
    assert corpo["to"] == [{"email": _EMAIL}]
    assert corpo["sender"] == {"name": "Escola Sem Barreiras", "email": "nao-responda@exemplo.org"}
    assert "123456" in corpo["textContent"] and "http" not in corpo["textContent"]
    assert req["timeout"] <= 10


def test_pedido_de_acesso_cita_a_escola(brevo):
    enviadas, _ = brevo
    envio.enviar_codigo(_EMAIL, "654321", escola="EM Escola de Teste")
    assert "EM Escola de Teste" in enviadas[0]["json"]["textContent"]
    assert enviadas[0]["json"]["subject"] == "Confirme seu pedido de acesso à Gestão Ativa"


def test_validade_no_texto_e_a_do_codigo():
    assert seguranca.VALIDADE_CODIGO.total_seconds() == envio.VALIDADE_MINUTOS * 60


def test_brevo_nao_usa_a_caixa_de_teste(brevo, monkeypatch):
    monkeypatch.setenv("AMBIENTE", "dev")
    antes = len(envio.caixa_de_teste())
    envio.enviar_codigo(_EMAIL, "111111")
    assert len(envio.caixa_de_teste()) == antes


@pytest.mark.parametrize("status", [302, 400, 401, 429, 500])
def test_recusa_do_provedor_vira_indisponivel_sem_endereco_no_log(brevo, caplog, status):
    _, resposta = brevo
    resposta["status"] = status
    with caplog.at_level(logging.WARNING, logger="email"), pytest.raises(envio.EnvioIndisponivel):
        envio.enviar_codigo(_EMAIL, "222222")
    assert f"HTTP {status}" in caplog.text
    assert _EMAIL not in caplog.text and "222222" not in caplog.text and "chave-de-teste" not in caplog.text


def test_falha_de_rede_vira_indisponivel_sem_endereco_no_log(brevo, monkeypatch, caplog):
    def falhar(url, **_):
        raise httpx.ConnectTimeout(f"timeout ao enviar para {_EMAIL}")  # a mensagem do httpx pode trazer o destino

    monkeypatch.setattr(envio._httpx, "post", falhar)
    with caplog.at_level(logging.WARNING, logger="email"), pytest.raises(envio.EnvioIndisponivel) as erro:
        envio.enviar_codigo(_EMAIL, "333333")
    assert "ConnectTimeout" in caplog.text and _EMAIL not in caplog.text
    assert erro.value.__cause__ is None and erro.value.__context__ is None and _EMAIL not in str(erro.value)


@pytest.mark.parametrize("faltando", ["BREVO_API_KEY", "EMAIL_REMETENTE"])
def test_brevo_incompleto_falha_fechado(brevo, monkeypatch, faltando):
    enviadas, _ = brevo
    monkeypatch.delenv(faltando)
    assert any(faltando in p for p in problemas_da_gestao())
    with pytest.raises(envio.EnvioIndisponivel):
        envio.enviar_codigo(_EMAIL, "444444")
    assert enviadas == []


def test_brevo_completo_e_aceito_fora_de_dev(brevo, monkeypatch):
    monkeypatch.delenv("AMBIENTE", raising=False)
    monkeypatch.setenv("GESTAO_SEGREDO_TOKEN", "t" * 40)
    monkeypatch.setenv("GESTAO_SEGREDO_CODIGO", "c" * 40)
    assert problemas_da_gestao() == []


def test_modo_desconhecido_falha_fechado(monkeypatch):
    monkeypatch.setenv("EMAIL_MODO", "smtp")
    assert any("EMAIL_MODO" in p for p in problemas_da_gestao())
    with pytest.raises(envio.EnvioIndisponivel):
        envio.enviar_codigo(_EMAIL, "555555")


# --- O e-mail não é canal para texto livre (revisão do AgLGPD de 2026-11-07, M2) -------------

@pytest.mark.parametrize(
    "codigo, escola",
    [("abc123", None), ("1234567", None), ("12345", None), ("123456", "Escola\nCom relato"), ("123456", "x" * 200)],
)
def test_envio_recusa_codigo_e_escola_fora_do_formato(brevo, codigo, escola):
    enviadas, _ = brevo
    for funcao in (envio.enviar_codigo, envio.despachar_codigo):
        with pytest.raises(ValueError):
            funcao(_EMAIL, codigo, escola)
    envio.aguardar_envios()
    assert enviadas == []


# --- Envio de fundo nas rotas anônimas (A1) ---------------------------------------------------

def test_despachar_nao_espera_nem_falha_com_o_provedor(brevo, monkeypatch, caplog):
    import threading
    import time

    liberar = threading.Event()
    chamadas = []

    def lento(url, **kwargs):
        chamadas.append(url)
        liberar.wait(5)
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(envio._httpx, "post", lento)
    inicio = time.monotonic()
    with caplog.at_level(logging.WARNING, logger="email"):
        envio.despachar_codigo(_EMAIL, "777777")  # não levanta, mesmo com o provedor em 500
        assert time.monotonic() - inicio < 0.5
        liberar.set()
        envio.aguardar_envios()
    assert chamadas == [envio.BREVO_URL]
    assert "HTTP 500" in caplog.text and _EMAIL not in caplog.text


def test_despachar_no_console_vai_na_hora_para_a_caixa(monkeypatch):
    monkeypatch.setenv("AMBIENTE", "dev")
    monkeypatch.setenv("EMAIL_MODO", "console")
    envio.despachar_codigo(_EMAIL, "888888")
    assert envio.caixa_de_teste()[0].codigo == "888888"
