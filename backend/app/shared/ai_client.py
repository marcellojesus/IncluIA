"""Spec: docs/business-rules/diagnostico-ia.md RN-01 (ordem fixa de fallback) e RNF-01 (timeout);
docs/sdd/fase-2/arquitetura.md AD-05 e AD-08.

Chamadas REST diretas (sem SDK de cada provedor) — Groq e Mistral são compatíveis com o formato
`chat/completions` da OpenAI; Gemini usa `generateContent`. Cada provedor tem 8s de timeout;
qualquer falha (sem chave, timeout, erro HTTP, JSON inválido) cai para o próximo nível.

`gerar_resposta` é genérica (system prompt + lista de mensagens) e serve a todas as features que
usam IA, com a mesma cadeia de fallback. `gerar_embedding_consulta` gera o vetor da pergunta para a
busca na base normativa (AD-08).

AD-05: este é o ÚNICO módulo do backend que acessa provedores de IA, e as duas funções só aceitam
`TextoProtegido` — texto que passou pelo Guardião LGPD —, inclusive o system prompt. Logs de falha
usam `descrever_falha`, nunca o texto da exceção.
"""

import json
import logging
import os
from collections.abc import Callable
from typing import TypeVar

import httpx
import numpy as np
from pydantic import BaseModel, ValidationError

from app.shared.guardiao_lgpd import TextoProtegido

logger = logging.getLogger("ai_client")

TIMEOUT = httpx.Timeout(8.0)

# Modelos conferidos em 2026-10-23 (plano gratuito, JSON, resposta em menos de 8s). Os anteriores,
# gemini-2.0-flash e llama-3.3-70b-versatile, foram descontinuados pelos provedores e a cadeia
# rodava só no Mistral. Conferir de novo a cada etapa (risco "limites mudam sem aviso").
_MODELO_GEMINI = "gemini-3.5-flash"
_MODELO_GROQ = "openai/gpt-oss-120b"
_MODELO_MISTRAL = "mistral-small-latest"

_GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODELO_GEMINI}:generateContent"
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
            # Chave no cabeçalho, não na URL: a URL aparece em mensagens de erro e logs.
            headers={"x-goog-api-key": api_key},
            json={
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                # Raciocínio baixo: com o padrão, o modelo passa dos 8s de TIMEOUT no prompt real.
                "generationConfig": {"responseMimeType": "application/json", "thinkingConfig": {"thinkingLevel": "low"}},
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
    return await _chamar_openai_compativel(_GROQ_URL, api_key, _MODELO_GROQ, system_prompt, mensagens)


async def _chamar_mistral(system_prompt: str, mensagens: list[dict]) -> dict:
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY não configurada")
    return await _chamar_openai_compativel(_MISTRAL_URL, api_key, _MODELO_MISTRAL, system_prompt, mensagens)


_PROVEDORES = [
    (_MODELO_GEMINI, _chamar_gemini),
    (f"groq-{_MODELO_GROQ}", _chamar_groq),
    (_MODELO_MISTRAL, _chamar_mistral),
]


class RespostaReprovada(ValueError):
    """Resposta no formato certo, mas reprovada por uma validação (por exemplo, citação fora do
    contexto, AD-08). `resumo_seguro` é o único texto dela que pode ir para log: nunca trechos da
    resposta da IA, que podem ecoar algo que o guardião deixou passar."""

    def resumo_seguro(self) -> str:
        return type(self).__name__


def descrever_falha(exc: Exception) -> str:
    """Descrição de falha segura para log: nunca `str(exc)`, que pode trazer URL com chave de API,
    corpo da requisição ou a resposta da IA (ValidationError inclui o valor recebido)."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    if isinstance(exc, ValidationError):
        return f"resposta fora do formato ({exc.error_count()} erro(s) em {[e['loc'] for e in exc.errors()]})"
    if isinstance(exc, RespostaReprovada):
        return exc.resumo_seguro()
    return type(exc).__name__


async def gerar_resposta(
    system_prompt: TextoProtegido,
    mensagens: list[dict],
    schema_model: type[_ModeloResposta],
    validar: Callable[[_ModeloResposta], object] | None = None,
) -> tuple[_ModeloResposta, str]:
    """Tenta os provedores em ordem (RN-01); retorna (resposta, nome_do_modelo).
    Levanta RuntimeError se todos falharem — quem chama decide o fallback (RN-02 no diagnóstico
    automático; HTTP 503 no chat, ver chat_service.py). Levanta TypeError se alguma mensagem não
    tiver passado pelo Guardião LGPD (AD-05). `validar` roda depois do formato: se levantar
    exceção (por exemplo, citação fora do contexto, AD-08), a resposta é descartada e a cadeia
    segue para o próximo provedor.
    """
    if not isinstance(system_prompt, TextoProtegido) or not all(
        isinstance(m["content"], TextoProtegido) for m in mensagens
    ):
        raise TypeError("Texto para a IA sem passar pelo Guardião LGPD (AD-05)")
    mensagens_texto = [{"role": m["role"], "content": str(m["content"])} for m in mensagens]

    for nome_modelo, funcao in _PROVEDORES:
        try:
            bruto = await funcao(str(system_prompt), mensagens_texto)
            resposta = schema_model.model_validate(bruto)
            if validar is not None:
                validar(resposta)
            return resposta, nome_modelo
        except Exception as exc:  # noqa: BLE001 — qualquer falha aqui deve só acionar o próximo nível
            logger.warning("Falha no provedor %s: %s", nome_modelo, descrever_falha(exc))

    raise RuntimeError("Todos os provedores de IA falharam")


# Mesmo modelo e dimensão da base normativa (etl/base_normativa/embeddings.py). A busca confere o
# modelo gravado na tabela `meta` da base antes de comparar vetores.
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSAO_EMBEDDING = 768
_EMBEDDING_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_EMBEDDING}:embedContent"


async def _chamar_embedding(texto: str) -> list[float]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _EMBEDDING_URL,
            headers={"x-goog-api-key": api_key},
            json={
                "model": f"models/{MODELO_EMBEDDING}",
                "content": {"parts": [{"text": texto}]},
                "taskType": "RETRIEVAL_QUERY",
                "outputDimensionality": DIMENSAO_EMBEDDING,
            },
        )
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]


async def gerar_embedding_consulta(pergunta: TextoProtegido) -> np.ndarray:
    """Vetor normalizado da pergunta (AD-08). Levanta RuntimeError em qualquer falha; quem chama
    segue só com a busca por palavra-chave."""
    if not isinstance(pergunta, TextoProtegido):
        raise TypeError("Texto para a IA sem passar pelo Guardião LGPD (AD-05)")
    try:
        vetor = np.asarray(await _chamar_embedding(str(pergunta)), dtype=np.float32)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha no embedding da consulta: %s", descrever_falha(exc))
        raise RuntimeError("Embedding da consulta indisponível") from None
    return vetor / np.linalg.norm(vetor)
