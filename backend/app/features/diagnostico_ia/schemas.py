"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md"""

from typing import Literal, Optional

from app.shared.schemas import CamelModel


class RecomendacaoIA(CamelModel):
    acao: str
    custo_estimado: str
    prazo: str
    impacto_alunos: int
    fundamentacao: str


class DiagnosticoEixo(CamelModel):
    eixo: Literal["I", "II", "III", "IV"]
    situacao: str
    analise: str
    alerta_legal: Optional[str] = None
    recomendacoes: list[RecomendacaoIA]
    referencia_municipio: Optional[str] = None
    modelo_usado: str
    gerado_em: str
    # RN-09: preenchido quando a recomendação exibida foi ajustada via chat (não a gerada
    # automaticamente) — ver chat_service.py::_aplicar_ajuste.
    recomendacao_ajustada_em: Optional[str] = None
    # RN-10: preenchido quando este diagnóstico inteiro (não só a recomendação) foi reprocessado
    # considerando a conversa do chat — ver chat_service.py::reprocessar_diagnostico.
    reprocessado_em: Optional[str] = None


class RespostaIA(CamelModel):
    """Shape que pedimos à IA gerar (sem os campos de proveniência, que o service preenche)."""

    situacao: str
    analise: str
    alerta_legal: Optional[str] = None
    recomendacoes: list[RecomendacaoIA]
    referencia_municipio: Optional[str] = None


class MensagemChat(CamelModel):
    papel: Literal["user", "assistant"]
    conteudo: str
    criado_em: str


class RespostaChatIA(CamelModel):
    """Shape que pedimos à IA gerar no chat (RN-09) — texto livre + recomendação opcional."""

    resposta: str
    recomendacoes_atualizadas: Optional[list[RecomendacaoIA]] = None


class MensagemEntrada(CamelModel):
    mensagem: str
