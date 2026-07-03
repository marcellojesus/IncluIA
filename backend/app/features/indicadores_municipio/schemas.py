"""Spec: docs/requirements/indicadores-municipio.md, docs/business-rules/indicadores-municipio.md"""

from typing import Literal

from app.shared.schemas import CamelModel


class EixoIndicador(CamelModel):
    status: Literal["ok", "warn", "nok"]
    icone: str
    label: str
    valor: str
    subtexto: str


class ScoreEixo(CamelModel):
    label: str
    percentual: float
    valor: str
    cor: str


class CriterioDecreto(CamelModel):
    eixo: str
    criterio: str
    variavel_censo: str
    resultado: str
    conformidade: Literal["conforme", "parcial", "nao_conforme"]


class MunicipioDetalhe(CamelModel):
    codigo_ibge: int
    nome: str
    uf: str
    score: float
    faixa: str
    cor: str
    eixos: list[EixoIndicador]
    score_eixos: list[ScoreEixo]
    dados_gerais: list[tuple[str, str]]
    detalhamento_decreto: list[CriterioDecreto]
