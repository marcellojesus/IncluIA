"""Spec: docs/requirements/login.md, docs/business-rules/login.md

Cria a tabela `usuarios` em data/incluia.db (mesmo arquivo do ETL — ver backend/etl/persist.py,
que só reescreve escolas/municipios/uf_agregado, então esta tabela sobrevive a reprocessamentos
do Censo) e semeia 2 usuários de demonstração na primeira subida do app.
"""

import bcrypt

from app.database import get_connection

_USUARIOS_DEMO = [
    {
        "id": "u-joao-niteroi",
        "email": "joao.silva@niteroi.rj.gov.br",
        "senha": "demo1234",
        "nome": "João Silva",
        "perfil": "municipal",
        "municipio_id": 3303302,  # Niterói/RJ
        "uf": "RJ",
    },
    {
        "id": "u-maria-rj",
        "email": "maria.souza@rj.gov.br",
        "senha": "demo1234",
        "nome": "Maria Souza",
        "perfil": "estadual",
        "municipio_id": None,
        "uf": "RJ",
    },
]


def _tabela_usuarios_desatualizada(conn) -> bool:
    # A tabela original restringia `perfil` a municipal/estadual e exigia `uf` — incompatível
    # com o autocadastro público (RN-01 revisada), que aceita outros perfis e não coleta UF.
    # SQLite não suporta ALTER de CHECK/NOT NULL, então recriamos a tabela quando detectamos o
    # schema antigo (migração feita uma única vez, nas próximas subidas o SQL já bate).
    linha = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'usuarios'"
    ).fetchone()
    if linha is None:
        return False
    return "CHECK" in (linha["sql"] or "")


def _migrar_tabela_usuarios(conn) -> None:
    conn.execute("ALTER TABLE usuarios RENAME TO usuarios_old")
    conn.execute(
        """
        CREATE TABLE usuarios (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            perfil TEXT NOT NULL,
            municipio_id INTEGER,
            uf TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO usuarios (id, email, senha_hash, nome, perfil, municipio_id, uf) "
        "SELECT id, email, senha_hash, nome, perfil, municipio_id, uf FROM usuarios_old"
    )
    conn.execute("DROP TABLE usuarios_old")


def ensure_schema_and_seed() -> None:
    conn = get_connection()
    try:
        if _tabela_usuarios_desatualizada(conn):
            _migrar_tabela_usuarios(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                perfil TEXT NOT NULL,
                municipio_id INTEGER,
                uf TEXT
            )
            """
        )
        ja_tem_usuarios = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"] > 0
        if not ja_tem_usuarios:
            for usuario in _USUARIOS_DEMO:
                senha_hash = bcrypt.hashpw(usuario["senha"].encode(), bcrypt.gensalt()).decode()
                conn.execute(
                    "INSERT INTO usuarios "
                    "(id, email, senha_hash, nome, perfil, municipio_id, uf) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        usuario["id"],
                        usuario["email"],
                        senha_hash,
                        usuario["nome"],
                        usuario["perfil"],
                        usuario["municipio_id"],
                        usuario["uf"],
                    ),
                )
        conn.commit()
    finally:
        conn.close()
