"""Spec: docs/sdd/fase-2/requirements/secretario/dashboard-municipal.md.

O município vem do vínculo do secretário, nunca da URL (DMS-RF-08, RN-DMS-06).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.features.acesso.dependencias import SessaoGestao, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao
from app.features.dashboard_municipal import servico
from app.features.dashboard_municipal.schemas import DashboardMunicipal
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel

router = APIRouter(prefix="/gestao/secretario/dashboard", tags=["gestao-secretario"], dependencies=[Depends(exigir_configuracao)])


@router.get("", response_model=DashboardMunicipal)
def dashboard(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> DashboardMunicipal:
    try:
        return servico.montar(sessao, sessao_gestao.co_municipio)
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None
