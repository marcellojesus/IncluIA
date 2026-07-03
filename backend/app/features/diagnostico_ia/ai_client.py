"""Spec: docs/business-rules/diagnostico-ia.md RN-01 (ordem fixa de fallback) e RNF-01 (timeout).

Chamadas REST diretas (sem SDK de cada provedor) — Groq e Mistral são compatíveis com o formato
`chat/completions` da OpenAI; Gemini usa `generateContent`. Cada provedor tem 8s de timeout;
qualquer falha (sem chave, timeout, erro HTTP, JSON inválido) cai para o próximo nível.

`gerar_resposta` é genérica (system prompt + lista de mensagens) para servir tanto o diagnóstico
narrativo (`gerar_narrativa`, 1 mensagem) quanto o chat de ajuste por eixo (RN-09, várias
mensagens/histórico) — mesma cadeia de fallback para os dois, sem duplicar lógica.
"""

import json
import logging
import os
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.features.diagnostico_ia.prompts import SYSTEM_PROMPT, montar_prompt_usuario
from app.features.diagnostico_ia.schemas import RespostaIA

logger = logging.getLogger("diagnostico_ia")

TIMEOUT = httpx.Timeout(8.0)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

_ModeloResposta = TypeVar("_ModeloResposta", bound=BaseModel)


async def _chamar_gemini(system_prompt: str, mensagens: list[dict]) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada")

    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in mensagens
    ]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "generationConfig": {"responseMimeType": "application/json"},
            },
        )
        resp.raise_for_status()
        texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(texto)


async def _chamar_openai_compativel(
    url: str, api_key: str, modelo: str, system_prompt: str, mensagens: list[dict]
) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": modelo,
                "messages": [{"role": "system", "content": system_prompt}, *mensagens],
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        texto = resp.json()["choices"][0]["message"]["content"]
        return json.loads(texto)


async def _chamar_groq(system_prompt: str, mensagens: list[dict]) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada")
    return await _chamar_openai_compativel(_GROQ_URL, api_key, "llama-3.3-70b-versatile", system_prompt, mensagens)


async def _chamar_mistral(system_prompt: str, mensagens: list[dict]) -> dict:
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY não configurada")
    return await _chamar_openai_compativel(_MISTRAL_URL, api_key, "mistral-small-latest", system_prompt, mensagens)


_PROVEDORES = [
    ("gemini-2.0-flash", _chamar_gemini),
    ("groq-llama-3.3-70b", _chamar_groq),
    ("mistral-small", _chamar_mistral),
]


async def gerar_resposta(
    system_prompt: str, mensagens: list[dict], schema_model: type[_ModeloResposta]
) -> tuple[_ModeloResposta, str]:
    """Tenta os provedores em ordem (RN-01); retorna (resposta, nome_do_modelo).
    Levanta RuntimeError se todos falharem — quem chama decide o fallback (RN-02 no diagnóstico
    automático; HTTP 503 no chat, ver chat_service.py).
    """
    for nome_modelo, funcao in _PROVEDORES:
        try:
            bruto = await funcao(system_prompt, mensagens)
            resposta = schema_model.model_validate(bruto)
            return resposta, nome_modelo
        except Exception as exc:  # noqa: BLE001 — qualquer falha aqui deve só acionar o próximo nível
            logger.warning("Falha no provedor %s: %s", nome_modelo, exc)

    raise RuntimeError("Todos os provedores de IA falharam")


async def gerar_narrativa(contexto: dict) -> tuple[RespostaIA, str]:
    """Wrapper fino sobre `gerar_resposta` — mantém a assinatura/comportamento originais
    (1 prompt de usuário, sem histórico) usados pelo diagnóstico automático por eixo."""
    mensagens = [{"role": "user", "content": montar_prompt_usuario(contexto)}]
    return await gerar_resposta(SYSTEM_PROMPT, mensagens, RespostaIA)
