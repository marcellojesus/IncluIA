"""Spec: docs/sdd/fase-2/requirements/secretario/fila-revisao-planos.md (SFR-RF-01 a 07).

O município vem do vínculo do secretário; escola de outra rede responde como inexistente. Só as
versões enviadas aparecem: rascunho, sugestões da IA e quem enviou ficam com a escola.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.acesso.dependencias import SessaoGestao, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao
from app.features.declaracao.modelos import Declaracao
from app.features.plano import revisao
from app.features.plano.router import resumo_versao, versao_para_resposta
from app.features.plano.schemas import BarreiraBase, Decisao, FilaPlanos, PlanoNaFila, RevisaoPlano
from app.features.plano.servico import ErroPlano
from app.shared.banco_gestao import obter_sessao
from app.shared.guardiao_lgpd import GuardiaoIndisponivel

router = APIRouter(prefix="/gestao/secretario/planos", tags=["gestao-secretario"], dependencies=[Depends(exigir_configuracao)])


AVISO_COMENTARIO = "Trechos do comentário com dados pessoais foram trocados por marcadores como [NOME]. Confira o texto registrado."


def _revisao(sessao: Session, co_municipio: int, co_entidade: int, numero: int, aviso: str | None = None) -> RevisaoPlano:
    versoes = revisao.versoes_da_escola(sessao, co_municipio, co_entidade)
    alvo = revisao.versao(versoes, numero)
    base = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade, Declaracao.versao == alvo.declaracao_versao))
    return RevisaoPlano(
        co_entidade=co_entidade, versao=versao_para_resposta(alvo),
        ultima_declaracao=revisao.ultima_declaracao(sessao, co_entidade), versao_atual=versoes[-1].versao,
        historico=[resumo_versao(sessao, v) for v in versoes], aviso_guardiao=aviso,
        barreiras=[
            BarreiraBase(codigo=i.codigo, eixo=i.eixo, barreira=i.barreira, posicao=i.posicao, texto=i.texto, resumo=i.resumo)
            for i in (base.itens if base else [])
        ],
    )


@router.get("", response_model=FilaPlanos)
def fila(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> FilaPlanos:
    co_municipio = sessao_gestao.co_municipio
    linhas = revisao.fila(sessao, co_municipio)
    escolas = censo.escolas({linha.co_entidade for linha in linhas})
    planos = []
    for linha in linhas:
        escola = escolas.get(linha.co_entidade)
        horizontes = [i.horizonte for i in linha.ultima.itens]
        planos.append(PlanoNaFila(
            co_entidade=linha.co_entidade, escola=escola.nome if escola else f"INEP {linha.co_entidade}", versao=linha.ultima.versao,
            estado=linha.ultima.estado, submetida_em=linha.ultima.submetida_em, decidida_em=linha.ultima.decidida_em,
            declaracao_versao=linha.ultima.declaracao_versao, ultima_declaracao=linha.ultima_declaracao, acoes=len(horizontes),
            loa=horizontes.count("LOA"), ppa=horizontes.count("PPA"), versoes=linha.versoes,
        ))
    municipio = censo.municipio(co_municipio)
    return FilaPlanos(municipio=municipio.nome if municipio else "", uf=municipio.uf if municipio else "", planos=planos)


@router.get("/{co_entidade}/versoes/{numero}", response_model=RevisaoPlano)
def ver(co_entidade: int, numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> RevisaoPlano:
    try:
        return _revisao(sessao, sessao_gestao.co_municipio, co_entidade, numero)
    except ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None


@router.post("/{co_entidade}/versoes/{numero}/decisao", response_model=RevisaoPlano)
def decidir(
    co_entidade: int, numero: int, corpo: Decisao, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> RevisaoPlano:
    try:
        mascarou = revisao.decidir(
            sessao, secretario_id=sessao_gestao.conta.id, co_municipio=sessao_gestao.co_municipio, co_entidade=co_entidade,
            numero=numero, decisao=corpo.decisao, comentario=corpo.comentario,
            marcacoes=[revisao.Marcacao(codigo=a.codigo, item_id=a.item_id, texto=a.texto) for a in corpo.apontamentos],
        )
        return _revisao(sessao, sessao_gestao.co_municipio, co_entidade, numero, AVISO_COMENTARIO if mascarou else None)
    except ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
