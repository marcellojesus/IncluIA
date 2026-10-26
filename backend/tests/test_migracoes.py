"""As migrações precisam funcionar sobre um banco com dados, não só sobre um banco vazio.

No SQLite, o Alembic altera tabela recriando-a; com chave estrangeira ligada e linhas apontando para
a tabela, a migração falhava (visto em 2026-10-24 no banco local, ao acrescentar a retirada da
publicação). `banco_gestao.migrar` desliga a checagem durante a migração e confere as referências
no fim.
"""

import sqlite3

from alembic import command
from alembic.config import Config

from app.shared import banco_gestao
from etl.config import BASE_DIR


def _config(conexao) -> Config:
    config = Config(str(BASE_DIR / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "backend" / "migrations"))
    config.attributes["connection"] = conexao
    return config


def test_migrar_ate_o_fim_com_declaracao_ja_gravada(tmp_path):
    caminho = tmp_path / "gestao.db"
    banco_gestao.configurar(f"sqlite:///{caminho.as_posix()}")
    try:
        with banco_gestao.engine().begin() as conexao:
            command.upgrade(_config(conexao), "f48675eb7a39")  # antes da retirada da publicação

        bruto = sqlite3.connect(caminho)
        bruto.execute("INSERT INTO contas (id, nome, email, papel, criado_em, atualizado_em) VALUES ('c1', 'Diretora', 'd@e.gov.br', 'diretor', '2026-10-24', '2026-10-24')")
        bruto.execute(
            "INSERT INTO declaracoes (id, co_entidade, co_municipio, versao, censo_versao, metodologia_versao, emitida_por, emitida_em) "
            "VALUES ('d1', 33055238, 3303302, 1, '2025', '0.1', 'c1', '2026-10-24')"
        )
        bruto.execute(
            "INSERT INTO declaracao_itens (id, declaracao_id, ordem, codigo, eixo, barreira, dado_censo, pontos, posicao) "
            "VALUES ('i1', 'd1', 0, 'B-I-01', 'I', 'Sem oferta de AEE', 'O Censo…', 3.0, 'sem_relato')"
        )
        bruto.commit()
        bruto.close()

        banco_gestao.migrar()

        bruto = sqlite3.connect(caminho)
        colunas = [linha[1] for linha in bruto.execute("PRAGMA table_info(declaracoes)")]
        assert {"retirada_em", "retirada_por", "retirada_motivo"} <= set(colunas)
        assert bruto.execute("SELECT count(*) FROM declaracao_itens").fetchone()[0] == 1
        assert bruto.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not bruto.execute("SELECT name FROM sqlite_master WHERE name LIKE '_alembic_tmp%'").fetchall()
        bruto.close()
    finally:
        banco_gestao.configurar()
