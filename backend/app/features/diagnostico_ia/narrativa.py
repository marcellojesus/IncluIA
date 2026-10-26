"""Diagnóstico narrativo por eixo (Fase 1) sobre a cadeia de IA compartilhada (app/shared/ai_client.py)."""

from app.features.diagnostico_ia.prompts import SYSTEM_PROMPT, montar_prompt_usuario
from app.features.diagnostico_ia.schemas import RespostaIA
from app.shared.ai_client import gerar_resposta
from app.shared.guardiao_lgpd import liberar_dados_publicos


async def gerar_narrativa(contexto: dict) -> tuple[RespostaIA, str]:
    """1 prompt de usuário, sem histórico, usado pelo diagnóstico automático por eixo. O prompt é
    montado só com dados agregados públicos do município (RN-04), sem texto de usuário."""
    mensagens = [{"role": "user", "content": liberar_dados_publicos(montar_prompt_usuario(contexto))}]
    return await gerar_resposta(liberar_dados_publicos(SYSTEM_PROMPT), mensagens, RespostaIA)
