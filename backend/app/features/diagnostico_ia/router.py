"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md

RN-06 de docs/business-rules/login.md: todas as rotas deste router exigem autenticação (única
feature paga/com custo real de IA do produto) — via dependência aplicada ao router inteiro, não
endpoint a endpoint, para não haver risco de esquecer uma rota nova sem proteção.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from app.features.diagnostico_ia import chat_service, service
from app.features.diagnostico_ia.schemas import DiagnosticoEixo, MensagemChat, MensagemEntrada, RespostaChatIA
from app.shared.auth import exigir_usuario_autenticado

router = APIRouter(tags=["diagnostico-ia"], dependencies=[Depends(exigir_usuario_autenticado)])

_Eixo = Literal["I", "II", "III", "IV"]


@router.post("/municipios/{codigo_ibge}/diagnostico", response_model=list[DiagnosticoEixo])
async def gerar_diagnostico(codigo_ibge: int, forcar: bool = False) -> list[DiagnosticoEixo]:
    resultado = await service.obter_diagnostico_municipio(codigo_ibge, forcar)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Município {codigo_ibge} não encontrado")
    return resultado


@router.get("/municipios/{codigo_ibge}/diagnostico/{eixo}/chat", response_model=list[MensagemChat])
async def obter_chat(codigo_ibge: int, eixo: _Eixo) -> list[MensagemChat]:
    return chat_service.obter_historico(codigo_ibge, eixo)


@router.post("/municipios/{codigo_ibge}/diagnostico/{eixo}/chat", response_model=RespostaChatIA)
async def enviar_chat(codigo_ibge: int, eixo: _Eixo, body: MensagemEntrada) -> RespostaChatIA:
    try:
        return await chat_service.enviar_mensagem(codigo_ibge, eixo, body.mensagem)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Município {codigo_ibge} não encontrado")
    except RuntimeError:
        raise HTTPException(
            status_code=503, detail="Não foi possível processar sua mensagem agora — tente novamente em instantes."
        )


@router.post("/municipios/{codigo_ibge}/diagnostico/{eixo}/reprocessar", response_model=DiagnosticoEixo)
async def reprocessar_diagnostico(codigo_ibge: int, eixo: _Eixo) -> DiagnosticoEixo:
    try:
        return await chat_service.reprocessar_diagnostico(codigo_ibge, eixo)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Município {codigo_ibge} não encontrado")
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível reprocessar o diagnóstico agora — tente novamente em instantes.",
        )
