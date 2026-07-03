"""Spec: docs/requirements/mapa.md, docs/business-rules/mapa.md

Consultas sobre data/incluia.db (gerado pela feature score-incluia, backend/etl/).
"""

from app.database import get_connection
from app.features.mapa.schemas import KpisNacionais, MunicipioRanking, MunicipioResumo, RankingUf
from etl.score import LIMIAR_SCORE_DESEJADO

# RN-04 de docs/business-rules/mapa.md: limiar absoluto de score, o mesmo da faixa "Crítico"
# na metodologia do Score IncluIA (ver metodologia_score.md §5) — não é um "top N piores".
LIMIAR_CRITICO = 3.0


def _linha_para_municipio_resumo(linha) -> MunicipioResumo:
    return MunicipioResumo(
        codigo_ibge=linha["co_municipio"],
        nome=linha["no_municipio"],
        uf=linha["sg_uf"],
        score=linha["score"],
        faixa=linha["faixa"],
        cor=linha["cor"],
    )


def _linha_para_municipio_ranking(linha) -> MunicipioRanking:
    return MunicipioRanking(
        **_linha_para_municipio_resumo(linha).model_dump(),
        ranking_no_estado=linha["ranking_no_estado"],
        qtd_municipios_no_estado=linha["qtd_municipios_no_estado"],
    )


def obter_kpis_nacionais() -> KpisNacionais:
    conn = get_connection()
    try:
        municipios_criticos = conn.execute(
            "SELECT COUNT(*) AS n FROM municipios WHERE score < ?", (LIMIAR_CRITICO,)
        ).fetchone()["n"]

        escolas_sem_aee = conn.execute(
            "SELECT COUNT(*) AS n FROM escolas WHERE tp_aee = 0"
        ).fetchone()["n"]

        municipios_mapeados = conn.execute("SELECT COUNT(*) AS n FROM municipios").fetchone()["n"]

        media = conn.execute(
            "SELECT SUM(score * total_alunos_esp) AS soma_ponderada, "
            "SUM(total_alunos_esp) AS soma_pesos, AVG(score) AS media_simples FROM municipios"
        ).fetchone()
        if media["soma_pesos"]:
            score_medio_nacional = media["soma_ponderada"] / media["soma_pesos"]
        else:
            score_medio_nacional = media["media_simples"] or 0.0

        return KpisNacionais(
            municipios_criticos=municipios_criticos,
            escolas_sem_aee=escolas_sem_aee,
            score_medio_nacional=score_medio_nacional,
            score_desejado=LIMIAR_SCORE_DESEJADO,
            municipios_mapeados=municipios_mapeados,
            total_alunos_esp=media["soma_pesos"] or 0,
        )
    finally:
        conn.close()


def obter_municipios_por_uf(sigla: str) -> list[MunicipioResumo]:
    conn = get_connection()
    try:
        linhas = conn.execute(
            "SELECT co_municipio, no_municipio, sg_uf, score, faixa, cor "
            "FROM municipios WHERE sg_uf = ?",
            (sigla.upper(),),
        ).fetchall()
        return [_linha_para_municipio_resumo(linha) for linha in linhas]
    finally:
        conn.close()


def obter_ranking_por_uf(sigla: str) -> RankingUf:
    conn = get_connection()
    try:
        colunas = (
            "co_municipio, no_municipio, sg_uf, score, faixa, cor, "
            "ranking_no_estado, qtd_municipios_no_estado"
        )
        melhores = conn.execute(
            f"SELECT {colunas} FROM municipios WHERE sg_uf = ? ORDER BY score DESC LIMIT 5",
            (sigla.upper(),),
        ).fetchall()
        criticos = conn.execute(
            f"SELECT {colunas} FROM municipios WHERE sg_uf = ? AND score < ? ORDER BY score ASC",
            (sigla.upper(), LIMIAR_CRITICO),
        ).fetchall()
        return RankingUf(
            melhores=[_linha_para_municipio_ranking(linha) for linha in melhores],
            criticos=[_linha_para_municipio_ranking(linha) for linha in criticos],
        )
    finally:
        conn.close()
