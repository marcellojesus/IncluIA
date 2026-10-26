"""Avalia a busca normativa e, opcionalmente, as respostas da IA com o conjunto de avaliacao.json (AD-08).

Uso (a partir de backend/, com o .venv ativo e as chaves no .env):
    python -m etl.base_normativa.avaliar                    # busca: palavra-chave, vetor e híbrida
    python -m etl.base_normativa.avaliar --com-ia           # também gera e valida as respostas da IA
    python -m etl.base_normativa.avaliar --meta 0.9         # falha se o acerto entre os 3 primeiros < 90%
    python -m etl.base_normativa.avaliar --saida rel.json   # grava o relatório em JSON

As perguntas passam pelo Guardião LGPD antes de qualquer chamada, como em produção. Rodar a cada
nova versão da base, mudança de corpus, de modelo de embedding ou de provedor de IA.
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from etl.base_normativa.construir import PASTA

AVALIACAO = PASTA / "avaliacao.json"
ESCOLA_REFERENCIA = 11050098  # escola usada para montar o contexto nas respostas da IA (--com-ia)
_TOPO = 5


@dataclass
class ResultadoPergunta:
    pergunta: str
    esperado: str
    posicao: dict[str, int | None] = field(default_factory=dict)
    """Modo de busca → posição do trecho esperado (1 = primeiro); None se fora dos 20 candidatos."""
    ia: dict | None = None


def _posicao(ids, esperado: str) -> int | None:
    ids = list(ids)
    return ids.index(esperado) + 1 if esperado in ids else None


def _metricas(resultados: list[ResultadoPergunta], modo: str) -> dict[str, float]:
    posicoes = [r.posicao.get(modo) for r in resultados if modo in r.posicao]
    if not posicoes:
        return {}
    n = len(posicoes)
    return {
        "acerto@1": sum(p == 1 for p in posicoes) / n,
        "acerto@3": sum(p is not None and p <= 3 for p in posicoes) / n,
        "acerto@5": sum(p is not None and p <= 5 for p in posicoes) / n,
        "mrr": sum(1 / p for p in posicoes if p) / n,
    }


async def _avaliar_busca(base, pergunta_protegida, esperado: str, resultado: ResultadoPergunta) -> None:
    from app.shared import ai_client
    from app.shared.contexto_ia.busca import _CANDIDATOS, PESO_PALAVRA_CHAVE, consulta_fts, fundir

    expressao = consulta_fts(str(pergunta_protegida))
    por_palavra = base.buscar_palavra_chave(expressao, _CANDIDATOS) if expressao else []
    resultado.posicao["palavra_chave"] = _posicao(por_palavra, esperado)
    if base.matriz is None or base.meta.get("embeddings_modelo") != ai_client.MODELO_EMBEDDING:
        return
    try:
        vetor = await ai_client.gerar_embedding_consulta(pergunta_protegida)
    except RuntimeError:
        return
    por_vetor = base.buscar_vetor(vetor, _CANDIDATOS)
    resultado.posicao["vetor"] = _posicao(por_vetor, esperado)
    resultado.posicao["hibrida"] = _posicao(fundir(por_palavra, por_vetor, pesos=(PESO_PALAVRA_CHAVE, 1.0)), esperado)


async def _avaliar_ia(base, pergunta_protegida, esperado: str) -> dict:
    from app.shared.contexto_ia import (
        FORMATO_RESPOSTA_FUNDAMENTADA,
        INSTRUCOES_CITACAO,
        CitacaoInvalida,
        RespostaFundamentada,
        gerar_resposta_fundamentada,
        validar_citacoes,
    )
    from app.shared.contexto_ia.montador import montar_contexto
    from app.shared.guardiao_lgpd import juntar_protegidos, liberar_dados_publicos

    contexto = await montar_contexto(ESCOLA_REFERENCIA, pergunta=pergunta_protegida, base=base)
    sistema = juntar_protegidos([
        liberar_dados_publicos(FORMATO_RESPOSTA_FUNDAMENTADA),
        liberar_dados_publicos(INSTRUCOES_CITACAO),
        contexto.texto,
    ])
    saida = {"esperado_no_contexto": esperado in contexto.ids_citaveis}
    try:
        resposta, modelo = await gerar_resposta_fundamentada(
            sistema, [{"role": "user", "content": pergunta_protegida}], RespostaFundamentada, contexto
        )
    except (RuntimeError, CitacaoInvalida):
        return {**saida, "valida": False}
    # Os identificadores normalizados pelo validador (a IA às vezes devolve "[LBI-art28-XII]").
    citados = validar_citacoes(resposta, contexto).ids_usados
    return {**saida, "valida": True, "modelo": modelo, "citou_esperado": esperado in citados, "lacuna": bool(resposta.lacunas)}


async def avaliar(com_ia: bool, intervalo: float = 0.0) -> list[ResultadoPergunta]:
    from app.shared.contexto_ia import base_normativa
    from app.shared.guardiao_lgpd import proteger

    base = base_normativa.carregar()
    resultados = []
    for item in json.loads(AVALIACAO.read_text(encoding="utf-8"))["perguntas"]:
        protegida = proteger(item["pergunta"]).texto_protegido
        resultado = ResultadoPergunta(item["pergunta"], item["esperado"])
        if protegida is None:
            resultado.ia = {"erro": "pergunta bloqueada pelo Guardião LGPD"}
        else:
            await _avaliar_busca(base, protegida, item["esperado"], resultado)
            if com_ia:
                if resultados and intervalo:
                    await asyncio.sleep(intervalo)  # limite por minuto dos planos gratuitos
                resultado.ia = await _avaliar_ia(base, protegida, item["esperado"])
        resultados.append(resultado)
    return resultados


def _imprimir(resultados: list[ResultadoPergunta]) -> dict:
    modos = [m for m in ("palavra_chave", "vetor", "hibrida") if any(m in r.posicao for r in resultados)]
    print(f"{'pergunta':<62} {'esperado':<18} " + " ".join(f"{m:>13}" for m in modos))
    for r in resultados:
        posicoes = " ".join(f"{(r.posicao.get(m) or '-'):>13}" for m in modos)
        print(f"{r.pergunta[:60]:<62} {r.esperado:<18} {posicoes}")
    resumo = {m: _metricas(resultados, m) for m in modos}
    print()
    for modo, metricas in resumo.items():
        print(f"{modo:<14} " + "  ".join(f"{k} {v:.0%}" if k != "mrr" else f"{k} {v:.2f}" for k, v in metricas.items()))
    com_ia = [r.ia for r in resultados if r.ia and "valida" in r.ia]
    if com_ia:
        n = len(com_ia)
        resumo["ia"] = {
            "esperado_no_contexto": sum(i["esperado_no_contexto"] for i in com_ia) / n,
            "resposta_valida": sum(i["valida"] for i in com_ia) / n,
            "citou_esperado": sum(i.get("citou_esperado", False) for i in com_ia) / n,
        }
        print("IA            " + "  ".join(f"{k} {v:.0%}" for k, v in resumo["ia"].items()))
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--com-ia", action="store_true", help="gera e valida as respostas da IA (consome cota)")
    parser.add_argument("--meta", type=float, help="acerto mínimo entre os 3 primeiros no melhor modo (0 a 1)")
    parser.add_argument("--saida", type=Path, help="grava o relatório em JSON")
    parser.add_argument("--intervalo", type=float, default=15.0, help="segundos entre perguntas com --com-ia (padrão 15)")
    args = parser.parse_args()
    load_dotenv()

    resultados = asyncio.run(avaliar(args.com_ia, args.intervalo))
    resumo = _imprimir(resultados)
    if args.saida:
        args.saida.write_text(
            json.dumps({"resumo": resumo, "perguntas": [asdict(r) for r in resultados]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.meta is not None:
        melhor = max((m.get("acerto@3", 0) for k, m in resumo.items() if k != "ia"), default=0)
        if melhor < args.meta:
            print(f"\nAbaixo da meta: acerto@3 de {melhor:.0%} < {args.meta:.0%}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
