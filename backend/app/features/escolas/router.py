"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md"""

from fastapi import APIRouter, HTTPException

from app.features.escolas import service
from app.features.escolas.schemas import Escola

router = APIRouter(tags=["escolas"])


@router.get("/municipios/{codigo_ibge}/escolas", response_model=list[Escola])
def get_escolas_por_municipio(codigo_ibge: int) -> list[Escola]:
    return service.obter_escolas_por_municipio(codigo_ibge)


@router.get("/escolas/{co_entidade}", response_model=Escola)
def get_escola_detalhe(co_entidade: int) -> Escola:
    resultado = service.obter_escola_detalhe(co_entidade)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Escola {co_entidade} não encontrada")
    return resultado
