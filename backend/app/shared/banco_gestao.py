"""Banco da Gestão Ativa (AD-01): contas, vínculos, auditoria e, depois, declarações e planos.

SQLAlchemy 2, portável entre SQLite (desenvolvimento local, `data/gestao_ativa.db`, fora do Git) e
PostgreSQL (deploy, via `GESTAO_DATABASE_URL`). Separado do `incluia.db`, que é o artefato somente
leitura do Censo. O esquema é criado pelas migrações Alembic (`backend/migrations/`).
"""

import os
from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from etl.config import BASE_DIR

URL_PADRAO = f"sqlite:///{(BASE_DIR / 'data' / 'gestao_ativa.db').as_posix()}"


class Base(DeclarativeBase):
    pass


def agora() -> datetime:
    return datetime.now(timezone.utc)


_engine: Engine | None = None
_fabrica: sessionmaker[Session] | None = None


def configurar(url: str | None = None) -> Engine:
    """Cria o engine (na subida do app ou nos testes, com um banco temporário)."""
    global _engine, _fabrica
    url = url or os.environ.get("GESTAO_DATABASE_URL", URL_PADRAO)
    argumentos = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    _engine = create_engine(url, **argumentos)
    if url.startswith("sqlite"):
        # SQLite só aplica chave estrangeira com o pragma ligado em cada conexão.
        @event.listens_for(_engine, "connect")
        def _ligar_chaves_estrangeiras(conexao, _registro):
            conexao.execute("PRAGMA foreign_keys = ON")

    _fabrica = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def engine() -> Engine:
    return _engine or configurar()


def migrar() -> None:
    """Aplica as migrações pendentes (na subida do app e no comando de linha)."""
    from alembic import command
    from alembic.config import Config

    backend = BASE_DIR / "backend"
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "migrations"))
    with engine().connect() as conexao:
        sqlite = conexao.dialect.name == "sqlite"
        if sqlite:
            # O SQLite altera tabela recriando-a (copia, apaga, renomeia); com chave estrangeira
            # ligada, apagar uma tabela já referenciada falha. O pragma só muda fora de transação.
            conexao.exec_driver_sql("PRAGMA foreign_keys = OFF")
            conexao.commit()  # o SQLAlchemy 2 abre transação até para o pragma
        try:
            with conexao.begin():
                config.attributes["connection"] = conexao
                command.upgrade(config, "head")
            if sqlite:
                violacoes = conexao.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
                conexao.commit()
                if violacoes:
                    raise RuntimeError(f"Migração deixou {len(violacoes)} referência(s) quebrada(s) no banco da Gestão Ativa")
        finally:
            if sqlite:
                conexao.exec_driver_sql("PRAGMA foreign_keys = ON")
                conexao.commit()


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    if _fabrica is None:
        configurar()
    sessao = _fabrica()
    try:
        yield sessao
    finally:
        sessao.close()
