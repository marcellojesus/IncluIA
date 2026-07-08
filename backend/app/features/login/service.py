"""Spec: docs/requirements/login.md, docs/business-rules/login.md"""

import uuid
from typing import Optional

from app.database import get_connection
from app.features.login.schemas import LoginResponse, PerfilPublico
from app.features.login.security import criar_token, hash_senha, verificar_senha


class EmailJaCadastradoError(Exception):
    pass


def autenticar(email: str, senha: str) -> Optional[LoginResponse]:
    conn = get_connection()
    try:
        linha = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    # RN-04: mesma resposta (None -> 401 genérico) para e-mail inexistente e senha incorreta,
    # para não permitir enumeração de contas.
    if linha is None or not verificar_senha(senha, linha["senha_hash"]):
        return None

    token = criar_token(
        usuario_id=linha["id"],
        nome=linha["nome"],
        perfil=linha["perfil"],
        municipio_id=linha["municipio_id"],
        uf=linha["uf"],
    )
    return LoginResponse(
        usuario_id=linha["id"],
        nome=linha["nome"],
        perfil=linha["perfil"],
        municipio_id=linha["municipio_id"],
        uf=linha["uf"],
        token=token,
    )


def registrar(nome: str, email: str, senha: str, perfil: PerfilPublico) -> LoginResponse:
    conn = get_connection()
    try:
        existente = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if existente is not None:
            raise EmailJaCadastradoError()

        usuario_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO usuarios (id, email, senha_hash, nome, perfil, municipio_id, uf) "
            "VALUES (?, ?, ?, ?, ?, NULL, NULL)",
            (usuario_id, email, hash_senha(senha), nome, perfil),
        )
        conn.commit()
    finally:
        conn.close()

    token = criar_token(usuario_id=usuario_id, nome=nome, perfil=perfil, municipio_id=None, uf=None)
    return LoginResponse(
        usuario_id=usuario_id,
        nome=nome,
        perfil=perfil,
        municipio_id=None,
        uf=None,
        token=token,
    )
