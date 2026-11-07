"""retenção (AD-07): conta pseudonimizada, texto apagado da versão retirada e auditoria só de inclusão

Revision ID: 7d1e0c5a9b42
Revises: 3bc6efcd2093
Create Date: 2026-11-03 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d1e0c5a9b42'
down_revision: Union[str, Sequence[str], None] = '3bc6efcd2093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# A auditoria não muda; só sai depois de 5 anos (RN-RET-03). Vale também para quem acessa o banco
# por fora da aplicação com o papel da aplicação. O corte é o mesmo de `retencao.PRAZO_AUDITORIA`.
# A data do evento é a do servidor: evento com data antiga não entra (não dá para forjar histórico
# nem fabricar evento já vencido; AgLGPD, M3). Limites: quem é dono das tabelas pode remover os
# gatilhos (no SQLite, quem tem o arquivo); no PostgreSQL de produção, a aplicação deve usar um papel
# sem posse da tabela e sem UPDATE, DELETE e TRUNCATE nela (pendência do AD-01).
_SQLITE = [
    """CREATE TRIGGER auditoria_sem_alteracao BEFORE UPDATE ON auditoria
       BEGIN SELECT RAISE(ABORT, 'a auditoria não pode ser alterada'); END""",
    """CREATE TRIGGER auditoria_sem_exclusao_no_prazo BEFORE DELETE ON auditoria
       WHEN julianday(old.criado_em) >= julianday('now', '-1827 days')
       BEGIN SELECT RAISE(ABORT, 'a auditoria só pode ser apagada depois de 5 anos'); END""",
    """CREATE TRIGGER auditoria_data_do_servidor BEFORE INSERT ON auditoria
       WHEN new.criado_em IS NULL OR julianday(new.criado_em) IS NULL
         OR abs(julianday(new.criado_em) - julianday('now')) > 1.0 / 24
       BEGIN SELECT RAISE(ABORT, 'a auditoria só aceita a data do servidor'); END""",
]
_POSTGRES = [
    """CREATE FUNCTION auditoria_protegida() RETURNS trigger AS $$
       BEGIN
         IF TG_OP = 'INSERT' THEN NEW.criado_em := now(); RETURN NEW; END IF;
         IF TG_OP IN ('UPDATE', 'TRUNCATE') THEN RAISE EXCEPTION 'a auditoria não pode ser alterada'; END IF;
         IF OLD.criado_em >= now() - interval '1827 days' THEN
           RAISE EXCEPTION 'a auditoria só pode ser apagada depois de 5 anos';
         END IF;
         RETURN OLD;
       END $$ LANGUAGE plpgsql""",
    """CREATE TRIGGER auditoria_protegida BEFORE INSERT OR UPDATE OR DELETE ON auditoria
       FOR EACH ROW EXECUTE FUNCTION auditoria_protegida()""",
    """CREATE TRIGGER auditoria_sem_truncate BEFORE TRUNCATE ON auditoria
       FOR EACH STATEMENT EXECUTE FUNCTION auditoria_protegida()""",
]


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('contas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('anonimizada_em', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('declaracoes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('texto_apagado_em', sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table('versoes_plano', schema=None) as batch_op:
        batch_op.add_column(sa.Column('texto_apagado_em', sa.DateTime(timezone=True), nullable=True))
    for comando in (_POSTGRES if op.get_bind().dialect.name == "postgresql" else _SQLITE):
        op.execute(comando)


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER auditoria_sem_truncate ON auditoria")
        op.execute("DROP TRIGGER auditoria_protegida ON auditoria")
        op.execute("DROP FUNCTION auditoria_protegida()")
    else:
        op.execute("DROP TRIGGER auditoria_data_do_servidor")
        op.execute("DROP TRIGGER auditoria_sem_exclusao_no_prazo")
        op.execute("DROP TRIGGER auditoria_sem_alteracao")
    with op.batch_alter_table('versoes_plano', schema=None) as batch_op:
        batch_op.drop_column('texto_apagado_em')
    with op.batch_alter_table('declaracoes', schema=None) as batch_op:
        batch_op.drop_column('texto_apagado_em')
    with op.batch_alter_table('contas', schema=None) as batch_op:
        batch_op.drop_column('anonimizada_em')
