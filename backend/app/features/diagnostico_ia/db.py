"""Tabela da narrativa pública em data/incluia.db (mesmo arquivo do ETL; não é tocada pelo ETL).

As tabelas do chat da Fase 1 (`chat_diagnostico_mensagens` e `chat_diagnostico_recomendacoes_ajustadas`)
deixaram de ser criadas em 2026-10-27, quando o chat saiu do ar; o destino do conteúdo já gravado
é decisão pendente (impacto-fase-1.md).
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
        conn.commit()
    finally:
        conn.close()
