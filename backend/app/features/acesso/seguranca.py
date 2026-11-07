"""Código de uso único e token de sessão da Gestão Ativa (RF-04, RF-12).

- Código de 6 dígitos, válido por 10 minutos, até 5 tentativas; guardado só como HMAC.
- Limites contra força bruta por e-mail: novo código a cada 60 s, no máximo 5 por hora e 10 por
  dia, e no máximo 20 tentativas erradas por dia (revisão do AgLGPD).
- Token separado do da Fase 1 (audiência própria). Ele só identifica a conta: estado da conta e do
  vínculo são conferidos no banco a cada requisição (RN-07, RN-12).
- Chaves separadas para o token e para o HMAC dos códigos, lidas em `app.shared.ambiente`.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt

from app.shared.ambiente import segredo
from app.shared.banco_gestao import agora

VALIDADE_CODIGO = timedelta(minutes=10)
MAX_TENTATIVAS = 5
INTERVALO_REENVIO = timedelta(seconds=60)
MAX_CODIGOS_POR_HORA = 5
MAX_CODIGOS_POR_DIA = 10
MAX_ERROS_POR_DIA = 20
TETO_DIARIO_ANONIMO = 250
"""Códigos pedidos pelas rotas anônimas em 24 h, somando todos os e-mails (revisão do AgLGPD de
2026-11-07, A2). Fica abaixo da cota grátis do Brevo (300/dia) para sobrar margem ao
provisionamento de secretários; acima dele, nada é enviado e a resposta é a mesma."""

_AUDIENCIA = "gestao-ativa"
_VALIDADE_TOKEN = timedelta(hours=8)


def novo_codigo() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_codigo(email: str, codigo: str) -> str:
    return hmac.new(segredo("GESTAO_SEGREDO_CODIGO"), f"{email}:{codigo}".encode(), hashlib.sha256).hexdigest()


def codigo_confere(email: str, codigo: str, codigo_hash: str) -> bool:
    return hmac.compare_digest(hash_codigo(email, codigo.strip()), codigo_hash)


def criar_token(conta_id: str) -> str:
    return jwt.encode({"sub": conta_id, "aud": _AUDIENCIA, "exp": agora() + _VALIDADE_TOKEN}, segredo("GESTAO_SEGREDO_TOKEN"), algorithm="HS256")


def conta_do_token(token: str) -> str:
    """Levanta jwt.InvalidTokenError (inclusive expirado ou de outra audiência, como o da Fase 1)."""
    return jwt.decode(token, segredo("GESTAO_SEGREDO_TOKEN"), algorithms=["HS256"], audience=_AUDIENCIA)["sub"]
