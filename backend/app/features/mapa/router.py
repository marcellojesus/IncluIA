"""Spec: docs/requirements/mapa.md, docs/business-rules/mapa.md"""

from fastapi import APIRouter

from app.features.mapa import service
from app.features.mapa.schemas import KpisNacionais, MunicipioResumo, RankingUf, UfRanking

router = APIRouter(tags=["mapa"])


@router.get("/kpis-nacionais", response_model=KpisNacionais)
def get_kpis_nacionais() -> KpisNacionais:
    return service.obter_kpis_nacionais()


@router.get("/ranking-nacional", response_model=list[UfRanking])
def get_ranking_nacional() -> list[UfRanking]:
    return service.obter_ranking_nacional()


@router.get("/uf/{sigla}/municipios", response_model=list[MunicipioResumo])
def get_municipios_por_uf(sigla: str) -> list[MunicipioResumo]:
    return service.obter_municipios_por_uf(sigla)


@router.get("/uf/{sigla}/ranking", response_model=RankingUf)
def get_ranking_por_uf(sigla: str) -> RankingUf:
    return service.obter_ranking_por_uf(sigla)
