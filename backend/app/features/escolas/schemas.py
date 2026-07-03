"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md"""

from typing import Literal

from pydantic import Field

from app.shared.schemas import CamelModel

# "na" só é usado no Eixo IV, para escolas especiais exclusivas — RN-05 de
# docs/business-rules/escolas.md (taxa de inclusão em classe comum não se aplica a elas).
StatusEixo = Literal["ok", "warn", "nok", "na"]
Rede = Literal["Federal", "Estadual", "Municipal", "Privada"]


class Escola(CamelModel):
    co_entidade: int
    nome: str
    bairro: str
    rede: Rede
    alunos_esp: int
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
    ranking_municipal: int
    qtd_escolas_municipio: int
