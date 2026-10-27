"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md

RN-01: status/score vêm do mesmo cálculo de score-incluia, sem reinterpretação aqui.
RN-02: faixa/cor de escola usam a mesma régua de 5 faixas do município (já calculada no ETL).
RN-05: escolas com matrícula da educação especial só em classe exclusiva recebem status "na" no
Eixo IV, não um falso "nok".
RN-06 (pendência 13 da arquitetura, decisão de 2026-10-27): escola com 1 a 4 matrículas da educação
especial tem os dados protegidos na área pública. A contagem sai como None, o Eixo IV e a classe
exclusiva ficam omitidos, e o score público troca a taxa de classe comum da escola pela média das
escolas do município com 5 ou mais matrículas (da UF, se o município não tiver nenhuma) — a mesma
ideia da regra do ETL para escolas sem matrícula. Assim o score público não depende de onde esses
estudantes estudam. O ranking usa o score público. O score real continua no ETL, no score do
município e no painel privado do diretor.
"""

from typing import Optional

from app.database import get_connection
from app.features.escolas.schemas import Escola
from app.shared.classificacao import status_semaforo
from app.shared.contexto_ia.barreiras import LIMIAR_CELULA_PEQUENA
from etl.score import PESO_TAXA_CC, classificar_faixa

_COLUNAS_SELECT = (
    "co_entidade, no_entidade, sg_uf, bairro, rede, qt_mat_esp, v_taxa_cc, "
    "score_eixo_i, score_eixo_ii, score_eixo_iii, score_eixo_iv, "
    "score, faixa, cor, in_especial_exclusiva, qt_mat_esp_cc"
)

_MEDIA_DA_TAXA = "SELECT AVG(qt_mat_esp_cc * 1.0 / qt_mat_esp) FROM escolas WHERE {filtro} = ? AND qt_mat_esp >= ?"


def protegida(linha) -> bool:
    return 0 < (linha["qt_mat_esp"] or 0) < LIMIAR_CELULA_PEQUENA


def _media_da_taxa(conn, co_municipio: int, sg_uf: str) -> float:
    media = conn.execute(_MEDIA_DA_TAXA.format(filtro="co_municipio"), (co_municipio, LIMIAR_CELULA_PEQUENA)).fetchone()[0]
    if media is None:
        media = conn.execute(_MEDIA_DA_TAXA.format(filtro="sg_uf"), (sg_uf, LIMIAR_CELULA_PEQUENA)).fetchone()[0]
    return media if media is not None else 0.0


def _score_publico(linha, media: float) -> float:
    if not protegida(linha):
        return linha["score"]
    return linha["score"] + 10 * PESO_TAXA_CC * (media - linha["v_taxa_cc"])


def _linha_para_escola(linha, score: float, ranking: int, total: int) -> Escola:
    esconder = protegida(linha)
    especial_exclusiva = bool(linha["in_especial_exclusiva"]) and not esconder
    # IN_ESPECIAL_EXCLUSIVA=1 significa "ao menos uma classe exclusiva"; o Eixo IV só não se aplica
    # quando nenhuma matrícula da educação especial está em classe comum.
    sem_classe_comum = especial_exclusiva and not linha["qt_mat_esp_cc"]

    status_iv: str
    if esconder:
        status_iv = "omitido"
    elif sem_classe_comum:
        status_iv = "na"
    else:
        faixa_iv, _ = classificar_faixa(linha["score_eixo_iv"])
        status_iv = status_semaforo(faixa_iv)

    faixa_i, _ = classificar_faixa(linha["score_eixo_i"])
    faixa_ii, _ = classificar_faixa(linha["score_eixo_ii"])
    faixa_iii, _ = classificar_faixa(linha["score_eixo_iii"])
    faixa, cor = classificar_faixa(score) if esconder else (linha["faixa"], linha["cor"])

    return Escola(
        co_entidade=linha["co_entidade"],
        nome=linha["no_entidade"],
        # NO_BAIRRO vem nulo do Censo para algumas escolas — normaliza para não quebrar o schema.
        bairro=linha["bairro"] or "Não informado",
        rede=linha["rede"],
        alunos_esp=None if esconder else int(linha["qt_mat_esp"]),
        status_eixo_i=status_semaforo(faixa_i),
        status_eixo_ii=status_semaforo(faixa_ii),
        status_eixo_iii=status_semaforo(faixa_iii),
        status_eixo_iv=status_iv,
        score=score,
        faixa=faixa,
        cor=cor,
        especial_exclusiva=especial_exclusiva,
        dados_protegidos=esconder,
        ranking_municipal=ranking,
        qtd_escolas_municipio=total,
    )


def obter_escolas_por_municipio(codigo_ibge: int) -> list[Escola]:
    conn = get_connection()
    try:
        linhas = conn.execute(f"SELECT {_COLUNAS_SELECT} FROM escolas WHERE co_municipio = ?", (codigo_ibge,)).fetchall()
        if not linhas:
            return []
        media = _media_da_taxa(conn, codigo_ibge, linhas[0]["sg_uf"])
    finally:
        conn.close()

    scores = [_score_publico(linha, media) for linha in linhas]
    # Ranking "min" como no ETL (adicionar_ranking_escolas), mas sobre o score público.
    ordenados = sorted(scores, reverse=True)
    posicao = {score: ordenados.index(score) + 1 for score in set(scores)}
    escolas = [_linha_para_escola(linha, score, posicao[score], len(linhas)) for linha, score in zip(linhas, scores)]
    return sorted(escolas, key=lambda e: e.score)


def obter_escola_detalhe(co_entidade: int) -> Optional[Escola]:
    conn = get_connection()
    try:
        linha = conn.execute("SELECT co_municipio FROM escolas WHERE co_entidade = ?", (co_entidade,)).fetchone()
    finally:
        conn.close()
    if linha is None:
        return None
    return next((e for e in obter_escolas_por_municipio(linha["co_municipio"]) if e.co_entidade == co_entidade), None)
