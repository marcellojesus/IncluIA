"""Spec: docs/business-rules/login.md RN-06 — só o Diagnóstico IA exige autenticação.

Barreira real (não só de UI): aplicada como dependência do router de diagnostico_ia, para que
ninguém chame a API de IA (custo real por chamada a Gemini/Groq/Mistral) sem passar pelo login.
"""

from typing import Optional

import jwt
from fastapi import Header, HTTPException

from app.features.login.security import ClaimsUsuario, decodificar_token


def exigir_usuario_autenticado(authorization: Optional[str] = Header(default=None)) -> ClaimsUsuario:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decodificar_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessão expirada — faça login novamente")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Sessão inválida — faça login novamente")
