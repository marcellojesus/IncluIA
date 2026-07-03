"""Spec: docs/requirements/login.md, docs/business-rules/login.md"""

from typing import Optional

from app.database import get_connection
from app.features.login.schemas import LoginResponse
from app.features.login.security import criar_token, verificar_senha


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
