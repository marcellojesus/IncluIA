"""Spec: docs/requirements/diagnostico-ia.md, docs/business-rules/diagnostico-ia.md"""

from typing import Literal, Optional

from app.shared.schemas import CamelModel


class RespostaIA(CamelModel):
    """Shape que pedimos à IA gerar (sem os campos de proveniência, que o service preenche)."""

    situacao: str
    analise: str
    alerta_legal: Optional[str] = None
    referencia_municipio: Optional[str] = None


class NarrativaEixo(CamelModel):
    eixo: Literal["I", "II", "III", "IV"]
    situacao: str
    analise: str
    alerta_legal: Optional[str] = None
    referencia_municipio: Optional[str] = None
    modelo_usado: str
    """Modelo que escreveu o texto, ou "dados_brutos" quando nenhum provedor respondeu (RN-02)."""
    gerado_em: str


class NarrativaMunicipio(CamelModel):
    codigo_ibge: int
    censo_versao: str
    eixos: list[NarrativaEixo]
