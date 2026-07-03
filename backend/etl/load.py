"""Carga dos microdados do Censo Escolar 2025 (Escola + Matrícula) em um único DataFrame por escola."""

import pandas as pd

from etl.config import (
    CSV_ENCODING,
    CSV_SEP,
    SITUACAO_EM_ATIVIDADE,
    TABELA_ESCOLA_CSV,
    TABELA_MATRICULA_CSV,
)

COLUNAS_ESCOLA = [
    "CO_ENTIDADE",
    "NO_ENTIDADE",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "SG_UF",
    "CO_UF",
    "NO_BAIRRO",
    "TP_DEPENDENCIA",
    "TP_SITUACAO_FUNCIONAMENTO",
    "TP_AEE",
    "IN_SALA_ATENDIMENTO_ESPECIAL",
    "IN_ESPECIAL_EXCLUSIVA",
    "IN_ACESSIBILIDADE_RAMPAS",
    "IN_BANHEIRO_PNE",
    "IN_ACESSIBILIDADE_CORRIMAO",
    "IN_ACESSIBILIDADE_PISOS_TATEIS",
    "IN_ACESSIBILIDADE_SINAL_VISUAL",
    "IN_ACESSIBILIDADE_SINAL_SONORO",
    "IN_ACESSIBILIDADE_ELEVADOR",
    "QT_PROF_TRAD_LIBRAS",
    "QT_PROF_REVISOR_BRAILLE",
]

COLUNAS_MATRICULA = ["CO_ENTIDADE", "QT_MAT_ESP", "QT_MAT_ESP_CC"]

REDE_POR_TP_DEPENDENCIA = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada",
}


def carregar_escolas() -> pd.DataFrame:
    """Lê Tabela_Escola_2025.csv, filtra escolas em atividade e mapeia a rede de ensino."""
    df = pd.read_csv(
        TABELA_ESCOLA_CSV,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        usecols=COLUNAS_ESCOLA,
    )
    df = df[df["TP_SITUACAO_FUNCIONAMENTO"] == SITUACAO_EM_ATIVIDADE].copy()
    df["rede"] = df["TP_DEPENDENCIA"].map(REDE_POR_TP_DEPENDENCIA)
    return df


def carregar_matriculas() -> pd.DataFrame:
    """Lê Tabela_Matricula_2025.csv (uma linha por CO_ENTIDADE)."""
    return pd.read_csv(
        TABELA_MATRICULA_CSV,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        usecols=COLUNAS_MATRICULA,
    )


def carregar_escolas_com_matricula() -> pd.DataFrame:
    """Junta Escola x Matrícula por CO_ENTIDADE (left join — escola sem matrícula registrada vira 0)."""
    escolas = carregar_escolas()
    matriculas = carregar_matriculas()
    df = escolas.merge(matriculas, on="CO_ENTIDADE", how="left")
    df["QT_MAT_ESP"] = df["QT_MAT_ESP"].fillna(0)
    df["QT_MAT_ESP_CC"] = df["QT_MAT_ESP_CC"].fillna(0)
    return df
