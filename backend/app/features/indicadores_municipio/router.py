"""Spec: docs/requirements/indicadores-municipio.md, docs/business-rules/indicadores-municipio.md"""

from fastapi import APIRouter, HTTPException

from app.features.indicadores_municipio import service
from app.features.indicadores_municipio.schemas import MunicipioDetalhe

router = APIRouter(tags=["indicadores-municipio"])


@router.get("/municipios/{codigo_ibge}", response_model=MunicipioDetalhe)
def get_municipio_detalhe(codigo_ibge: int) -> MunicipioDetalhe:
    resultado = service.obter_municipio_detalhe(codigo_ibge)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Município {codigo_ibge} não encontrado")
    return resultado
