"""Cache de diagnósticos de IA — RN-05 de docs/business-rules/diagnostico-ia.md.

Tabela em data/incluia.db (mesmo arquivo do ETL e do login — não é tocada pelo ETL nem afetada
por ele, mesmo padrão já usado em app/features/login/db.py).
"""

from app.database import get_connection


def ensure_schema() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_diagnosticos (
                chave         TEXT PRIMARY KEY,
                codigo_ibge   INTEGER NOT NULL,
                eixo          TEXT NOT NULL,
                modelo_usado  TEXT NOT NULL,
                diagnostico   TEXT NOT NULL,
                gerado_em     TEXT NOT NULL,
                expira_em     TEXT NOT NULL
            )
            """
        )
        # RN-09: histórico de chat por (município, eixo) — append-only, nunca sobrescrito.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_diagnostico_mensagens (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_ibge INTEGER NOT NULL,
                eixo        TEXT NOT NULL,
                papel       TEXT NOT NULL CHECK (papel IN ('user', 'assistant')),
                conteudo    TEXT NOT NULL,
                criado_em   TEXT NOT NULL
            )
            """
        )
        # Última recomendação ajustada via chat por (município, eixo) — substitui a recomendação
        # gerada automaticamente até o secretário pedir outro ajuste pelo próprio chat.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_diagnostico_recomendacoes_ajustadas (
                codigo_ibge         INTEGER NOT NULL,
                eixo                TEXT NOT NULL,
                recomendacoes_json  TEXT NOT NULL,
                ajustado_em         TEXT NOT NULL,
                PRIMARY KEY (codigo_ibge, eixo)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
