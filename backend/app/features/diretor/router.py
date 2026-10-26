"""Spec: docs/sdd/fase-2/requirements/diretor/dashboard-situacao-escola.md.

A escola vem do vínculo aprovado (SessaoGestao), nunca da URL: não há como pedir outra escola
(DSE-RF-06, RN-07 do acesso).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.features.acesso.dependencias import SessaoGestao, exigir_diretor
from app.features.acesso.protecao import exigir_configuracao
from app.features.declaracao.servico import ErroDeclaracao
from app.features.diretor import servico
from app.features.diretor.schemas import DashboardEscola
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel

router = APIRouter(prefix="/gestao/diretor", tags=["gestao-diretor"], dependencies=[Depends(exigir_configuracao)])


@router.get("/escola", response_model=DashboardEscola)
def dashboard_da_escola(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> DashboardEscola:
    try:
        return servico.dashboard(sessao, sessao_gestao.co_entidade)
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None
    except ErroDeclaracao as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
