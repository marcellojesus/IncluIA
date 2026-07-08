"""Spec: docs/requirements/login.md, docs/business-rules/login.md"""

from typing import Literal, Optional

from app.shared.schemas import CamelModel

# Perfis de gestão, provisionados manualmente (seed) — não têm cadastro público (RN-02).
PerfilGestor = Literal["municipal", "estadual"]

# Perfis públicos, disponíveis via autocadastro na tela de Diagnóstico IA (RN-01 revisada).
PerfilPublico = Literal[
    "familia",
    "imprensa",
    "sociedade_civil",
    "secretario_educacao",
    "pesquisador",
    "poder_publico",
]

Perfil = Literal[
    "municipal",
    "estadual",
    "familia",
    "imprensa",
    "sociedade_civil",
    "secretario_educacao",
    "pesquisador",
    "poder_publico",
]


class LoginRequest(CamelModel):
    email: str
    senha: str


class RegistroRequest(CamelModel):
    nome: str
    email: str
    senha: str
    perfil: PerfilPublico


class LoginResponse(CamelModel):
    usuario_id: str
    nome: str
    perfil: Perfil
    municipio_id: Optional[int] = None
    uf: Optional[str] = None
    token: str
