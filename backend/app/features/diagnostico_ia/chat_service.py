"""Spec: docs/business-rules/diagnostico-ia.md RN-09 — chat de ajuste de recomendações por eixo.

Reaproveita a mesma cadeia de fallback de IA (ai_client.py::gerar_resposta) e o mesmo diagnóstico
já calculado/cacheado (service.py::_obter_diagnostico_eixo) — o chat nunca gera um diagnóstico
paralelo, só conversa em cima do que já existe.
"""

import json
import logging
from datetime import datetime, timezone

from app.database import get_connection
from app.features.diagnostico_ia.ai_client import gerar_resposta
from app.features.diagnostico_ia.cache import calcular_chave, salvar_no_cache
from app.features.diagnostico_ia.prompts import SYSTEM_PROMPT
from app.features.diagnostico_ia.prompts_chat import (
    montar_mensagens_chat,
    montar_mensagens_reprocessamento,
    montar_system_prompt_chat,
)
from app.features.diagnostico_ia.schemas import DiagnosticoEixo, MensagemChat, RecomendacaoIA, RespostaChatIA, RespostaIA
from app.features.diagnostico_ia.service import EIXOS_ROMANOS, _montar_contexto_diagnostico, _obter_diagnostico_eixo
from app.features.indicadores_municipio.service import obter_municipio_detalhe

logger = logging.getLogger("diagnostico_ia")


def obter_historico(codigo_ibge: int, eixo: str) -> list[MensagemChat]:
    conn = get_connection()
    try:
        linhas = conn.execute(
            "SELECT papel, conteudo, criado_em FROM chat_diagnostico_mensagens "
            "WHERE codigo_ibge = ? AND eixo = ? ORDER BY id",
            (codigo_ibge, eixo),
        ).fetchall()
        return [
            MensagemChat(papel=linha["papel"], conteudo=linha["conteudo"], criado_em=linha["criado_em"])
            for linha in linhas
        ]
    finally:
        conn.close()


def _persistir_mensagem(codigo_ibge: int, eixo: str, papel: str, conteudo: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_diagnostico_mensagens (codigo_ibge, eixo, papel, conteudo, criado_em) "
            "VALUES (?, ?, ?, ?, ?)",
            (codigo_ibge, eixo, papel, conteudo, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _remover_ajuste(codigo_ibge: int, eixo: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM chat_diagnostico_recomendacoes_ajustadas WHERE codigo_ibge = ? AND eixo = ?",
            (codigo_ibge, eixo),
        )
        conn.commit()
    finally:
        conn.close()


def _salvar_ajuste(codigo_ibge: int, eixo: str, recomendacoes: list[RecomendacaoIA]) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO chat_diagnostico_recomendacoes_ajustadas "
            "(codigo_ibge, eixo, recomendacoes_json, ajustado_em) VALUES (?, ?, ?, ?)",
            (
                codigo_ibge,
                eixo,
                json.dumps([r.model_dump(mode="json") for r in recomendacoes]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


async def enviar_mensagem(codigo_ibge: int, eixo: str, mensagem_usuario: str) -> RespostaChatIA:
    """Levanta ValueError se o município não existir, RuntimeError se todos os provedores de IA
    falharem (o router converte ambos em respostas HTTP apropriadas)."""
    municipio = obter_municipio_detalhe(codigo_ibge)
    if municipio is None:
        raise ValueError(f"Município {codigo_ibge} não encontrado")

    indice = EIXOS_ROMANOS.index(eixo)
    diagnostico_atual = await _obter_diagnostico_eixo(codigo_ibge, indice, eixo, municipio, forcar=False)

    contexto_diagnostico = {
        "nome_municipio": municipio.nome,
        "uf": municipio.uf,
        "eixo_label": municipio.score_eixos[indice].label,
        "status": municipio.eixos[indice].status,
        "valor": municipio.eixos[indice].valor,
        "subtexto": municipio.eixos[indice].subtexto,
        "analise": diagnostico_atual.analise,
        "recomendacoes": [r.model_dump(mode="json") for r in diagnostico_atual.recomendacoes],
    }

    historico = obter_historico(codigo_ibge, eixo)
    historico_mensagens = [{"role": m.papel, "content": m.conteudo} for m in historico]

    # Persistida antes da chamada à IA: a mensagem do gestor fica registrada mesmo se a IA falhar.
    _persistir_mensagem(codigo_ibge, eixo, "user", mensagem_usuario)

    system_prompt = montar_system_prompt_chat(eixo, contexto_diagnostico)
    mensagens = montar_mensagens_chat(historico_mensagens, mensagem_usuario)
    resposta, _modelo = await gerar_resposta(system_prompt, mensagens, RespostaChatIA)

    _persistir_mensagem(codigo_ibge, eixo, "assistant", resposta.resposta)

    if resposta.recomendacoes_atualizadas:
        _salvar_ajuste(codigo_ibge, eixo, resposta.recomendacoes_atualizadas)

    return resposta


async def reprocessar_diagnostico(codigo_ibge: int, eixo: str) -> DiagnosticoEixo:
    """RN-10: ação explícita do gestor (botão) — gera uma versão final do diagnóstico completo
    (situação, análise, alerta legal e recomendações), considerando toda a conversa do chat até
    aqui, e a torna a versão oficial cacheada do eixo. Diferente do ajuste automático por mensagem
    (RN-09), que só troca a lista de recomendações: aqui o diagnóstico inteiro é reconsiderado."""
    municipio = obter_municipio_detalhe(codigo_ibge)
    if municipio is None:
        raise ValueError(f"Município {codigo_ibge} não encontrado")

    indice = EIXOS_ROMANOS.index(eixo)
    contexto = _montar_contexto_diagnostico(codigo_ibge, indice, eixo, municipio)
    historico = obter_historico(codigo_ibge, eixo)
    historico_mensagens = [{"role": m.papel, "content": m.conteudo} for m in historico]

    mensagens = montar_mensagens_reprocessamento(contexto, historico_mensagens)
    resposta_ia, modelo = await gerar_resposta(SYSTEM_PROMPT, mensagens, RespostaIA)

    agora = datetime.now(timezone.utc).isoformat()
    diagnostico = DiagnosticoEixo(
        eixo=eixo,
        situacao=resposta_ia.situacao,
        analise=resposta_ia.analise,
        alerta_legal=resposta_ia.alerta_legal,
        recomendacoes=resposta_ia.recomendacoes,
        referencia_municipio=resposta_ia.referencia_municipio,
        modelo_usado=modelo,
        gerado_em=agora,
        reprocessado_em=agora,
    )

    salvar_no_cache(calcular_chave(codigo_ibge, eixo), codigo_ibge, eixo, diagnostico)
    # A versão reprocessada já incorpora qualquer ajuste pontual anterior — evita que um ajuste
    # antigo (RN-09) sobreponha por engano o resultado fresco do reprocessamento.
    _remover_ajuste(codigo_ibge, eixo)

    _persistir_mensagem(codigo_ibge, eixo, "assistant", "✅ Diagnóstico reprocessado com base nesta conversa.")

    return diagnostico
