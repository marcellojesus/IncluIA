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
from app.features.diagnostico_ia.prompts import SYSTEM_PROMPT, montar_prompt_usuario
from app.features.diagnostico_ia.prompts_chat import (
    INSTRUCAO_REPROCESSAMENTO,
    montar_mensagens_chat,
    montar_mensagens_reprocessamento,
    montar_system_prompt_chat,
)
from app.features.diagnostico_ia.schemas import DiagnosticoEixo, MensagemChat, RecomendacaoIA, RespostaChatIA, RespostaIA
from app.features.diagnostico_ia.service import EIXOS_ROMANOS, _montar_contexto_diagnostico, _obter_diagnostico_eixo
from app.features.indicadores_municipio.service import obter_municipio_detalhe
from app.shared.guardiao_lgpd import liberar_dados_publicos, proteger, proteger_ou_falhar

logger = logging.getLogger("diagnostico_ia")

_MENSAGEM_REMOVIDA = "[mensagem anterior removida pelo Guardião LGPD]"
_TRECHO_REMOVIDO = "[trecho removido pelo Guardião LGPD]"
_MENSAGEM_REPROCESSADO = "✅ Diagnóstico reprocessado com base nesta conversa."


def _proteger_historico(historico: list[MensagemChat]) -> list[dict]:
    """AD-05: o histórico também vai à IA, então passa pelo guardião. Mensagens antigas gravadas
    antes do guardião podem ter dado de risco alto; essas saem do contexto em vez de travar o chat.
    A mensagem fixa do sistema não passa pelo reconhecimento de nomes (dava falso positivo)."""
    mensagens = []
    for m in historico:
        if m.conteudo == _MENSAGEM_REPROCESSADO:
            conteudo = liberar_dados_publicos(_MENSAGEM_REPROCESSADO)
        else:
            conteudo = proteger(m.conteudo).texto_protegido or liberar_dados_publicos(_MENSAGEM_REMOVIDA)
        mensagens.append({"role": m.papel, "content": conteudo})
    return mensagens


def _mascarar_texto_derivado(texto: str) -> str:
    """Análise e recomendações foram geradas pela IA, possivelmente a partir de conversas; podem
    ecoar algo que o guardião deixou passar. Vão mascaradas ao system prompt; bloqueadas, saem."""
    resultado = proteger(texto)
    return resultado.texto_mascarado if not resultado.bloqueado else _TRECHO_REMOVIDO


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
    """Levanta ValueError se o município não existir, TextoBloqueado se a mensagem tiver dado de
    risco alto (AD-05) e RuntimeError se o guardião ou todos os provedores de IA falharem (o router
    converte cada caso na resposta HTTP apropriada)."""
    municipio = obter_municipio_detalhe(codigo_ibge)
    if municipio is None:
        raise ValueError(f"Município {codigo_ibge} não encontrado")

    # Antes de qualquer outra coisa: mensagem bloqueada não é gravada nem enviada.
    mensagem_protegida = proteger_ou_falhar(mensagem_usuario)

    indice = EIXOS_ROMANOS.index(eixo)
    diagnostico_atual = await _obter_diagnostico_eixo(codigo_ibge, indice, eixo, municipio, forcar=False)

    contexto_diagnostico = {
        "nome_municipio": municipio.nome,
        "uf": municipio.uf,
        "eixo_label": municipio.score_eixos[indice].label,
        "status": municipio.eixos[indice].status,
        "valor": municipio.eixos[indice].valor,
        "subtexto": municipio.eixos[indice].subtexto,
        "analise": _mascarar_texto_derivado(diagnostico_atual.analise),
        "recomendacoes": _mascarar_texto_derivado(
            json.dumps([r.model_dump(mode="json") for r in diagnostico_atual.recomendacoes], ensure_ascii=False)
        ),
    }

    historico_mensagens = _proteger_historico(obter_historico(codigo_ibge, eixo))

    # Persistida antes da chamada à IA: a mensagem do gestor fica registrada mesmo se a IA falhar.
    # Grava a versão mascarada, não o texto original (minimização, AD-03).
    _persistir_mensagem(codigo_ibge, eixo, "user", str(mensagem_protegida))

    # Modelo fixo + dados públicos do município + análise e recomendações já mascaradas acima.
    system_prompt = liberar_dados_publicos(montar_system_prompt_chat(eixo, contexto_diagnostico))
    mensagens = montar_mensagens_chat(historico_mensagens, mensagem_protegida)
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
    historico_mensagens = _proteger_historico(obter_historico(codigo_ibge, eixo))

    mensagens = montar_mensagens_reprocessamento(
        liberar_dados_publicos(montar_prompt_usuario(contexto)),
        historico_mensagens,
        liberar_dados_publicos(INSTRUCAO_REPROCESSAMENTO),
    )
    resposta_ia, modelo = await gerar_resposta(liberar_dados_publicos(SYSTEM_PROMPT), mensagens, RespostaIA)

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

    _persistir_mensagem(codigo_ibge, eixo, "assistant", _MENSAGEM_REPROCESSADO)

    return diagnostico
