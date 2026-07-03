"""Configuração de caminhos e constantes do ETL do Score IncluIA."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DADOS_CENSO_DIR = BASE_DIR / "base" / "microdados_censo_escolar_2025" / "dados"

TABELA_ESCOLA_CSV = DADOS_CENSO_DIR / "Tabela_Escola_2025.csv"
TABELA_MATRICULA_CSV = DADOS_CENSO_DIR / "Tabela_Matricula_2025.csv"

CSV_SEP = ";"
CSV_ENCODING = "cp1252"

CENSO_VERSAO = "2025"

SQLITE_PATH = BASE_DIR / "data" / "incluia.db"

# TP_SITUACAO_FUNCIONAMENTO — ver docs/business-rules/score-incluia.md e o plano do ETL:
# só escolas "Em Atividade" entram no cálculo do score.
SITUACAO_EM_ATIVIDADE = 1
