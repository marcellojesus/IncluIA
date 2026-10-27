"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md

Narrativa pública do município: só leitura, sem login e sem chat (decisão de 2026-10-18, aplicada
em 2026-10-27). A narrativa guardada é servida a qualquer visitante; quando falta, quem a pede
passa pelo limite por IP de geração, e só um pedido por município chega à IA de cada vez.
"""

import threading
import time
from collections import deque

from fastapi import APIRouter, HTTPException, Request

from app.features.acesso.protecao import Limitador
from app.features.diagnostico_ia import service
from app.features.diagnostico_ia.schemas import NarrativaMunicipio

router = APIRouter(tags=["diagnostico-ia"])

limitar_geracao = Limitador(limite=10, janela_segundos=600)
"""Pedidos que disparam IA, por IP: impede varrer municípios para esgotar a cota gratuita."""

GERACOES_POR_DIA = 200
_geracoes: deque[float] = deque()
_trava = threading.Lock()


def _teto_global() -> None:
    """Teto diário de pedidos que disparam IA, somando todos os visitantes (revisão do AgLGPD de
    2026-10-27). Atrás do proxy do Render todos chegam com o mesmo IP, e o limite por IP sozinho não
    segura uma varredura. Em memória, por processo; com mais instâncias, cada uma tem o seu teto."""
    agora = time.monotonic()
    with _trava:
        while _geracoes and _geracoes[0] < agora - 86400:
            _geracoes.popleft()
        if len(_geracoes) >= GERACOES_POR_DIA:
            raise HTTPException(429, "A leitura deste município ainda não foi escrita. Tente de novo amanhã.")
        _geracoes.append(agora)


@router.get("/municipios/{codigo_ibge}/narrativa", response_model=NarrativaMunicipio)
async def narrativa(codigo_ibge: int, request: Request) -> NarrativaMunicipio:
    pronta = service.guardada(codigo_ibge)
    if pronta is not None:
        return pronta
    limitar_geracao(request)
    _teto_global()
    resultado = await service.obter_narrativa_municipio(codigo_ibge)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Município {codigo_ibge} não encontrado")
    return resultado
