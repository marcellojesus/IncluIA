"""Spec: docs/sdd/fase-2/requirements/diretor/declaracao-obstaculos.md.

A escola é sempre a do vínculo aprovado (SessaoGestao); não há parâmetro de escola na URL.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.acesso.dependencias import SessaoGestao, exigir_admin, exigir_diretor
from app.features.acesso.protecao import exigir_configuracao
from app.features.declaracao import conversa as conversa_ia
from app.features.declaracao import publicacao, servico
from app.features.declaracao.modelos import Declaracao
from app.features.declaracao.schemas import (
    Aprovacao,
    BarreiraDeclaracao,
    EstadoDeclaracao,
    ItemVersao,
    MensagemConversa,
    NovaPosicao,
    PedidoConversa,
    PreviaPublica,
    Retirada,
    RespostaConversa,
    ResumoVersao,
    VersaoDeclaracao,
)
from app.features.declaracao.schemas import ItemPublico as ItemPublicoSchema
from app.features.declaracao.schemas import PontoDeAtencao as PontoSchema
from app.features.declaracao.router_publico import limpar_cache as limpar_cache_publico
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel
from app.shared.guardiao_lgpd import GuardiaoIndisponivel

router = APIRouter(prefix="/gestao/diretor/declaracao", tags=["gestao-declaracao"], dependencies=[Depends(exigir_configuracao)])


def _erro(funcao, *args, **kwargs):
    try:
        return funcao(*args, **kwargs)
    except servico.ErroDeclaracao as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None


def _estado(sessao: Session, co_entidade: int) -> EstadoDeclaracao:
    atual = _erro(servico.estado, sessao, co_entidade)
    escola = atual.escola.escola
    return EstadoDeclaracao(
        escola=escola["no_entidade"], co_entidade=co_entidade, censo_versao=escola["censo_versao"],
        metodologia_versao=atual.escola.metodologia_versao,
        barreiras=[
            BarreiraDeclaracao(
                codigo=i.barreira.codigo, eixo=i.barreira.eixo, nome=i.barreira.nome, dado_censo=i.barreira.texto,
                pontos=i.barreira.pontos, nota=i.barreira.nota, posicao=i.posicao, texto=i.texto, resumo=i.resumo,
                relato_original=i.relato_original, atualizado_em=i.atualizado_em, pergunta_inicial=conversa_ia.pergunta_inicial(i.barreira.codigo),
            )
            for i in atual.barreiras
        ],
        faltam=atual.faltam, ha_alteracoes=atual.ha_alteracoes, pode_emitir=atual.pode_emitir,
        versoes=[ResumoVersao(versao=v.versao, emitida_em=v.emitida_em, publicada_em=v.publicada_em, retirada_em=v.retirada_em) for v in atual.versoes],
    )


@router.get("", response_model=EstadoDeclaracao)
def obter(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoDeclaracao:
    return _estado(sessao, sessao_gestao.co_entidade)


@router.put("/barreiras/{codigo}", response_model=EstadoDeclaracao)
def registrar(
    codigo: str, corpo: NovaPosicao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> EstadoDeclaracao:
    _erro(
        servico.registrar_posicao, sessao, co_entidade=sessao_gestao.co_entidade, autor_id=sessao_gestao.conta.id,
        codigo=codigo, posicao=corpo.posicao, texto=corpo.texto, resumo=corpo.resumo,
    )
    return _estado(sessao, sessao_gestao.co_entidade)


@router.delete("/barreiras/{codigo}", response_model=EstadoDeclaracao)
def retificar(codigo: str, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoDeclaracao:
    _erro(servico.retificar_posicao, sessao, co_entidade=sessao_gestao.co_entidade, codigo=codigo)
    return _estado(sessao, sessao_gestao.co_entidade)


@router.post("/emitir", response_model=VersaoDeclaracao, status_code=201)
def emitir(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> VersaoDeclaracao:
    declaracao = _erro(servico.emitir, sessao, co_entidade=sessao_gestao.co_entidade, autor_id=sessao_gestao.conta.id)
    return _versao(sessao, declaracao)


@router.get("/versoes/{numero}", response_model=VersaoDeclaracao)
def obter_versao(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> VersaoDeclaracao:
    return _versao(sessao, _erro(servico.versao, sessao, sessao_gestao.co_entidade, numero))


def _versao(sessao: Session, declaracao) -> VersaoDeclaracao:
    escola = _erro(servico.escola_com_barreiras, declaracao.co_entidade).escola
    return VersaoDeclaracao(
        versao=declaracao.versao, escola=escola["no_entidade"], censo_versao=declaracao.censo_versao,
        metodologia_versao=declaracao.metodologia_versao, emitida_em=declaracao.emitida_em, publicada_em=declaracao.publicada_em,
        retirada_em=declaracao.retirada_em,
        itens=[
            ItemVersao(codigo=i.codigo, eixo=i.eixo, barreira=i.barreira, dado_censo=i.dado_censo, pontos=i.pontos,
                       posicao=i.posicao, texto=i.texto, resumo=i.resumo)
            for i in declaracao.itens
        ],
    )


# --- Conversa com a IA ---------------------------------------------------------------------------

@router.get("/barreiras/{codigo}/conversa", response_model=list[MensagemConversa])
def obter_conversa(codigo: str, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> list[MensagemConversa]:
    _erro(servico._barreira, _erro(servico.estado, sessao, sessao_gestao.co_entidade), codigo)
    return [MensagemConversa(papel=m.papel, texto=m.texto, criado_em=m.criado_em) for m in conversa_ia.mensagens(sessao, sessao_gestao.co_entidade, codigo)]


@router.post("/barreiras/{codigo}/conversa", response_model=RespostaConversa)
async def conversar(
    codigo: str, corpo: PedidoConversa, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> RespostaConversa:
    try:
        resposta = await conversa_ia.conversar(
            sessao, co_entidade=sessao_gestao.co_entidade, codigo=codigo, mensagem=corpo.mensagem, formalizar=corpo.formalizar
        )
    except servico.ErroDeclaracao as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except (RuntimeError, BaseNormativaIndisponivel):
        # GuardiaoIndisponivel também é RuntimeError: falha fechado, sem chamar a IA.
        raise HTTPException(503, "O assistente está indisponível agora. Você pode escrever o texto do obstáculo diretamente.") from None
    return RespostaConversa(resposta=resposta.resposta, texto_formal=resposta.texto_formal, resumo=resposta.resumo)


@router.delete("/barreiras/{codigo}/conversa", status_code=204)
def reiniciar_conversa(codigo: str, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> None:
    _erro(servico._barreira, _erro(servico.estado, sessao, sessao_gestao.co_entidade), codigo)
    conversa_ia.reiniciar(sessao, sessao_gestao.co_entidade, codigo)


# --- Publicação ----------------------------------------------------------------------------------

def _previa(sessao: Session, co_entidade: int, numero: int) -> PreviaPublica:
    declaracao, itens, pontos = _erro(publicacao.previa, sessao, co_entidade, numero)
    escola = _erro(servico.escola_com_barreiras, co_entidade).escola
    ultima = sessao.scalar(select(func.max(Declaracao.versao)).where(Declaracao.co_entidade == co_entidade))
    return PreviaPublica(
        versao=declaracao.versao, escola=escola["no_entidade"], emitida_em=declaracao.emitida_em, publicada_em=declaracao.publicada_em,
        retirada_em=declaracao.retirada_em,
        itens=[ItemPublicoSchema(**vars(i)) for i in itens],
        pontos=[PontoSchema(**vars(p)) for p in pontos],
        pode_publicar=declaracao.publicada_em is None and declaracao.retirada_em is None and declaracao.versao == ultima and not any(p.bloqueia for p in pontos),
    )


@router.get("/versoes/{numero}/publica", response_model=PreviaPublica)
def previa_publica(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> PreviaPublica:
    return _previa(sessao, sessao_gestao.co_entidade, numero)


@router.post("/versoes/{numero}/publicar", response_model=PreviaPublica)
def publicar(
    numero: int, corpo: Aprovacao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> PreviaPublica:
    _erro(publicacao.publicar, sessao, co_entidade=sessao_gestao.co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, aprovado=corpo.aprovado)
    limpar_cache_publico(sessao_gestao.co_entidade)
    return _previa(sessao, sessao_gestao.co_entidade, numero)


@router.post("/versoes/{numero}/retirar", response_model=PreviaPublica)
def retirar(
    numero: int, corpo: Retirada, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> PreviaPublica:
    _erro(publicacao.retirar, sessao, co_entidade=sessao_gestao.co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, motivo=corpo.motivo)
    limpar_cache_publico(sessao_gestao.co_entidade)
    return _previa(sessao, sessao_gestao.co_entidade, numero)


# Administração: retirada a pedido de titular (LGPD, art. 18) ou por dado pessoal publicado.
router_admin = APIRouter(prefix="/gestao/admin/declaracoes", tags=["gestao-admin"], dependencies=[Depends(exigir_configuracao)])


@router_admin.post("/{co_entidade}/versoes/{numero}/retirar", status_code=204)
def retirar_pela_administracao(
    co_entidade: int, numero: int, corpo: Retirada, sessao_gestao: SessaoGestao = Depends(exigir_admin), sessao: Session = Depends(obter_sessao)
) -> None:
    _erro(publicacao.retirar, sessao, co_entidade=co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, motivo=corpo.motivo)
    limpar_cache_publico(co_entidade)
