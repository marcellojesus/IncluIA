"""Orquestra o ETL do Score IncluIA: carga -> score -> agregação -> persistência.

Uso: python run_etl.py   (a partir da pasta backend/)
"""

import time

from etl.aggregate import adicionar_ranking_escolas, agregar_municipios, agregar_uf
from etl.load import carregar_escolas_com_matricula
from etl.persist import persistir
from etl.score import calcular_score_escola


def main() -> None:
    inicio = time.time()

    print("1/4 — Carregando e cruzando Tabela_Escola_2025 x Tabela_Matricula_2025...")
    df_escolas = carregar_escolas_com_matricula()
    print(f"     {len(df_escolas):,} escolas em atividade carregadas.")

    print("2/4 — Calculando o Score IncluIA por escola...")
    df_escolas = calcular_score_escola(df_escolas)
    df_escolas = adicionar_ranking_escolas(df_escolas)

    print("3/4 — Agregando para município e UF...")
    df_municipios = agregar_municipios(df_escolas)
    df_uf = agregar_uf(df_municipios)
    print(f"     {len(df_municipios):,} municípios, {len(df_uf)} UFs.")

    print("4/4 — Persistindo em SQLite (data/incluia.db)...")
    persistir(df_escolas, df_municipios, df_uf)

    duracao = time.time() - inicio
    print(f"\nETL concluído em {duracao:.1f}s.\n")

    print("Distribuição de escolas por faixa:")
    print(df_escolas["faixa"].value_counts().to_string())

    print("\nDistribuição de municípios por faixa:")
    print(df_municipios["faixa"].value_counts().to_string())

    print("\nTop 5 municípios (score):")
    print(
        df_municipios.sort_values("score", ascending=False)
        .head(5)[["NO_MUNICIPIO", "SG_UF", "score", "faixa"]]
        .to_string(index=False)
    )

    print("\nTop 5 municípios críticos (score):")
    print(
        df_municipios.sort_values("score", ascending=True)
        .head(5)[["NO_MUNICIPIO", "SG_UF", "score", "faixa"]]
        .to_string(index=False)
    )

    # Sanity check: recalcular manualmente o score de 1 município e comparar com o valor agregado
    municipio_teste = df_municipios.iloc[0]
    escolas_do_municipio = df_escolas[df_escolas["CO_MUNICIPIO"] == municipio_teste["CO_MUNICIPIO"]]
    peso_total = escolas_do_municipio["QT_MAT_ESP"].sum()
    if peso_total > 0:
        score_manual = (
            escolas_do_municipio["score"] * escolas_do_municipio["QT_MAT_ESP"]
        ).sum() / peso_total
    else:
        score_manual = escolas_do_municipio["score"].mean()
    print(
        f"\nSanity check — {municipio_teste['NO_MUNICIPIO']}/{municipio_teste['SG_UF']}: "
        f"score agregado={municipio_teste['score']:.4f} vs. recalculado manualmente={score_manual:.4f}"
    )
    assert abs(municipio_teste["score"] - score_manual) < 1e-6, "Divergência no sanity check!"
    print("OK — os valores batem.")


if __name__ == "__main__":
    main()
