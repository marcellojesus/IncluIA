"""Spec: docs/requirements/login.md (RNF-01 hash de senha) e docs/business-rules/login.md.

Sessão via JWT stateless — sem tabela de sessão no banco. Simplificação assumida: expiração fixa
(8h a partir do login), não uma janela deslizante por inatividade (exigiria refresh token).
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, TypedDict

import bcrypt
import jwt

# Sem infraestrutura de segredo de produção ainda neste projeto — variável de ambiente com
# fallback óbvio de desenvolvimento (trocar antes de qualquer deploy real).
_JWT_SECRET = os.environ.get("INCLUIA_JWT_SECRET", "dev-secret-change-me")
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRACAO = timedelta(hours=8)


class ClaimsUsuario(TypedDict):
    sub: str
    nome: str
    perfil: str
    municipioId: Optional[int]
    uf: str


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def criar_token(*, usuario_id: str, nome: str, perfil: str, municipio_id: Optional[int], uf: str) -> str:
    payload = {
        "sub": usuario_id,
        "nome": nome,
        "perfil": perfil,
        "municipioId": municipio_id,
        "uf": uf,
        "exp": datetime.now(timezone.utc) + _JWT_EXPIRACAO,
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decodificar_token(token: str) -> ClaimsUsuario:
    return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])  # type: ignore[return-value]
