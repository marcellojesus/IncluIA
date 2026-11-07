"""Banco da Gestão Ativa para os testes (AD-01).

Por padrão, um SQLite novo no diretório temporário de cada teste. Com `GESTAO_TESTE_DATABASE_URL`
definida (CI com PostgreSQL ou uma branch de testes no Neon), cada teste recebe o esquema `public`
apagado e recriado no PostgreSQL, com as migrações aplicadas do zero. Nunca aponte essa variável
para o banco de produção: o esquema é apagado a cada teste.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.orm import close_all_sessions

from app.shared import banco_gestao


def url_postgres_de_teste() -> str | None:
    url = os.environ.get("GESTAO_TESTE_DATABASE_URL") or None
    if url is None:
        return None
    # O conftest zera GESTAO_DATABASE_URL; a do app pode estar no ambiente original ou no .env.
    do_app = {os.environ.get("GESTAO_DATABASE_URL"), dotenv_values(Path(__file__).resolve().parents[1] / ".env").get("GESTAO_DATABASE_URL")}
    if any(u and banco_gestao.normalizar_url(u) == banco_gestao.normalizar_url(url) for u in do_app):
        raise RuntimeError("GESTAO_TESTE_DATABASE_URL é igual à GESTAO_DATABASE_URL: os testes apagariam o banco do app")
    return url


def preparar(tmp_path: Path) -> None:
    # Testes que abrem sessão e não fecham deixariam a conexão "idle in transaction", segurando as
    # tabelas: no PostgreSQL, o DROP SCHEMA do teste seguinte esperaria para sempre.
    close_all_sessions()
    url = url_postgres_de_teste()
    if url is None:
        banco_gestao.configurar(f"sqlite:///{(tmp_path / 'gestao.db').as_posix()}")
    else:
        engine = banco_gestao.configurar(url)
        with engine.begin() as conexao:
            # Conexões que sobraram de testes anteriores (deste processo ou de uma execução
            # interrompida) no banco descartável de testes.
            conexao.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid() AND usename = current_user"
            ))
            conexao.execute(text("SET LOCAL lock_timeout = '30s'"))
            conexao.execute(text("DROP SCHEMA public CASCADE"))
            conexao.execute(text("CREATE SCHEMA public"))
    banco_gestao.migrar()
