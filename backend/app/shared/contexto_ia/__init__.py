"""Contexto da IA em camadas (AD-08): fatos da escola, metodologia, base normativa e registros privados."""

from app.shared.contexto_ia.barreiras import BarreiraIdentificada, identificar
from app.shared.contexto_ia.base_normativa import BaseNormativaIndisponivel, TrechoNormativo
from app.shared.contexto_ia.montador import ContextoIA, EscolaNaoEncontrada, FatosDaRede, RegistroDaEscola, montar_contexto, montar_contexto_rede
from app.shared.contexto_ia.citacoes import (  # noqa: E402 — depende do montador
    FORMATO_RESPOSTA_FUNDAMENTADA,
    INSTRUCOES_CITACAO,
    CitacaoInvalida,
    Fundamento,
    RespostaFundamentada,
    gerar_resposta_fundamentada,
    validar_citacoes,
)

__all__ = [
    "FORMATO_RESPOSTA_FUNDAMENTADA",
    "INSTRUCOES_CITACAO",
    "RespostaFundamentada",
    "BarreiraIdentificada",
    "BaseNormativaIndisponivel",
    "CitacaoInvalida",
    "Fundamento",
    "gerar_resposta_fundamentada",
    "validar_citacoes",
    "ContextoIA",
    "EscolaNaoEncontrada",
    "RegistroDaEscola",
    "TrechoNormativo",
    "identificar",
    "montar_contexto",
    "montar_contexto_rede",
    "FatosDaRede",
]
