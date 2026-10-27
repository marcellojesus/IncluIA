"""Spec: docs/sdd/fase-2/requirements/secretario/analitico-barreiras.md (SAB-RF-01 a 06) e regras.

O município vem do vínculo do secretário (RN-SAB-01). As contagens são recalculadas a cada abertura;
só a síntese da IA é guardada, e é gerada quando o secretário pede.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.features.acesso.dependencias import SessaoGestao, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao
from app.features.analitico import base as base_rede
from app.features.analitico import sintese as sintese_ia
from app.features.analitico.modelos import SinteseAnalitica
from app.features.analitico.schemas import Achado, Analitico, BarreiraAnalitica, Evidencia, EvidenciaDoAchado, Sintese
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel
from app.shared.guardiao_lgpd import GuardiaoIndisponivel

router = APIRouter(prefix="/gestao/secretario/analitico", tags=["gestao-secretario"], dependencies=[Depends(exigir_configuracao)])

AVISO_GUARDIAO = "Trechos dos relatos ou da síntese com dados pessoais foram trocados por marcadores como [NOME]."


def _sintese(registro: SinteseAnalitica | None, rede: base_rede.Rede) -> Sintese | None:
    if registro is None:
        return None
    conteudo = registro.conteudo
    return Sintese(
        gerada_em=sintese_ia._com_fuso(registro.gerada_em), modelo=registro.modelo, desatualizada=registro.assinatura != rede.assinatura,
        limitacoes=conteudo.get("limitacoes", []), relatos_fora=conteudo.get("fora", 0),
        achados=[
            Achado(
                tipo=a["tipo"], texto=a["texto"], barreiras=a["barreiras"],
                evidencias=[
                    # Escola que saiu da rede desde a síntese não volta a aparecer.
                    EvidenciaDoAchado(co_entidade=e["co_entidade"], escola=rede.escolas[e["co_entidade"]], codigo=e["codigo"])
                    for e in a["evidencias"] if e["co_entidade"] in rede.escolas
                ],
            )
            for a in conteudo.get("achados", [])
        ],
    )


def _resposta(sessao: Session, co_municipio: int, aviso: str | None = None) -> Analitico:
    rede = base_rede.montar(sessao, co_municipio)
    total = len(rede.escolas)
    barreiras = [
        BarreiraAnalitica(
            codigo=b.codigo, eixo=b.eixo, eixo_nome=b.eixo_nome, nome=b.nome, nota=b.nota, escolas=len(b.escolas), alunos=b.alunos,
            alta_recorrencia=total > 0 and len(b.escolas) / total >= base_rede.ALTA_RECORRENCIA, com_declaracao=b.com_declaracao,
            obstaculos=b.contar("obstaculo"), divergencias=b.contar("divergencia"), sem_relato=b.contar("sem_relato"),
            com_acao=b.com_acao, com_acao_aceita=b.com_acao_aceita,
            evidencias=[Evidencia(**e.__dict__) for e in b.evidencias],
        )
        for b in rede.barreiras
    ]
    return Analitico(
        municipio=rede.municipio, uf=rede.uf, censo_versao=rede.censo_versao, escolas_municipais=total, alunos=rede.alunos,
        com_declaracao=rede.com_declaracao, com_plano=rede.com_plano, alta_recorrencia=sum(b.alta_recorrencia for b in barreiras),
        barreiras=barreiras, sintese=_sintese(sintese_ia.ultima(sessao, co_municipio), rede), aviso_guardiao=aviso,
    )


@router.get("", response_model=Analitico)
def analitico(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> Analitico:
    try:
        return _resposta(sessao, sessao_gestao.co_municipio)
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None


@router.post("/sintese", response_model=Analitico)
async def gerar_sintese(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> Analitico:
    try:
        _, mascarou = await sintese_ia.gerar(sessao, co_municipio=sessao_gestao.co_municipio, secretario_id=sessao_gestao.conta.id)
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "A verificação de dados pessoais está indisponível. Tente novamente em instantes.") from None
    except sintese_ia.ContextoBloqueado:
        raise HTTPException(
            409, "Os relatos da rede, juntos, têm dado pessoal sensível e não foram ao assistente. Os números continuam disponíveis."
        ) from None
    except RuntimeError:
        raise HTTPException(503, "O assistente não respondeu agora. Os números da rede continuam disponíveis; tente de novo em instantes.") from None
    return _resposta(sessao, sessao_gestao.co_municipio, AVISO_GUARDIAO if mascarou else None)
