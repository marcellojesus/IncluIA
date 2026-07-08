"""Agregação do Score Escola Sem Barreiras de escola -> município -> UF (RN-03 de
docs/business-rules/score-incluia.md: média ponderada por QT_MAT_ESP, com fallback
para média simples quando a soma de pesos do grupo é zero)."""

import pandas as pd

from etl.score import classificar_faixa

SCORE_COLS = ["score", "score_eixo_i", "score_eixo_ii", "score_eixo_iii", "score_eixo_iv"]


def _media_ponderada_fallback(valores: pd.Series, pesos: pd.Series) -> float:
    soma_peso = pesos.sum()
    if soma_peso > 0:
        return (valores * pesos).sum() / soma_peso
    return valores.mean()


def adicionar_ranking_escolas(df_escolas: pd.DataFrame) -> pd.DataFrame:
    """Posição de cada escola no ranking de score dentro do próprio município (ver
    docs/requirements/escolas.md RF-04) — mesma lógica de `ranking_no_estado` abaixo."""
    df = df_escolas.copy()
    df["ranking_no_municipio"] = (
        df.groupby("CO_MUNICIPIO")["score"].rank(method="min", ascending=False).astype(int)
    )
    df["qtd_escolas_no_municipio"] = df.groupby("CO_MUNICIPIO")["CO_ENTIDADE"].transform("count")
    return df


def _agregar_scores(df: pd.DataFrame, chave: str, peso_col: str) -> pd.DataFrame:
    """Agrega as 5 colunas de score (geral + 4 eixos) por grupo, ponderado por peso_col."""
    linhas = []
    for valor_chave, grupo in df.groupby(chave):
        pesos = grupo[peso_col]
        linha = {chave: valor_chave}
        for col in SCORE_COLS:
            linha[col] = _media_ponderada_fallback(grupo[col], pesos)
        linhas.append(linha)
    return pd.DataFrame(linhas)


_ESCOLAS_COM_COLS = {
    "escolas_com_aee": "V_AEE",
    "escolas_com_rampa": "V_rampa",
    "escolas_com_banheiro_pne": "V_banheiro_pne",
    "escolas_com_corrimao": "V_corrimao",
    "escolas_com_piso_tatil": "V_piso_tatil",
    "escolas_com_sinal_visual": "V_sinal_visual",
    "escolas_com_sinal_sonoro": "V_sinal_sonoro",
    "escolas_com_elevador": "V_elevador",
    "escolas_com_sala_atendimento_especial": "IN_SALA_ATENDIMENTO_ESPECIAL",
    "escolas_com_libras": "V_libras",
    "escolas_com_braille": "V_braille",
}


def agregar_municipios(df_escolas: pd.DataFrame) -> pd.DataFrame:
    """Um município por linha, com score agregado e indicadores gerais (ver
    docs/requirements/indicadores-municipio.md — inclui todas as variáveis binárias do Censo
    usadas na tabela de detalhamento do Decreto, não só as do cálculo do score)."""
    df_escolas = df_escolas.copy()
    # IN_SALA_ATENDIMENTO_ESPECIAL não passa por calcular_variaveis (não entra no score) —
    # normaliza aqui do mesmo jeito que os demais binários (ausente = recurso não confirmado).
    df_escolas["IN_SALA_ATENDIMENTO_ESPECIAL"] = df_escolas["IN_SALA_ATENDIMENTO_ESPECIAL"].fillna(0)

    scores = _agregar_scores(df_escolas, "CO_MUNICIPIO", "QT_MAT_ESP")

    agregacoes_contagem = {
        nome: (coluna, "sum") for nome, coluna in _ESCOLAS_COM_COLS.items()
    }
    indicadores = df_escolas.groupby("CO_MUNICIPIO").agg(
        NO_MUNICIPIO=("NO_MUNICIPIO", "first"),
        SG_UF=("SG_UF", "first"),
        CO_UF=("CO_UF", "first"),
        qtd_escolas=("CO_ENTIDADE", "count"),
        total_alunos_esp=("QT_MAT_ESP", "sum"),
        total_alunos_esp_cc=("QT_MAT_ESP_CC", "sum"),
        qt_prof_libras=("QT_PROF_TRAD_LIBRAS", "sum"),
        qt_prof_braille=("QT_PROF_REVISOR_BRAILLE", "sum"),
        **agregacoes_contagem,
    ).reset_index()

    df = indicadores.merge(scores, on="CO_MUNICIPIO")

    for nome_contagem in _ESCOLAS_COM_COLS:
        nome_pct = "pct_escolas_" + nome_contagem.removeprefix("escolas_com_")
        df[nome_pct] = df[nome_contagem] / df["qtd_escolas"]

    df["taxa_inclusao_cc"] = df.apply(
        lambda r: (r["total_alunos_esp_cc"] / r["total_alunos_esp"]) if r["total_alunos_esp"] > 0 else 0.0,
        axis=1,
    )

    faixas_cores = df["score"].apply(classificar_faixa)
    df["faixa"] = faixas_cores.apply(lambda t: t[0])
    df["cor"] = faixas_cores.apply(lambda t: t[1])

    df["ranking_no_estado"] = (
        df.groupby("SG_UF")["score"].rank(method="min", ascending=False).astype(int)
    )
    df["qtd_municipios_no_estado"] = df.groupby("SG_UF")["CO_MUNICIPIO"].transform("count")

    return df


def agregar_uf(df_municipios: pd.DataFrame) -> pd.DataFrame:
    """Uma UF por linha, com score agregado ponderado pelo total de alunos ESP do município."""
    scores = _agregar_scores(df_municipios, "SG_UF", "total_alunos_esp")

    indicadores = df_municipios.groupby("SG_UF").agg(
        CO_UF=("CO_UF", "first"),
        qtd_municipios=("CO_MUNICIPIO", "count"),
        total_alunos_esp=("total_alunos_esp", "sum"),
        qtd_escolas=("qtd_escolas", "sum"),
    ).reset_index()

    df = indicadores.merge(scores, on="SG_UF")

    faixas_cores = df["score"].apply(classificar_faixa)
    df["faixa"] = faixas_cores.apply(lambda t: t[0])
    df["cor"] = faixas_cores.apply(lambda t: t[1])

    return df
