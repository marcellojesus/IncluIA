"""Migrações do banco da Gestão Ativa (AD-01). A URL vem de `GESTAO_DATABASE_URL` ou do padrão local
(`data/gestao_ativa.db`), a mesma usada pelo app (app/shared/banco_gestao.py).

Uso (a partir de backend/): `alembic upgrade head`; nova migração: `alembic revision --autogenerate -m "..."`.
"""

from alembic import context

from app.features.acesso import modelos  # noqa: F401 — registra as tabelas no metadata
from app.features.declaracao import modelos as modelos_declaracao  # noqa: F401
from app.features.plano import modelos as modelos_plano  # noqa: F401
from app.features.plano_municipal import modelos as modelos_plano_municipal  # noqa: F401
from app.features.analitico import modelos as modelos_analitico  # noqa: F401
from app.shared import banco_gestao

alvo = banco_gestao.Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=str(banco_gestao.engine().url), target_metadata=alvo, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conexao_externa = context.config.attributes.get("connection")
    if conexao_externa is not None:
        _rodar(conexao_externa)
        return
    with banco_gestao.engine().connect() as conexao:
        _rodar(conexao)


def _rodar(conexao) -> None:
    # render_as_batch: o SQLite não altera colunas; o Alembic recria a tabela quando preciso.
    context.configure(connection=conexao, target_metadata=alvo, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
