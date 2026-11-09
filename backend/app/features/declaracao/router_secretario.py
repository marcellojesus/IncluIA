"""Declarações emitidas pelas escolas da rede, vistas pelo secretário (RN-DO-07: a versão emitida é
visível ao secretário da rede; RN-SAB-04: escola sem declaração aparece como "sem registro
emitido", nunca como escola sem dificuldade).

O escopo vem do vínculo do secretário; rascunho de escola nunca aparece, só versões emitidas.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_connection
from app.features.acesso import censo, entrega_pdf
from app.features.acesso.dependencias import SessaoGestao, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao
from app.features.declaracao import documento
from app.features.declaracao.modelos import Declaracao
from app.features.declaracao.schemas import DeclaracaoDaEscola, DeclaracoesDaRede, ItemVersao, VersaoDeclaracao
from app.shared.banco_gestao import obter_sessao

router = APIRouter(prefix="/gestao/secretario/declaracoes", tags=["gestao-secretario"], dependencies=[Depends(exigir_configuracao)])


def _escolas_municipais(co_municipio: int) -> dict[int, str]:
    conn = get_connection()
    try:
        linhas = conn.execute(
            "SELECT co_entidade, no_entidade FROM escolas WHERE co_municipio = ? AND rede = ?", (co_municipio, censo.rede_da_gestao(co_municipio))
        ).fetchall()
    finally:
        conn.close()
    return {linha[0]: linha[1] for linha in linhas}


@router.get("", response_model=DeclaracoesDaRede)
def listar(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> DeclaracoesDaRede:
    co_municipio = sessao_gestao.co_municipio
    escolas = _escolas_municipais(co_municipio)
    ultimas: dict[int, Declaracao] = {}
    for declaracao in sessao.scalars(select(Declaracao).where(Declaracao.co_municipio == co_municipio).order_by(Declaracao.versao)):
        ultimas[declaracao.co_entidade] = declaracao
    municipio = censo.municipio(co_municipio)
    linhas = []
    for co_entidade, declaracao in ultimas.items():
        posicoes = [i.posicao for i in declaracao.itens]
        linhas.append(DeclaracaoDaEscola(
            co_entidade=co_entidade, escola=escolas.get(co_entidade, f"INEP {co_entidade}"), versao=declaracao.versao,
            emitida_em=declaracao.emitida_em, publicada_em=declaracao.publicada_em, retirada_em=declaracao.retirada_em, total=len(posicoes),
            obstaculos=posicoes.count("obstaculo"), divergencias=posicoes.count("divergencia"), sem_relato=posicoes.count("sem_relato"),
        ))
    linhas.sort(key=lambda l: l.emitida_em, reverse=True)
    return DeclaracoesDaRede(
        municipio=municipio.nome if municipio else "", uf=municipio.uf if municipio else "",
        escolas_municipais=len(escolas), com_declaracao=len(linhas), escolas=linhas,
    )


def _da_rede(sessao: Session, co_municipio: int, co_entidade: int, numero: int) -> Declaracao:
    declaracao = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade, Declaracao.versao == numero))
    # Escola de outra rede responde como inexistente (RN-07 do acesso).
    if declaracao is None or declaracao.co_municipio != co_municipio:
        raise HTTPException(404, "Declaração não encontrada.")
    return declaracao


@router.get("/{co_entidade}/versoes/{numero}", response_model=VersaoDeclaracao)
def ver_versao(
    co_entidade: int, numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> VersaoDeclaracao:
    declaracao = _da_rede(sessao, sessao_gestao.co_municipio, co_entidade, numero)
    escola = censo.escola(co_entidade)
    return VersaoDeclaracao(
        versao=declaracao.versao, escola=escola.nome if escola else f"INEP {co_entidade}", censo_versao=declaracao.censo_versao,
        metodologia_versao=declaracao.metodologia_versao, emitida_em=declaracao.emitida_em, publicada_em=declaracao.publicada_em,
        retirada_em=declaracao.retirada_em,
        itens=[
            ItemVersao(codigo=i.codigo, eixo=i.eixo, barreira=i.barreira, dado_censo=i.dado_censo, pontos=i.pontos,
                       posicao=i.posicao, texto=i.texto, resumo=i.resumo)
            for i in declaracao.itens
        ],
    )


@router.get("/{co_entidade}/versoes/{numero}/pdf", response_class=Response)
def baixar_pdf(
    co_entidade: int, numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> Response:
    """PDF-RF-01: o PDF da versão emitida, para o secretário da rede da escola (RN-PDF-02)."""
    declaracao = _da_rede(sessao, sessao_gestao.co_municipio, co_entidade, numero)
    return entrega_pdf.entregar(sessao, sessao_gestao, documento.documento(declaracao), declaracao.retirada_motivo)
