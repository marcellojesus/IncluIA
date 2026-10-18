"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md

RN-01: status/score vêm do mesmo cálculo de score-incluia, sem reinterpretação aqui.
RN-02: faixa/cor de escola usam a mesma régua de 5 faixas do município (já calculada no ETL).
RN-05: escolas com matrícula da educação especial só em classe exclusiva recebem status "na" no
Eixo IV, não um falso "nok".
"""

from typing import Optional

from app.database import get_connection
from app.features.escolas.schemas import Escola
from app.shared.classificacao import status_semaforo
from etl.score import classificar_faixa

_COLUNAS_SELECT = (
    "co_entidade, no_entidade, bairro, rede, qt_mat_esp, "
    "score_eixo_i, score_eixo_ii, score_eixo_iii, score_eixo_iv, "
    "score, faixa, cor, in_especial_exclusiva, qt_mat_esp_cc, ranking_no_municipio, "
    "qtd_escolas_no_municipio"
)


def _linha_para_escola(linha) -> Escola:
    especial_exclusiva = bool(linha["in_especial_exclusiva"])
    # IN_ESPECIAL_EXCLUSIVA=1 significa "ao menos uma classe exclusiva"; o Eixo IV só não se aplica
    # quando nenhuma matrícula da educação especial está em classe comum.
    sem_classe_comum = especial_exclusiva and not linha["qt_mat_esp_cc"]

    status_iv: str
    if sem_classe_comum:
        status_iv = "na"
    else:
        faixa_iv, _ = classificar_faixa(linha["score_eixo_iv"])
        status_iv = status_semaforo(faixa_iv)

    faixa_i, _ = classificar_faixa(linha["score_eixo_i"])
    faixa_ii, _ = classificar_faixa(linha["score_eixo_ii"])
    faixa_iii, _ = classificar_faixa(linha["score_eixo_iii"])

    return Escola(
        co_entidade=linha["co_entidade"],
        nome=linha["no_entidade"],
        # NO_BAIRRO vem nulo do Censo para algumas escolas — normaliza para não quebrar o schema.
        bairro=linha["bairro"] or "Não informado",
        rede=linha["rede"],
        alunos_esp=int(linha["qt_mat_esp"]),
        status_eixo_i=status_semaforo(faixa_i),
        status_eixo_ii=status_semaforo(faixa_ii),
        status_eixo_iii=status_semaforo(faixa_iii),
        status_eixo_iv=status_iv,
        score=linha["score"],
        faixa=linha["faixa"],
        cor=linha["cor"],
        especial_exclusiva=especial_exclusiva,
        ranking_municipal=linha["ranking_no_municipio"],
        qtd_escolas_municipio=linha["qtd_escolas_no_municipio"],
    )


def obter_escolas_por_municipio(codigo_ibge: int) -> list[Escola]:
    conn = get_connection()
    try:
        linhas = conn.execute(
            f"SELECT {_COLUNAS_SELECT} FROM escolas WHERE co_municipio = ? ORDER BY score ASC",
            (codigo_ibge,),
        ).fetchall()
        return [_linha_para_escola(linha) for linha in linhas]
    finally:
        conn.close()


def obter_escola_detalhe(co_entidade: int) -> Optional[Escola]:
    conn = get_connection()
    try:
        linha = conn.execute(
            f"SELECT {_COLUNAS_SELECT} FROM escolas WHERE co_entidade = ?", (co_entidade,)
        ).fetchone()
        if linha is None:
            return None
        return _linha_para_escola(linha)
    finally:
        conn.close()
