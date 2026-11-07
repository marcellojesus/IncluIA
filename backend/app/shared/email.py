"""Envio de e-mail da Gestão Ativa (AD-02, pendência 3 resolvida em 2026-11-07).

Dois modos, escolhidos por `EMAIL_MODO`:

- `console`: só com `AMBIENTE=dev`. A mensagem vai para o console do backend e para a caixa de
  teste local (`caixa_de_teste`, exibida em /gestao/dev/emails). Em produção o console vira log
  persistente, e o código ali daria acesso a quem lê o log.
- `brevo`: API HTTP transacional do Brevo (o Render gratuito bloqueia SMTP desde 2025-09). Exige
  `BREVO_API_KEY` e `EMAIL_REMETENTE` (remetente verificado no Brevo; até haver domínio próprio,
  uma caixa dedicada do projeto, nunca pessoal). Mensagem só em texto: sem pixel de abertura nem
  link rastreado.

O provedor é operador: recebe só o e-mail do destinatário, o assunto e o texto (código de 6
dígitos e, no pedido de acesso, o nome da escola no Censo). O módulo só aceita isso: `enviar_codigo`
valida o código e a escola, e a única requisição sai para `BREVO_URL` (testes de arquitetura).

Revisão do AgLGPD de 2026-11-07:
- rotas anônimas usam `despachar_codigo`: o envio pelo provedor roda fora da requisição, então a
  resposta não muda (nem no tempo) se a conta existe ou se o provedor falhou (A1);
- falha vira `EnvioIndisponivel`, e o log registra só o código HTTP ou o tipo do erro, nunca o
  endereço, o código ou a chave; sem configuração completa, o envio falha fechado.
"""

import logging
import os
import re
import sys
import threading
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import datetime

import httpx as _httpx

from app.shared.ambiente import em_desenvolvimento
from app.shared.banco_gestao import agora

logger = logging.getLogger("email")
# Em DEBUG, httpx e httpcore registrariam a requisição; ficam em WARNING (B3).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

_CAPACIDADE_CAIXA = 30
BREVO_URL = "https://api.brevo.com/v3/smtp/email"
_TIMEOUT = 10.0
_NOME_REMETENTE_PADRAO = "Escola Sem Barreiras"
VALIDADE_MINUTOS = 10
"""Mesma validade de `acesso.seguranca.VALIDADE_CODIGO` (conferida em teste)."""
_CODIGO = re.compile(r"\d{6}")
_TAMANHO_MAXIMO_ESCOLA = 150


class EnvioIndisponivel(RuntimeError):
    pass


@dataclass(frozen=True)
class MensagemTeste:
    para: str
    assunto: str
    texto: str
    codigo: str
    enviada_em: datetime


_caixa: deque[MensagemTeste] = deque(maxlen=_CAPACIDADE_CAIXA)
_trava = threading.Lock()
_fila = ThreadPoolExecutor(max_workers=2, thread_name_prefix="envio-email")
_pendentes: set[Future] = set()


def caixa_de_teste() -> list[MensagemTeste]:
    """Últimas mensagens simuladas, da mais recente para a mais antiga. Só em memória: some quando
    o backend reinicia. Vazia fora de dev."""
    if not em_desenvolvimento():
        return []
    with _trava:
        return list(reversed(_caixa))


def _redigir(escola: str | None) -> tuple[str, str]:
    if escola:
        return (
            "Confirme seu pedido de acesso à Gestão Ativa",
            f"Você pediu acesso à Gestão Ativa como diretor(a) de {escola}. Se não foi você, ignore este e-mail.",
        )
    return (
        "Seu código de acesso à Gestão Ativa",
        "Use este código para entrar na Gestão Ativa. Se você não pediu este código, ignore este e-mail.",
    )


def _corpo(texto: str, codigo: str) -> str:
    return (
        f"{texto}\n\n"
        f"Código: {codigo}\n\n"
        f"O código vale por {VALIDADE_MINUTOS} minutos e só pode ser usado uma vez. "
        "Não compartilhe este código com ninguém: a equipe da Escola Sem Barreiras nunca pede o código.\n\n"
        "Escola Sem Barreiras — mensagem automática, não responda."
    )


def _validar(codigo: str, escola: str | None) -> None:
    """O e-mail não é canal para texto livre (revisão do AgLGPD, M2)."""
    if not _CODIGO.fullmatch(codigo):
        raise ValueError("código de acesso fora do formato")
    if escola is not None and (len(escola) > _TAMANHO_MAXIMO_ESCOLA or "\n" in escola or "\r" in escola):
        raise ValueError("nome de escola fora do formato")


def enviar_codigo(email: str, codigo: str, escola: str | None = None) -> None:
    """Envia na hora. Levanta `EnvioIndisponivel` se não der: use só em fluxo autenticado, em que
    a falha pode aparecer (provisionamento de secretário pelo administrador)."""
    _validar(codigo, escola)
    modo = os.environ.get("EMAIL_MODO", "")
    assunto, texto = _redigir(escola)
    if modo == "console" and em_desenvolvimento():
        with _trava:
            _caixa.append(MensagemTeste(email, assunto, texto, codigo, agora()))
        print(f"\n[Gestão Ativa — e-mail simulado, AMBIENTE=dev] Para {email}: {texto} Código: {codigo}\n", file=sys.stderr, flush=True)
        return
    if modo == "brevo":
        _enviar_brevo(email, assunto, _corpo(texto, codigo))
        return
    raise EnvioIndisponivel("Envio de e-mail não configurado neste ambiente")


def despachar_codigo(email: str, codigo: str, escola: str | None = None) -> None:
    """Para as rotas anônimas: nunca levanta por causa do provedor e não espera por ele.

    No modo console (só dev, sem rede) envia na hora, para a caixa de teste. Com o Brevo, o envio
    vai para uma fila de fundo; falha vira só um aviso no log, sem endereço."""
    _validar(codigo, escola)
    if os.environ.get("EMAIL_MODO") != "brevo":
        try:
            enviar_codigo(email, codigo, escola)
        except EnvioIndisponivel:
            logger.warning("Envio de e-mail não configurado")
        return

    def tarefa() -> None:
        try:
            enviar_codigo(email, codigo, escola)
        except EnvioIndisponivel:
            pass  # _enviar_brevo já registrou o motivo, sem endereço
        except Exception as erro:  # noqa: BLE001 - a fila não pode morrer; o tipo basta
            logger.warning("Falha inesperada no envio de e-mail: %s", type(erro).__name__)

    futuro = _fila.submit(tarefa)
    with _trava:
        _pendentes.add(futuro)
    futuro.add_done_callback(_pendentes.discard)


def aguardar_envios(timeout: float = 5.0) -> None:
    """Para os testes: espera a fila de fundo esvaziar."""
    with _trava:
        pendentes = list(_pendentes)
    wait(pendentes, timeout=timeout)


def _enviar_brevo(email: str, assunto: str, corpo: str) -> None:
    chave = os.environ.get("BREVO_API_KEY", "")
    remetente = os.environ.get("EMAIL_REMETENTE", "")
    if not chave or not remetente:
        raise EnvioIndisponivel("Brevo sem BREVO_API_KEY ou EMAIL_REMETENTE")
    falha: str | None = None
    resposta = None
    try:
        resposta = _httpx.post(
            BREVO_URL,
            headers={"api-key": chave, "accept": "application/json"},
            json={
                "sender": {"name": os.environ.get("EMAIL_REMETENTE_NOME") or _NOME_REMETENTE_PADRAO, "email": remetente},
                "to": [{"email": email}],
                "subject": assunto,
                "textContent": corpo,
            },
            timeout=_TIMEOUT,
        )
    except _httpx.HTTPError as erro:
        falha = type(erro).__name__
    # Levantar fora do `except`: a exceção do httpx (com URL e contexto) não fica encadeada (B2).
    if falha is not None:
        logger.warning("Falha no envio de e-mail (Brevo): %s", falha)
        raise EnvioIndisponivel("Falha de rede no envio de e-mail")
    if not resposta.is_success:
        # Só o código HTTP: o corpo da resposta pode repetir o endereço do destinatário. 3xx também
        # é falha: o httpx não segue redirecionamento (B1).
        logger.warning("Falha no envio de e-mail (Brevo): HTTP %s", resposta.status_code)
        raise EnvioIndisponivel("Provedor de e-mail recusou o envio")
