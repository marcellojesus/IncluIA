"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md

RF-06/RN-08: os 4 eixos são gerados em paralelo, cache independente por eixo. RF-07/RN-04:
o contexto enviado à IA é só o que já está pronto em indicadores_municipio (agregados públicos,
nenhum dado pessoal). RN-02: se todos os provedores falharem, cai para dados brutos sem narrativa.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import get_connection
from app.features.diagnostico_ia.ai_client import gerar_narrativa
from app.features.diagnostico_ia.cache import calcular_chave, obter_do_cache, salvar_no_cache
from app.features.diagnostico_ia.schemas import DiagnosticoEixo, RecomendacaoIA
from app.features.indicadores_municipio.schemas import EixoIndicador
from app.features.indicadores_municipio.service import obter_municipio_detalhe

logger = logging.getLogger("diagnostico_ia")

EIXOS_ROMANOS = ["I", "II", "III", "IV"]

_COLUNA_SCORE_EIXO = {
    "I": "score_eixo_i",
    "II": "score_eixo_ii",
    "III": "score_eixo_iii",
    "IV": "score_eixo_iv",
}

# Rótulo usado em CriterioDecreto.eixo (ver indicadores_municipio/service.py::_CRITERIOS_DECRETO)
_LABEL_DECRETO_POR_EIXO = {
    "I": "I — AEE",
    "II": "II — Acessib.",
    "III": "III — Prof.",
    "IV": "IV — Incl. CC",
}

# RN-06 (revisada): só citamos artigo específico quando validado contra o texto oficial —
# ver docs/legislacao.md para o mapeamento completo e o trecho literal de cada citação.
_ARTIGO_VALIDADO_POR_EIXO = {
    "I": "Art. 5º a 10 do Decreto 12.686/2025 (organização e objetivos do AEE)",
    "II": "Art. 28, II e XVI, da Lei 13.146/2015 (LBI) — acessibilidade às edificações escolares",
    "III": "Art. 28, XI, XII e § 2º, da Lei 13.146/2015 (LBI) — formação e oferta de LIBRAS/Braille",
    "IV": "Art. 1º, § 3º, e Art. 8º do Decreto 12.686/2025 — inclusão em classes comuns",
}

_STATUS_TEXTO = {"ok": "adequada", "warn": "em desenvolvimento", "nok": "crítica"}


def _fallback_dados_brutos(eixo_romano: str, eixo_indicador: EixoIndicador) -> DiagnosticoEixo:
    situacao_texto = _STATUS_TEXTO[eixo_indicador.status]
    analise = (
        f"{eixo_indicador.label} está com situação {situacao_texto}: {eixo_indicador.valor} "
        f"({eixo_indicador.subtexto}). Diagnóstico narrativo por IA indisponível no momento — "
        "exibindo apenas os dados já calculados do Censo Escolar."
    )
    return DiagnosticoEixo(
        eixo=eixo_romano,
        situacao=f"Situação {situacao_texto}",
        analise=analise,
        alerta_legal=None,
        recomendacoes=[],
        referencia_municipio=None,
        modelo_usado="dados_brutos",
        gerado_em=datetime.now(timezone.utc).isoformat(),
    )


def _obter_benchmarking(codigo_ibge: int, uf: str, eixo_romano: str, score_atual: float) -> list[dict]:
    coluna = _COLUNA_SCORE_EIXO[eixo_romano]
    conn = get_connection()
    try:
        linhas = conn.execute(
            f"SELECT no_municipio, {coluna} AS score FROM municipios "
            f"WHERE sg_uf = ? AND co_municipio != ? AND {coluna} > ? "
            f"ORDER BY {coluna} DESC LIMIT 3",
            (uf, codigo_ibge, score_atual),
        ).fetchall()
        return [{"nome": linha["no_municipio"], "score": linha["score"]} for linha in linhas]
    finally:
        conn.close()


def _aplicar_ajuste(codigo_ibge: int, eixo_romano: str, diagnostico: DiagnosticoEixo) -> DiagnosticoEixo:
    """RN-09: se o chat já ajustou a recomendação deste eixo, ela substitui a gerada
    automaticamente — mesmo após "Regenerar" o diagnóstico base (decisão deliberada)."""
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT recomendacoes_json, ajustado_em FROM chat_diagnostico_recomendacoes_ajustadas "
            "WHERE codigo_ibge = ? AND eixo = ?",
            (codigo_ibge, eixo_romano),
        ).fetchone()
    finally:
        conn.close()

    if linha is None:
        return diagnostico

    recomendacoes = [RecomendacaoIA.model_validate(r) for r in json.loads(linha["recomendacoes_json"])]
    return diagnostico.model_copy(
        update={"recomendacoes": recomendacoes, "recomendacao_ajustada_em": linha["ajustado_em"]}
    )


def _montar_contexto_diagnostico(codigo_ibge: int, indice: int, eixo_romano: str, municipio) -> dict:
    """Contexto enviado à IA para gerar (ou reprocessar, ver chat_service.py) o diagnóstico de um
    eixo — extraído para ser reaproveitado tanto na geração automática quanto no reprocessamento
    via chat (RN-10 de docs/business-rules/diagnostico-ia.md)."""
    eixo_indicador = municipio.eixos[indice]
    score_eixo_info = municipio.score_eixos[indice]
    score_eixo = score_eixo_info.percentual / 10
    label_decreto = _LABEL_DECRETO_POR_EIXO[eixo_romano]
    criterios = [c for c in municipio.detalhamento_decreto if c.eixo == label_decreto]
    benchmarking = _obter_benchmarking(codigo_ibge, municipio.uf, eixo_romano, score_eixo)

    return {
        "nome_municipio": municipio.nome,
        "uf": municipio.uf,
        "eixo_label": score_eixo_info.label,
        "status": eixo_indicador.status,
        "valor": eixo_indicador.valor,
        "subtexto": eixo_indicador.subtexto,
        "score_eixo": score_eixo,
        "artigo_legal_validado": _ARTIGO_VALIDADO_POR_EIXO.get(eixo_romano),
        "criterios_decreto": [
            {
                "criterio": c.criterio,
                "variavel_censo": c.variavel_censo,
                "resultado": c.resultado,
                "conformidade": c.conformidade,
            }
            for c in criterios
        ],
        "benchmarking": benchmarking,
    }


async def _obter_diagnostico_eixo(
    codigo_ibge: int, indice: int, eixo_romano: str, municipio, forcar: bool
) -> DiagnosticoEixo:
    chave = calcular_chave(codigo_ibge, eixo_romano)
    if not forcar:
        cacheado = obter_do_cache(chave)
        if cacheado is not None:
            return _aplicar_ajuste(codigo_ibge, eixo_romano, cacheado)

    eixo_indicador = municipio.eixos[indice]
    contexto = _montar_contexto_diagnostico(codigo_ibge, indice, eixo_romano, municipio)

    try:
        resposta_ia, modelo = await gerar_narrativa(contexto)
        diagnostico = DiagnosticoEixo(
            eixo=eixo_romano,
            situacao=resposta_ia.situacao,
            analise=resposta_ia.analise,
            alerta_legal=resposta_ia.alerta_legal,
            recomendacoes=resposta_ia.recomendacoes,
            referencia_municipio=resposta_ia.referencia_municipio,
            modelo_usado=modelo,
            gerado_em=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:  # noqa: BLE001 — qualquer falha aqui vira o fallback de dados brutos
        logger.warning("IA indisponível para município %s eixo %s: %s", codigo_ibge, eixo_romano, exc)
        diagnostico = _fallback_dados_brutos(eixo_romano, eixo_indicador)

    salvar_no_cache(chave, codigo_ibge, eixo_romano, diagnostico)
    return _aplicar_ajuste(codigo_ibge, eixo_romano, diagnostico)


async def obter_diagnostico_municipio(codigo_ibge: int, forcar: bool) -> Optional[list[DiagnosticoEixo]]:
    municipio = obter_municipio_detalhe(codigo_ibge)
    if municipio is None:
        return None

    tarefas = [
        _obter_diagnostico_eixo(codigo_ibge, indice, eixo_romano, municipio, forcar)
        for indice, eixo_romano in enumerate(EIXOS_ROMANOS)
    ]
    return list(await asyncio.gather(*tarefas))
