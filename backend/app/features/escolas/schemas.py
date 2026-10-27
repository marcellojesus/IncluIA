"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md"""

from typing import Literal

from pydantic import Field

from app.shared.schemas import CamelModel

# "na" só é usado no Eixo IV, para escolas especiais exclusivas — RN-05 de
# docs/business-rules/escolas.md (taxa de inclusão em classe comum não se aplica a elas).
# "omitido" só ocorre no Eixo IV, em escola com dados protegidos (RN-06; ver service.py).
StatusEixo = Literal["ok", "warn", "nok", "na", "omitido"]
Rede = Literal["Federal", "Estadual", "Municipal", "Privada"]


class Escola(CamelModel):
    co_entidade: int
    nome: str
    bairro: str
    rede: Rede
    alunos_esp: int | None
    """None quando a escola tem de 1 a 4 matrículas da educação especial (RN-06)."""
    status_eixo_i: StatusEixo
    # O alias_generator padrão (CamelModel) faz str.title() em cada parte do snake_case —
    # "eixo_ii" vira "EixoIi", não "EixoII" (só a 1ª letra de cada palavra é maiúscula). Sem o
    # alias explícito abaixo, o frontend recebe "statusEixoIi" em vez de "statusEixoII" e o
    # campo chega como undefined lá (bug real já visto em produção: ícones somem sem erro).
    status_eixo_ii: StatusEixo = Field(alias="statusEixoII")
    status_eixo_iii: StatusEixo = Field(alias="statusEixoIII")
    status_eixo_iv: StatusEixo = Field(alias="statusEixoIV")
    score: float
    faixa: str
    cor: str
    especial_exclusiva: bool
    dados_protegidos: bool = False
    """Score público calculado com a taxa média de classe comum; ver service.py (RN-06)."""
    ranking_municipal: int
    qtd_escolas_municipio: int


class BarreiraPublica(CamelModel):
    codigo: str
    eixo: str
    nome: str
    dado_censo: str
    pontos: float | None
    """Pontos do score em jogo; None quando revelariam a contagem de célula pequena."""
    nota: str | None = None


class BarreirasDaEscola(CamelModel):
    """PUB-01 (impacto-fase-1.md): barreiras identificadas no Censo, com ou sem Declaração publicada."""

    co_entidade: int
    censo_versao: str
    metodologia_versao: str
    barreiras: list[BarreiraPublica]
