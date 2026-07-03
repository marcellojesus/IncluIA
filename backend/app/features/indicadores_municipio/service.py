"""Spec: docs/requirements/indicadores-municipio.md, docs/business-rules/indicadores-municipio.md

RN-01 (revisada): status do semáforo e "valor" exibido reaproveitam score_eixo_i..iv — a MESMA
métrica do painel "Score por Eixo" — para nunca contradizer visualmente esse painel. RN-02: a
tabela do Decreto usa o mesmo limiar único (>=70% conforme, 40-69% parcial, <40% não conforme).
"""

from typing import Optional

from app.database import get_connection
from app.features.indicadores_municipio.schemas import (
    CriterioDecreto,
    EixoIndicador,
    MunicipioDetalhe,
    ScoreEixo,
)
from app.features.mapa.service import obter_kpis_nacionais
from app.shared.classificacao import status_semaforo
from etl.score import classificar_faixa

LIMIAR_CONFORME = 0.70
LIMIAR_PARCIAL = 0.40

_EIXOS_SCORE = [
    ("score_eixo_i", "Eixo I — AEE", "das escolas ofertam AEE"),
    ("score_eixo_ii", "Eixo II — Acessibilidade", "cobertura de acessibilidade física"),
    ("score_eixo_iii", "Eixo III — Profissionais", "cobertura de LIBRAS/Braille"),
    ("score_eixo_iv", "Eixo IV — Inclusão CC", "dos alunos ESP em classe comum"),
]

_EIXOS_SCORE_COM_PESO = [
    ("score_eixo_i", "Eixo I — AEE (30%)"),
    ("score_eixo_ii", "Eixo II — Acessibilidade (30%)"),
    ("score_eixo_iii", "Eixo III — Profissionais (25%)"),
    ("score_eixo_iv", "Eixo IV — Inclusão CC (15%)"),
]

_ICONE_POR_STATUS = {"ok": "✅", "warn": "⚠️", "nok": "❌"}

# (eixo, critério, variável do Censo, campo de % em `municipios`, campo de contagem — ou None)
_CRITERIOS_DECRETO = [
    ("I — AEE", "Oferta de AEE na escola", "TP_AEE ≠ 0", "pct_escolas_aee", "escolas_com_aee"),
    (
        "I — AEE",
        "Sala de recursos multifuncional",
        "IN_SALA_ATENDIMENTO_ESPECIAL",
        "pct_escolas_sala_atendimento_especial",
        "escolas_com_sala_atendimento_especial",
    ),
    ("II — Acessib.", "Rampa de acesso", "IN_ACESSIBILIDADE_RAMPAS", "pct_escolas_rampa", "escolas_com_rampa"),
    (
        "II — Acessib.",
        "Banheiro adaptado PNE",
        "IN_BANHEIRO_PNE",
        "pct_escolas_banheiro_pne",
        "escolas_com_banheiro_pne",
    ),
    (
        "II — Acessib.",
        "Piso tátil",
        "IN_ACESSIBILIDADE_PISOS_TATEIS",
        "pct_escolas_piso_tatil",
        "escolas_com_piso_tatil",
    ),
    (
        "II — Acessib.",
        "Corrimão e guarda-corpo",
        "IN_ACESSIBILIDADE_CORRIMAO",
        "pct_escolas_corrimao",
        "escolas_com_corrimao",
    ),
    (
        "II — Acessib.",
        "Sinalização visual",
        "IN_ACESSIBILIDADE_SINAL_VISUAL",
        "pct_escolas_sinal_visual",
        "escolas_com_sinal_visual",
    ),
    (
        "II — Acessib.",
        "Sinalização sonora",
        "IN_ACESSIBILIDADE_SINAL_SONORO",
        "pct_escolas_sinal_sonoro",
        "escolas_com_sinal_sonoro",
    ),
    ("II — Acessib.", "Elevador", "IN_ACESSIBILIDADE_ELEVADOR", "pct_escolas_elevador", "escolas_com_elevador"),
    (
        "III — Prof.",
        "Tradutor/intérprete de LIBRAS",
        "QT_PROF_TRAD_LIBRAS > 0",
        "pct_escolas_libras",
        "escolas_com_libras",
    ),
    (
        "III — Prof.",
        "Revisor de Braille",
        "QT_PROF_REVISOR_BRAILLE > 0",
        "pct_escolas_braille",
        "escolas_com_braille",
    ),
    (
        "IV — Incl. CC",
        "Taxa de matrícula em classe comum",
        "QT_MAT_ESP_CC / QT_MAT_ESP",
        "taxa_inclusao_cc",
        None,
    ),
]


def _conformidade(pct: float) -> str:
    if pct >= LIMIAR_CONFORME:
        return "conforme"
    if pct >= LIMIAR_PARCIAL:
        return "parcial"
    return "nao_conforme"


def _pct_str(pct: float) -> str:
    return f"{pct * 100:.0f}%"


def _formatar_score(score: float) -> str:
    return f"{score:.1f}".replace(".", ",")


def _montar_eixos(linha) -> list[EixoIndicador]:
    eixos = []
    for coluna, label, subtexto in _EIXOS_SCORE:
        score_eixo = linha[coluna]
        faixa, _ = classificar_faixa(score_eixo)
        status = status_semaforo(faixa)
        eixos.append(
            EixoIndicador(
                status=status,
                icone=_ICONE_POR_STATUS[status],
                label=label,
                valor=_pct_str(score_eixo / 10),
                subtexto=subtexto,
            )
        )
    return eixos


def _montar_score_eixos(linha) -> list[ScoreEixo]:
    resultado = []
    for coluna, label in _EIXOS_SCORE_COM_PESO:
        score_eixo = linha[coluna]
        _, cor = classificar_faixa(score_eixo)
        resultado.append(
            ScoreEixo(
                label=label,
                percentual=score_eixo / 10 * 100,
                valor=_formatar_score(score_eixo),
                cor=cor,
            )
        )
    return resultado


def _obter_score_medio_uf(conn, sigla: str) -> float:
    linha = conn.execute(
        "SELECT SUM(score * total_alunos_esp) AS soma_ponderada, "
        "SUM(total_alunos_esp) AS soma_pesos, AVG(score) AS media_simples "
        "FROM municipios WHERE sg_uf = ?",
        (sigla,),
    ).fetchone()
    if linha["soma_pesos"]:
        return linha["soma_ponderada"] / linha["soma_pesos"]
    return linha["media_simples"] or 0.0


def _int_str(valor) -> str:
    return f"{int(round(valor)):,}".replace(",", ".")


def _montar_dados_gerais(linha, conn) -> list[tuple[str, str]]:
    score_medio_estadual = _obter_score_medio_uf(conn, linha["sg_uf"])
    score_medio_nacional = obter_kpis_nacionais().score_medio_nacional

    return [
        ("Total de alunos com deficiência (ESP)", _int_str(linha["total_alunos_esp"])),
        (
            "Escolas com AEE",
            f"{_pct_str(linha['pct_escolas_aee'])} ({_int_str(linha['escolas_com_aee'])}/{linha['qtd_escolas']})",
        ),
        ("Em classe comum", _pct_str(linha["taxa_inclusao_cc"])),
        ("Score médio estadual", _formatar_score(score_medio_estadual)),
        ("Score médio nacional", _formatar_score(score_medio_nacional)),
        ("Professores LIBRAS", _int_str(linha["qt_prof_libras"])),
        ("Revisores Braille", _int_str(linha["qt_prof_braille"])),
        (
            "Escolas com rampa",
            f"{_pct_str(linha['pct_escolas_rampa'])} ({_int_str(linha['escolas_com_rampa'])}/{linha['qtd_escolas']})",
        ),
        (
            "Escolas com piso tátil",
            f"{_pct_str(linha['pct_escolas_piso_tatil'])} ({_int_str(linha['escolas_com_piso_tatil'])}/{linha['qtd_escolas']})",
        ),
        (
            "Escolas com banheiro PNE",
            f"{_pct_str(linha['pct_escolas_banheiro_pne'])} ({_int_str(linha['escolas_com_banheiro_pne'])}/{linha['qtd_escolas']})",
        ),
        ("Ranking no estado", f"#{linha['ranking_no_estado']} de {linha['qtd_municipios_no_estado']}"),
    ]


def _montar_detalhamento_decreto(linha) -> list[CriterioDecreto]:
    linhas = []
    for eixo, criterio, variavel, campo_pct, campo_contagem in _CRITERIOS_DECRETO:
        pct = linha[campo_pct]
        if campo_contagem:
            resultado = f"{_pct_str(pct)} ({_int_str(linha[campo_contagem])}/{linha['qtd_escolas']})"
        else:
            resultado = _pct_str(pct)
        linhas.append(
            CriterioDecreto(
                eixo=eixo,
                criterio=criterio,
                variavel_censo=variavel,
                resultado=resultado,
                conformidade=_conformidade(pct),
            )
        )
    return linhas


def obter_municipio_detalhe(codigo_ibge: int) -> Optional[MunicipioDetalhe]:
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT * FROM municipios WHERE co_municipio = ?", (codigo_ibge,)
        ).fetchone()
        if linha is None:
            return None

        return MunicipioDetalhe(
            codigo_ibge=linha["co_municipio"],
            nome=linha["no_municipio"],
            uf=linha["sg_uf"],
            score=linha["score"],
            faixa=linha["faixa"],
            cor=linha["cor"],
            eixos=_montar_eixos(linha),
            score_eixos=_montar_score_eixos(linha),
            dados_gerais=_montar_dados_gerais(linha, conn),
            detalhamento_decreto=_montar_detalhamento_decreto(linha),
        )
    finally:
        conn.close()
