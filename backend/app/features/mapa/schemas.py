"""Spec: docs/requirements/mapa.md, docs/business-rules/mapa.md"""

from app.shared.schemas import CamelModel


class KpisNacionais(CamelModel):
    municipios_criticos: int
    escolas_sem_aee: int
    score_medio_nacional: float
    score_desejado: float
    municipios_mapeados: int
    total_alunos_esp: int


class MunicipioResumo(CamelModel):
    codigo_ibge: int
    nome: str
    uf: str
    score: float
    faixa: str
    cor: str


class MunicipioRanking(MunicipioResumo):
    ranking_no_estado: int
    qtd_municipios_no_estado: int


class RankingUf(CamelModel):
    melhores: list[MunicipioRanking]
    criticos: list[MunicipioRanking]
