"""auditoria: alvo_tipo e resultado com 40 caracteres (o PDF da narrativa grava 'narrativa_plano_municipal')

Achado ao rodar a suíte no PostgreSQL (2026-11-07): o SQLite ignora o tamanho de VARCHAR, o
PostgreSQL recusa o valor de 25 caracteres em VARCHAR(20) e o download do PDF da narrativa
executiva falharia em produção.

Só altera no PostgreSQL: no SQLite o tamanho não vale, e alterar coluna recria a tabela, o que
apagaria os gatilhos da auditoria imutável (RN-RET-03). No PostgreSQL, alargar VARCHAR não reescreve
linhas nem dispara os gatilhos.

Revision ID: b3f1c2d4e5a6
Revises: 7d1e0c5a9b42
Create Date: 2026-11-07 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1c2d4e5a6'
down_revision: Union[str, Sequence[str], None] = '7d1e0c5a9b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name != "postgresql":
        return
    for coluna in ("alvo_tipo", "resultado"):
        op.alter_column("auditoria", coluna, type_=sa.String(40), existing_type=sa.String(20), existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name != "postgresql":
        return
    for coluna in ("alvo_tipo", "resultado"):
        op.alter_column("auditoria", coluna, type_=sa.String(20), existing_type=sa.String(40), existing_nullable=False)
