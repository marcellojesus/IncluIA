"""Cálculo do Score Escola Sem Barreiras por escola, conforme metodologia_score.md (com as correções
de TP_AEE e piso tátil confirmadas contra o dicionário oficial do Censo 2025)."""

import numpy as np
import pandas as pd

# Pesos — metodologia_score.md §3/§4.1 (soma = 1,00)
PESO_AEE = 0.30
PESO_TAXA_CC = 0.15
PESO_LIBRAS = 0.15
PESO_BRAILLE = 0.10
PESO_RAMPA = 0.08
PESO_BANHEIRO_PNE = 0.07
PESO_CORRIMAO = 0.06
PESO_PISO_TATIL = 0.04
PESO_SINAL_VISUAL = 0.02
PESO_SINAL_SONORO = 0.02
PESO_ELEVADOR = 0.01

PESO_EIXO_III = PESO_LIBRAS + PESO_BRAILLE  # 0,25 — Profissionais (=D2)
PESO_EIXO_II = (
    PESO_RAMPA
    + PESO_BANHEIRO_PNE
    + PESO_CORRIMAO
    + PESO_PISO_TATIL
    + PESO_SINAL_VISUAL
    + PESO_SINAL_SONORO
    + PESO_ELEVADOR
)  # 0,30 — Acessibilidade Física (=D3)

FAIXAS = [
    (8.5, "Referência", "#1351B4"),
    (7.0, "Adequado", "#168821"),
    (5.0, "Em desenvolvimento", "#E6B800"),
    (3.0, "Insuficiente", "#E05C00"),
    (0.0, "Crítico", "#E52207"),
]

# RN-07 de docs/business-rules/mapa.md: "Score Desejado" = limiar mínimo da faixa "Adequado" —
# derivado de FAIXAS, não um valor novo mantido em paralelo.
LIMIAR_SCORE_DESEJADO = next(limite for limite, faixa, _ in FAIXAS if faixa == "Adequado")


def classificar_faixa(score: float) -> tuple[str, str]:
    """Retorna (faixa, cor_hex) conforme metodologia_score.md §5."""
    for limite, faixa, cor in FAIXAS:
        if score >= limite:
            return faixa, cor
    return FAIXAS[-1][1], FAIXAS[-1][2]


def _binario(coluna: pd.Series) -> pd.Series:
    """Campos IN_* ausentes são tratados como 0 (recurso não confirmado como presente)."""
    return coluna.fillna(0).astype(float)


def calcular_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona as colunas V_* (0,0 a 1,0) normalizadas a partir dos campos brutos do Censo."""
    df = df.copy()

    # V_AEE: TP_AEE=0 -> não oferece; TP_AEE em {1,2} -> oferece (ver correção em metodologia_score.md)
    tp_aee = df["TP_AEE"].fillna(0)
    df["V_AEE"] = np.where(tp_aee == 0, 0.0, 1.0)

    df["V_libras"] = np.where(df["QT_PROF_TRAD_LIBRAS"].fillna(0) > 0, 1.0, 0.0)
    df["V_braille"] = np.where(df["QT_PROF_REVISOR_BRAILLE"].fillna(0) > 0, 1.0, 0.0)

    df["V_rampa"] = _binario(df["IN_ACESSIBILIDADE_RAMPAS"])
    df["V_banheiro_pne"] = _binario(df["IN_BANHEIRO_PNE"])
    df["V_corrimao"] = _binario(df["IN_ACESSIBILIDADE_CORRIMAO"])
    df["V_piso_tatil"] = _binario(df["IN_ACESSIBILIDADE_PISOS_TATEIS"])
    df["V_sinal_visual"] = _binario(df["IN_ACESSIBILIDADE_SINAL_VISUAL"])
    df["V_sinal_sonoro"] = _binario(df["IN_ACESSIBILIDADE_SINAL_SONORO"])
    df["V_elevador"] = _binario(df["IN_ACESSIBILIDADE_ELEVADOR"])

    # V_taxa_cc: taxa real quando há aluno ESP matriculado; senão, média do município (2 passadas).
    # IN_ESPECIAL_EXCLUSIVA=1 não zera mais a taxa (metodologia_score.md v1.1): no dicionário do
    # Censo 2025 o campo significa "possui ao menos uma classe especial exclusiva", e a taxa real
    # já reflete as matrículas em classe exclusiva.
    tem_matricula_esp = df["QT_MAT_ESP"] > 0
    taxa_bruta = pd.Series(np.nan, index=df.index)
    taxa_bruta[tem_matricula_esp] = (
        df.loc[tem_matricula_esp, "QT_MAT_ESP_CC"] / df.loc[tem_matricula_esp, "QT_MAT_ESP"]
    )
    media_municipio = taxa_bruta.groupby(df["CO_MUNICIPIO"]).transform("mean")
    df["V_taxa_cc"] = taxa_bruta.fillna(media_municipio).fillna(0.0)

    return df


def calcular_score_escola(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona score geral, score por eixo (I-IV), faixa e cor a cada escola."""
    df = calcular_variaveis(df)

    score_d3 = (
        PESO_RAMPA * df["V_rampa"]
        + PESO_BANHEIRO_PNE * df["V_banheiro_pne"]
        + PESO_CORRIMAO * df["V_corrimao"]
        + PESO_PISO_TATIL * df["V_piso_tatil"]
        + PESO_SINAL_VISUAL * df["V_sinal_visual"]
        + PESO_SINAL_SONORO * df["V_sinal_sonoro"]
        + PESO_ELEVADOR * df["V_elevador"]
    )
    score_d2 = PESO_LIBRAS * df["V_libras"] + PESO_BRAILLE * df["V_braille"]

    df["score"] = 10 * (
        PESO_AEE * df["V_AEE"] + PESO_TAXA_CC * df["V_taxa_cc"] + score_d2 + score_d3
    )
    df["score_eixo_i"] = 10 * df["V_AEE"]
    df["score_eixo_ii"] = 10 * score_d3 / PESO_EIXO_II
    df["score_eixo_iii"] = 10 * score_d2 / PESO_EIXO_III
    df["score_eixo_iv"] = 10 * df["V_taxa_cc"]

    faixas_cores = df["score"].apply(classificar_faixa)
    df["faixa"] = faixas_cores.apply(lambda t: t[0])
    df["cor"] = faixas_cores.apply(lambda t: t[1])

    return df
