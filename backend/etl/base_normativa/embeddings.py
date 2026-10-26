"""Embeddings do corpus normativo, gerados offline pelo ETL (AD-08).

Roda fora do app e só recebe texto legal público do corpus validado — nunca texto de usuário. Por
isso chama o provedor direto, sem o Guardião LGPD; a consulta em tempo de execução (pergunta do
usuário) passa pelo `ai_client.py` com `TextoProtegido`, usando o MESMO modelo e dimensão gravados
na tabela `meta` da base.

Provedor inicial: Gemini (`gemini-embedding-001`, plano gratuito), reduzido a 768 dimensões e
normalizado. A escolha definitiva é a decisão pendente 7 da arquitetura.
"""

import os
import sys
import time

import httpx
import numpy as np

MODELO = "gemini-embedding-001"
DIMENSAO = 768
_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:batchEmbedContents"
# No plano gratuito cada item do lote conta no limite por minuto: lotes pequenos, e ao receber
# 429 espera e tenta de novo (o ETL é offline, a espera não afeta ninguém).
_LOTE = 20
_TENTATIVAS = 6
_ESPERA_PADRAO = 30.0
_TIMEOUT = httpx.Timeout(60.0)


class EmbeddingsIndisponiveis(RuntimeError):
    pass


def _espera_sugerida(resposta: httpx.Response) -> float:
    """Lê o retryDelay ("27s") que o Gemini devolve no 429; sem ele, espera o padrão."""
    try:
        for detalhe in resposta.json()["error"]["details"]:
            if "retryDelay" in detalhe:
                return float(detalhe["retryDelay"].rstrip("s")) + 1
    except (ValueError, KeyError, TypeError):
        pass
    return _ESPERA_PADRAO


def _enviar(cliente: httpx.Client, chave: str, corpo: dict) -> dict:
    for tentativa in range(_TENTATIVAS):
        try:
            resposta = cliente.post(_URL, headers={"x-goog-api-key": chave}, json=corpo)
        except httpx.HTTPError as exc:
            raise EmbeddingsIndisponiveis(type(exc).__name__) from None
        if resposta.status_code == 429 and tentativa < _TENTATIVAS - 1:
            espera = _espera_sugerida(resposta)
            print(f"     limite por minuto atingido; aguardando {espera:.0f}s…", file=sys.stderr)
            time.sleep(espera)
            continue
        if resposta.status_code != 200:
            raise EmbeddingsIndisponiveis(f"HTTP {resposta.status_code}")
        return resposta.json()
    raise EmbeddingsIndisponiveis("HTTP 429 persistente")


def gerar(textos: list[str]) -> np.ndarray:
    """Matriz (len(textos), DIMENSAO) em float32, cada linha com norma 1."""
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        raise EmbeddingsIndisponiveis("GEMINI_API_KEY não configurada")

    vetores = []
    with httpx.Client(timeout=_TIMEOUT) as cliente:
        for inicio in range(0, len(textos), _LOTE):
            lote = textos[inicio : inicio + _LOTE]
            corpo = {
                "requests": [
                    {
                        "model": f"models/{MODELO}",
                        "content": {"parts": [{"text": texto}]},
                        "taskType": "RETRIEVAL_DOCUMENT",
                        "outputDimensionality": DIMENSAO,
                    }
                    for texto in lote
                ]
            }
            vetores.extend(item["values"] for item in _enviar(cliente, chave, corpo)["embeddings"])

    matriz = np.asarray(vetores, dtype=np.float32)
    # Abaixo de 3072 dimensões o modelo não devolve vetores normalizados.
    return matriz / np.linalg.norm(matriz, axis=1, keepdims=True)
