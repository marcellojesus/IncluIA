"""Spec: docs/requirements/login.md, docs/business-rules/login.md"""

from typing import Literal, Optional

from app.shared.schemas import CamelModel


class LoginRequest(CamelModel):
    email: str
    senha: str


class LoginResponse(CamelModel):
    usuario_id: str
    nome: str
    perfil: Literal["municipal", "estadual"]
    municipio_id: Optional[int] = None
    uf: str
    token: str
