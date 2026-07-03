"""Persistência dos resultados do ETL em SQLite (tabelas escolas, municipios, uf_agregado —
ver docs/requirements/score-incluia.md)."""

import sqlite3

import pandas as pd

from etl.config import CENSO_VERSAO, SQLITE_PATH

COLUNAS_ESCOLAS = {
    "CO_ENTIDADE": "co_entidade",
    "NO_ENTIDADE": "no_entidade",
    "CO_MUNICIPIO": "co_municipio",
    "NO_MUNICIPIO": "no_municipio",
    "SG_UF": "sg_uf",
    "CO_UF": "co_uf",
    "NO_BAIRRO": "bairro",
    "rede": "rede",
    "TP_AEE": "tp_aee",
    "IN_ESPECIAL_EXCLUSIVA": "in_especial_exclusiva",
    "QT_MAT_ESP": "qt_mat_esp",
    "QT_MAT_ESP_CC": "qt_mat_esp_cc",
    "V_AEE": "v_aee",
    "V_taxa_cc": "v_taxa_cc",
    "V_libras": "v_libras",
    "V_braille": "v_braille",
    "V_rampa": "v_rampa",
    "V_banheiro_pne": "v_banheiro_pne",
    "V_corrimao": "v_corrimao",
    "V_piso_tatil": "v_piso_tatil",
    "V_sinal_visual": "v_sinal_visual",
    "V_sinal_sonoro": "v_sinal_sonoro",
    "V_elevador": "v_elevador",
    "score": "score",
    "score_eixo_i": "score_eixo_i",
    "score_eixo_ii": "score_eixo_ii",
    "score_eixo_iii": "score_eixo_iii",
    "score_eixo_iv": "score_eixo_iv",
    "faixa": "faixa",
    "cor": "cor",
    "ranking_no_municipio": "ranking_no_municipio",
    "qtd_escolas_no_municipio": "qtd_escolas_no_municipio",
}

COLUNAS_MUNICIPIOS = {
    "CO_MUNICIPIO": "co_municipio",
    "NO_MUNICIPIO": "no_municipio",
    "SG_UF": "sg_uf",
    "CO_UF": "co_uf",
    "qtd_escolas": "qtd_escolas",
    "total_alunos_esp": "total_alunos_esp",
    "total_alunos_esp_cc": "total_alunos_esp_cc",
    "escolas_com_aee": "escolas_com_aee",
    "pct_escolas_aee": "pct_escolas_aee",
    "qt_prof_libras": "qt_prof_libras",
    "qt_prof_braille": "qt_prof_braille",
    "escolas_com_rampa": "escolas_com_rampa",
    "pct_escolas_rampa": "pct_escolas_rampa",
    "escolas_com_piso_tatil": "escolas_com_piso_tatil",
    "pct_escolas_piso_tatil": "pct_escolas_piso_tatil",
    "escolas_com_banheiro_pne": "escolas_com_banheiro_pne",
    "pct_escolas_banheiro_pne": "pct_escolas_banheiro_pne",
    "escolas_com_corrimao": "escolas_com_corrimao",
    "pct_escolas_corrimao": "pct_escolas_corrimao",
    "escolas_com_sinal_visual": "escolas_com_sinal_visual",
    "pct_escolas_sinal_visual": "pct_escolas_sinal_visual",
    "escolas_com_sinal_sonoro": "escolas_com_sinal_sonoro",
    "pct_escolas_sinal_sonoro": "pct_escolas_sinal_sonoro",
    "escolas_com_elevador": "escolas_com_elevador",
    "pct_escolas_elevador": "pct_escolas_elevador",
    "escolas_com_sala_atendimento_especial": "escolas_com_sala_atendimento_especial",
    "pct_escolas_sala_atendimento_especial": "pct_escolas_sala_atendimento_especial",
    "escolas_com_libras": "escolas_com_libras",
    "pct_escolas_libras": "pct_escolas_libras",
    "escolas_com_braille": "escolas_com_braille",
    "pct_escolas_braille": "pct_escolas_braille",
    "taxa_inclusao_cc": "taxa_inclusao_cc",
    "score": "score",
    "score_eixo_i": "score_eixo_i",
    "score_eixo_ii": "score_eixo_ii",
    "score_eixo_iii": "score_eixo_iii",
    "score_eixo_iv": "score_eixo_iv",
    "faixa": "faixa",
    "cor": "cor",
    "ranking_no_estado": "ranking_no_estado",
    "qtd_municipios_no_estado": "qtd_municipios_no_estado",
}

COLUNAS_UF = {
    "SG_UF": "sg_uf",
    "CO_UF": "co_uf",
    "qtd_municipios": "qtd_municipios",
    "qtd_escolas": "qtd_escolas",
    "total_alunos_esp": "total_alunos_esp",
    "score": "score",
    "score_eixo_i": "score_eixo_i",
    "score_eixo_ii": "score_eixo_ii",
    "score_eixo_iii": "score_eixo_iii",
    "score_eixo_iv": "score_eixo_iv",
    "faixa": "faixa",
    "cor": "cor",
}


def _preparar(df: pd.DataFrame, mapa_colunas: dict) -> pd.DataFrame:
    saida = df[list(mapa_colunas.keys())].rename(columns=mapa_colunas)
    saida["censo_versao"] = CENSO_VERSAO
    return saida


def persistir(df_escolas: pd.DataFrame, df_municipios: pd.DataFrame, df_uf: pd.DataFrame) -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    try:
        _preparar(df_escolas, COLUNAS_ESCOLAS).to_sql("escolas", conn, if_exists="replace", index=False)
        _preparar(df_municipios, COLUNAS_MUNICIPIOS).to_sql(
            "municipios", conn, if_exists="replace", index=False
        )
        _preparar(df_uf, COLUNAS_UF).to_sql("uf_agregado", conn, if_exists="replace", index=False)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_escolas_municipio ON escolas(co_municipio)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_municipios_uf ON municipios(sg_uf)")
        conn.commit()
    finally:
        conn.close()
