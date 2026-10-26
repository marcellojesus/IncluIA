"""Declaração publicada na página pública da escola (DO-RF-08; RN-DO-07).

Rota aberta, como o resto da Fase 1: mostra só a última versão publicada e não retirada, com número
e data, sem autoria, relato original nem rascunho. Proteções da revisão do AgLGPD:
- código INEP inexistente no Censo responde sem consultar o banco da Gestão Ativa;
- cache em memória de 60 s (inclusive "sem declaração"), limpo ao publicar ou retirar;
- limite por IP, `Cache-Control: no-store` (a retirada vale na hora, sem cópia em CDN) e
  `X-Robots-Tag: noindex` (buscadores não guardam cópia).
Se o banco da Gestão Ativa estiver indisponível, responde "sem declaração publicada": a página
pública da escola não pode cair por causa dele.
"""

import logging
import threading
import time

from fastapi import APIRouter, Depends, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.acesso.protecao import limitar_rota_publica
from app.features.declaracao import publicacao
from app.features.declaracao.modelos import Declaracao
from app.features.declaracao.schemas import DeclaracaoPublica, ItemPublico, PublicacaoDaEscola, PublicacoesDoMunicipio
from app.features.plano.schemas import PlanoPublico
from app.shared.banco_gestao import obter_sessao

router = APIRouter(tags=["declaracao-publica"])
logger = logging.getLogger("declaracao")

_VALIDADE_CACHE = 60.0
_cache: dict[int, tuple[float, DeclaracaoPublica | None]] = {}
_cache_municipios: dict[int, tuple[float, PublicacoesDoMunicipio]] = {}
_trava = threading.Lock()


def limpar_cache(co_entidade: int | None = None) -> None:
    with _trava:
        if co_entidade is None:
            _cache.clear()
        else:
            _cache.pop(co_entidade, None)
        _cache_municipios.clear()  # a lista do município muda junto com qualquer escola


def _montar(sessao: Session, co_entidade: int) -> DeclaracaoPublica | None:
    escola = censo.escola(co_entidade)
    if escola is None:
        return None  # INEP inexistente: nem consulta o banco da Gestão Ativa
    try:
        declaracao = publicacao.publicada(sessao, co_entidade)
    except SQLAlchemyError as erro:
        logger.warning("Declaração pública indisponível: %s", type(erro).__name__)
        return None
    if declaracao is None:
        return None
    return DeclaracaoPublica(
        co_entidade=co_entidade, escola=escola.nome, versao=declaracao.versao, emitida_em=declaracao.emitida_em,
        publicada_em=declaracao.publicada_em, censo_versao=declaracao.censo_versao, metodologia_versao=declaracao.metodologia_versao,
        itens=[
            ItemPublico(codigo=i.codigo, eixo=i.eixo, barreira=i.barreira, dado_censo=i.dado_censo, posicao=i.posicao, texto_publico=i.texto_publico or "")
            for i in declaracao.itens
        ],
        plano=_plano(sessao, co_entidade),
    )


def _plano(sessao: Session, co_entidade: int) -> PlanoPublico | None:
    """Plano de Ação aceito e publicado; falha no plano não derruba a Declaração pública."""
    from app.features.plano.router import plano_publico  # importação tardia: o plano depende da declaração

    try:
        return plano_publico(sessao, co_entidade)
    except (SQLAlchemyError, ValidationError) as erro:
        logger.warning("Plano público indisponível: %s", type(erro).__name__)
        return None


@router.get("/escolas/{co_entidade}/declaracao-publica", response_model=DeclaracaoPublica | None, dependencies=[Depends(limitar_rota_publica)])
def declaracao_publica(co_entidade: int, response: Response, sessao: Session = Depends(obter_sessao)) -> DeclaracaoPublica | None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    agora = time.monotonic()
    with _trava:
        guardado = _cache.get(co_entidade)
    if guardado and agora - guardado[0] < _VALIDADE_CACHE:
        return guardado[1]
    resultado = _montar(sessao, co_entidade)
    with _trava:
        _cache[co_entidade] = (agora, resultado)
    return resultado


def _publicacoes(sessao: Session, co_municipio: int) -> PublicacoesDoMunicipio:
    """Escolas do município com Declaração publicada e, entre elas, as com Plano de Ação publicado (o
    plano só conta junto com a Declaração publicada). Só números de versão: nada de texto ou autoria."""
    from app.features.plano.modelos import VersaoPlano  # importação tardia: o plano depende da declaração

    declaracoes: dict[int, int] = {}
    for d in sessao.scalars(
        select(Declaracao).where(Declaracao.co_municipio == co_municipio, Declaracao.publicada_em.is_not(None), Declaracao.retirada_em.is_(None))
    ):
        declaracoes[d.co_entidade] = max(d.versao, declaracoes.get(d.co_entidade, 0))
    planos: dict[int, int] = {}
    for v in sessao.scalars(
        select(VersaoPlano).where(VersaoPlano.co_municipio == co_municipio, VersaoPlano.publicada_em.is_not(None), VersaoPlano.retirada_em.is_(None))
    ):
        if v.co_entidade in declaracoes:
            planos[v.co_entidade] = max(v.versao, planos.get(v.co_entidade, 0))
    return PublicacoesDoMunicipio(
        escolas=[
            PublicacaoDaEscola(co_entidade=co, declaracao_versao=versao, plano_versao=planos.get(co))
            for co, versao in sorted(declaracoes.items())
        ]
    )


@router.get(
    "/municipios/{co_municipio}/publicacoes-gestao", response_model=PublicacoesDoMunicipio, dependencies=[Depends(limitar_rota_publica)]
)
def publicacoes_do_municipio(co_municipio: int, response: Response, sessao: Session = Depends(obter_sessao)) -> PublicacoesDoMunicipio:
    """Para a lista pública de escolas: quem publicou Declaração e Plano de Ação. Mesmas proteções da
    rota da escola (limite por IP, no-store, noindex, cache de 60 s limpo a cada publicação ou retirada)."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex"
    agora = time.monotonic()
    with _trava:
        guardado = _cache_municipios.get(co_municipio)
    if guardado and agora - guardado[0] < _VALIDADE_CACHE:
        return guardado[1]
    try:
        resultado = _publicacoes(sessao, co_municipio)
    except SQLAlchemyError as erro:
        logger.warning("Publicações do município indisponíveis: %s", type(erro).__name__)
        resultado = PublicacoesDoMunicipio(escolas=[])
    with _trava:
        _cache_municipios[co_municipio] = (agora, resultado)
    return resultado
