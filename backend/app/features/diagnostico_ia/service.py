"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md

Narrativa pública do município, só leitura e sem login (impacto-fase-1.md, opção 2): gerada uma vez
por edição do Censo e guardada. RF-06/RN-08: os 4 eixos são gerados em paralelo, guardados por eixo. RF-07/RN-04:
o contexto enviado à IA é só o que já está pronto em indicadores_municipio (agregados públicos,
nenhum dado pessoal). RN-02: se todos os provedores falharem, cai para dados brutos sem narrativa.
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from app.database import get_connection
from app.features.diagnostico_ia.narrativa import gerar_narrativa
from app.shared.ai_client import descrever_falha
from app.features.diagnostico_ia.cache import calcular_chave, obter_do_cache, salvar_no_cache
from app.features.diagnostico_ia.schemas import NarrativaEixo, NarrativaMunicipio
from app.features.indicadores_municipio.schemas import EixoIndicador
from app.features.indicadores_municipio.service import obter_municipio_detalhe
from etl.config import CENSO_VERSAO

logger = logging.getLogger("diagnostico_ia")

EIXOS_ROMANOS = ["I", "II", "III", "IV"]
ESPERA_APOS_FALHA = 600.0
"""Segundos sem nova chamada à IA para um município depois que todos os provedores falharam."""

_travas: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
_falhou_em: dict[int, float] = {}

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


def _fallback_dados_brutos(eixo_romano: str, eixo_indicador: EixoIndicador) -> NarrativaEixo:
    situacao_texto = _STATUS_TEXTO[eixo_indicador.status]
    analise = (
        f"{eixo_indicador.label} está com situação {situacao_texto}: {eixo_indicador.valor} "
        f"({eixo_indicador.subtexto}). Diagnóstico narrativo por IA indisponível no momento — "
        "exibindo apenas os dados já calculados do Censo Escolar."
    )
    return NarrativaEixo(
        eixo=eixo_romano,
        situacao=f"Situação {situacao_texto}",
        analise=analise,
        alerta_legal=None,
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


def _montar_contexto_diagnostico(codigo_ibge: int, indice: int, eixo_romano: str, municipio) -> dict:
    """Contexto enviado à IA para escrever a narrativa de um eixo: só agregados públicos (RN-04)."""
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


async def _gerar_eixo(codigo_ibge: int, indice: int, eixo_romano: str, municipio) -> NarrativaEixo:
    chave = calcular_chave(codigo_ibge, eixo_romano)
    guardada = obter_do_cache(chave)
    if guardada is not None:
        return guardada

    try:
        resposta_ia, modelo = await gerar_narrativa(_montar_contexto_diagnostico(codigo_ibge, indice, eixo_romano, municipio))
    except Exception as exc:  # noqa: BLE001 — qualquer falha aqui vira o texto de reserva com dados brutos
        logger.warning("IA indisponível para município %s eixo %s: %s", codigo_ibge, eixo_romano, descrever_falha(exc))
        _falhou_em[codigo_ibge] = time.monotonic()
        return _fallback_dados_brutos(eixo_romano, municipio.eixos[indice])

    narrativa = NarrativaEixo(
        eixo=eixo_romano, situacao=resposta_ia.situacao, analise=resposta_ia.analise, alerta_legal=resposta_ia.alerta_legal,
        referencia_municipio=resposta_ia.referencia_municipio, modelo_usado=modelo, gerado_em=datetime.now(timezone.utc).isoformat(),
    )
    salvar_no_cache(chave, codigo_ibge, narrativa)
    return narrativa


def guardada(codigo_ibge: int) -> Optional[NarrativaMunicipio]:
    """A narrativa completa já guardada para a edição atual, sem chamar a IA."""
    eixos = [obter_do_cache(calcular_chave(codigo_ibge, eixo)) for eixo in EIXOS_ROMANOS]
    if any(e is None for e in eixos):
        return None
    return NarrativaMunicipio(codigo_ibge=codigo_ibge, censo_versao=CENSO_VERSAO, eixos=eixos)


async def obter_narrativa_municipio(codigo_ibge: int) -> Optional[NarrativaMunicipio]:
    """Narrativa guardada; se faltar algum eixo, gera só os que faltam, um pedido por município de cada vez.

    Depois de uma falha da IA, por ESPERA_APOS_FALHA o município recebe o texto de reserva sem nova tentativa,
    para visitantes não repetirem chamadas a um provedor fora do ar.
    """
    municipio = obter_municipio_detalhe(codigo_ibge)
    if municipio is None:
        return None
    async with _travas[codigo_ibge]:
        pronta = guardada(codigo_ibge)
        if pronta is not None:
            return pronta
        if time.monotonic() - _falhou_em.get(codigo_ibge, -ESPERA_APOS_FALHA) < ESPERA_APOS_FALHA:
            eixos = [
                obter_do_cache(calcular_chave(codigo_ibge, eixo)) or _fallback_dados_brutos(eixo, municipio.eixos[i])
                for i, eixo in enumerate(EIXOS_ROMANOS)
            ]
        else:
            eixos = list(await asyncio.gather(*(
                _gerar_eixo(codigo_ibge, indice, eixo, municipio) for indice, eixo in enumerate(EIXOS_ROMANOS)
            )))
    return NarrativaMunicipio(codigo_ibge=codigo_ibge, censo_versao=CENSO_VERSAO, eixos=eixos)
