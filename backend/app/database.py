"""Conexão com o SQLite gerado pelo ETL (ver backend/etl/persist.py)."""

import sqlite3

from etl.config import SQLITE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
