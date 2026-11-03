"""Spec: docs/sdd/fase-2/requirements/diretor/plano-acao-escolar.md.

A escola é sempre a do vínculo aprovado (SessaoGestao); não há parâmetro de escola na URL.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, object_session

from app.features.acesso import entrega_pdf
from app.features.acesso.dependencias import SessaoGestao, exigir_admin, exigir_diretor
from app.features.acesso.modelos import Conta
from app.features.acesso.protecao import exigir_configuracao
from app.features.declaracao.servico import escola_com_barreiras
from app.features.plano import documento, publicacao, servico, sugestoes
from app.features.plano.fontes import citacoes
from app.features.plano.schemas import (
    AceiteSugestao,
    AprovacaoPublicacao,
    ItemPlanoPublico,
    PlanoPublico,
    PontoPublicacaoPlano,
    PreviaPlanoPublico,
    RetiradaPlano,
    Apontamento,
    Acao,
    BarreiraBase,
    Confirmacao,
    EstadoPlano,
    ItemVersao,
    NovaAcao,
    PedidoAjuste,
    PedidoSugestoes,
    ResumoVersaoPlano,
    Sugestao,
    VersaoPlano,
)
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel
from app.shared.guardiao_lgpd import GuardiaoIndisponivel

router = APIRouter(prefix="/gestao/diretor/plano", tags=["gestao-plano"], dependencies=[Depends(exigir_configuracao)])


def _erro(funcao, *args, **kwargs):
    try:
        return funcao(*args, **kwargs)
    except servico.ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Base normativa indisponível no servidor.") from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None



def nome_de(sessao: Session | None, conta_id: str | None) -> str | None:
    conta = sessao.get(Conta, conta_id) if sessao and conta_id else None
    return conta.nome if conta else None


def resumo_versao(sessao: Session, v) -> ResumoVersaoPlano:
    return ResumoVersaoPlano(
        versao=v.versao, declaracao_versao=v.declaracao_versao, submetida_em=v.submetida_em, estado=v.estado,
        decidida_em=v.decidida_em, decidida_por=nome_de(sessao, v.decidida_por), comentario=v.comentario,
        publicada_em=v.publicada_em, retirada_em=v.retirada_em,
    )


AVISO_SUGESTAO ="Trechos da resposta do assistente com dados pessoais foram trocados por marcadores ou deixados em branco. Revise antes de incluir."


def _estado(sessao: Session, co_entidade: int, aviso: str | None = None) -> EstadoPlano:
    atual = _erro(servico.estado, sessao, co_entidade)
    escola = _erro(escola_com_barreiras, co_entidade).escola
    sugestoes_ = [Sugestao(id=s.id, codigo=s.codigo, **s.conteudo) for s in atual.sugestoes]
    acoes = [
        Acao(id=a.id, codigo=a.codigo, acao=a.acao, relacao=a.relacao, responsavel=a.responsavel, prazo=a.prazo, horizonte=a.horizonte,
             custo_estimado=a.custo_estimado, premissas=a.premissas, fontes=a.fontes or [], origem=a.origem, editada=a.editada)
        for a in atual.acoes
    ]
    usados = {f for s in sugestoes_ for f in s.fontes} | {f for a in acoes for f in a.fontes}
    motivo = atual.motivo_para_nao_submeter
    return EstadoPlano(
        escola=escola["no_entidade"], declaracao_base=atual.base.versao, ultima_declaracao=atual.ultima_declaracao,
        desatualizado=atual.desatualizado,
        barreiras=[BarreiraBase(codigo=i.codigo, eixo=i.eixo, barreira=i.barreira, posicao=i.posicao, texto=i.texto, resumo=i.resumo) for i in atual.base.itens],
        sugestoes=sugestoes_, acoes=acoes,
        versoes=[resumo_versao(sessao, v) for v in atual.versoes],
        pode_submeter=motivo is None, motivo=motivo, fontes=citacoes(usados), aviso_guardiao=aviso,
        apontamentos=apontamentos_da(atual.versoes[-1]) if atual.versoes and atual.versoes[-1].estado in ("ajustes_solicitados", "reprovado") else [],
    )


def _dados(corpo: NovaAcao) -> servico.DadosAcao:
    return servico.DadosAcao(
        codigo=corpo.codigo, acao=corpo.acao, relacao=corpo.relacao, responsavel=corpo.responsavel, prazo=corpo.prazo,
        horizonte=corpo.horizonte, custo_estimado=corpo.custo_estimado, premissas=corpo.premissas,
    )


@router.get("", response_model=EstadoPlano)
def obter(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    return _estado(sessao, sessao_gestao.co_entidade)


@router.post("/barreiras/{codigo}/sugestoes", response_model=EstadoPlano)
async def sugerir(
    codigo: str, corpo: PedidoSugestoes, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> EstadoPlano:
    try:
        _novas, alterou = await sugestoes.sugerir(sessao, co_entidade=sessao_gestao.co_entidade, codigo=codigo, orientacao=corpo.orientacao)
    except servico.ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
    except (RuntimeError, BaseNormativaIndisponivel):
        raise HTTPException(503, "O assistente está indisponível agora. Você pode escrever a ação diretamente.") from None
    return _estado(sessao, sessao_gestao.co_entidade, AVISO_SUGESTAO if alterou else None)


@router.post("/sugestoes/{sugestao_id}/aceitar", response_model=EstadoPlano)
def aceitar(
    sugestao_id: str, corpo: AceiteSugestao | None = None, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> EstadoPlano:
    """Sem edição, inclui a sugestão como veio; com edição, inclui já editada ("Editar e incluir")."""
    mascarou = _erro(
        servico.aceitar_sugestao, sessao, co_entidade=sessao_gestao.co_entidade, autor_id=sessao_gestao.conta.id,
        sugestao_id=sugestao_id, dados=_dados(corpo.edicao) if corpo and corpo.edicao else None,
    )
    return _estado(sessao, sessao_gestao.co_entidade, servico.AVISO_MASCARA if mascarou else None)


@router.post("/sugestoes/{sugestao_id}/ajustar", response_model=EstadoPlano)
async def ajustar(
    sugestao_id: str, corpo: PedidoAjuste, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> EstadoPlano:
    try:
        _nova, alterou = await sugestoes.ajustar(sessao, co_entidade=sessao_gestao.co_entidade, sugestao_id=sugestao_id, pedido=corpo.pedido)
    except servico.ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
    except (RuntimeError, BaseNormativaIndisponivel):
        raise HTTPException(503, "O assistente está indisponível agora. Você pode editar a sugestão diretamente.") from None
    return _estado(sessao, sessao_gestao.co_entidade, AVISO_SUGESTAO if alterou else None)


@router.post("/sugestoes/{sugestao_id}/descartar", response_model=EstadoPlano)
def descartar(sugestao_id: str, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    _erro(servico.descartar_sugestao, sessao, co_entidade=sessao_gestao.co_entidade, sugestao_id=sugestao_id)
    return _estado(sessao, sessao_gestao.co_entidade)


@router.post("/acoes", response_model=EstadoPlano, status_code=201)
def incluir(corpo: NovaAcao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    mascarou = _erro(servico.incluir_acao, sessao, co_entidade=sessao_gestao.co_entidade, autor_id=sessao_gestao.conta.id, dados=_dados(corpo))
    return _estado(sessao, sessao_gestao.co_entidade, servico.AVISO_MASCARA if mascarou else None)


@router.put("/acoes/{acao_id}", response_model=EstadoPlano)
def editar(acao_id: str, corpo: NovaAcao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    mascarou = _erro(servico.editar_acao, sessao, co_entidade=sessao_gestao.co_entidade, acao_id=acao_id, dados=_dados(corpo))
    return _estado(sessao, sessao_gestao.co_entidade, servico.AVISO_MASCARA if mascarou else None)


@router.delete("/acoes/{acao_id}", response_model=EstadoPlano)
def remover(acao_id: str, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    _erro(servico.remover_acao, sessao, co_entidade=sessao_gestao.co_entidade, acao_id=acao_id)
    return _estado(sessao, sessao_gestao.co_entidade)


@router.post("/atualizar-base", response_model=EstadoPlano)
def atualizar_base(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> EstadoPlano:
    _erro(servico.atualizar_base, sessao, sessao_gestao.co_entidade)
    return _estado(sessao, sessao_gestao.co_entidade)


@router.post("/submeter", response_model=VersaoPlano, status_code=201)
def submeter(corpo: Confirmacao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> VersaoPlano:
    versao = _erro(servico.submeter, sessao, co_entidade=sessao_gestao.co_entidade, autor_id=sessao_gestao.conta.id, confirmado=corpo.confirmado)
    return versao_para_resposta(versao)


@router.get("/versoes/{numero}", response_model=VersaoPlano)
def obter_versao(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> VersaoPlano:
    return versao_para_resposta(_erro(servico.versao_do_plano, sessao, sessao_gestao.co_entidade, numero))


@router.get("/versoes/{numero}/pdf", response_class=Response)
def baixar_pdf(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> Response:
    """PDF-RF-02: o PDF da versão enviada, com o mesmo acesso da tela da versão (RN-PDF-02)."""
    versao = _erro(servico.versao_do_plano, sessao, sessao_gestao.co_entidade, numero)
    return entrega_pdf.entregar(sessao, sessao_gestao, documento.documento(versao), versao.retirada_motivo)


def versao_para_resposta(versao) -> VersaoPlano:
    escola = _erro(escola_com_barreiras, versao.co_entidade).escola
    itens = [
        ItemVersao(id=i.id, codigo=i.codigo, barreira=i.barreira, acao=i.acao, relacao=i.relacao, responsavel=i.responsavel, prazo=i.prazo,
                   horizonte=i.horizonte, custo_estimado=i.custo_estimado, premissas=i.premissas, fontes=i.fontes or [],
                   origem=i.origem, editada=i.editada)
        for i in versao.itens
    ]
    return VersaoPlano(
        versao=versao.versao, escola=escola["no_entidade"], declaracao_versao=versao.declaracao_versao, submetida_em=versao.submetida_em,
        estado=versao.estado, decidida_em=versao.decidida_em, decidida_por=nome_de(object_session(versao), versao.decidida_por), comentario=versao.comentario, itens=itens,
        fontes=citacoes({f for i in itens for f in i.fontes}), apontamentos=apontamentos_da(versao),
    )


def apontamentos_da(versao) -> list[Apontamento]:
    """Pontos de ajuste da secretaria, com a ação do rascunho de origem de cada item apontado."""
    origem = {i.id: i.acao_id for i in versao.itens}
    return [Apontamento(codigo=a.codigo, item_id=a.item_id, acao_id=origem.get(a.item_id), texto=a.texto) for a in versao.apontamentos]


# --- Publicação do plano aceito ------------------------------------------------------------------

def _previa_publica(sessao: Session, co_entidade: int, numero: int) -> PreviaPlanoPublico:
    versao, itens, pontos, motivo = _erro(publicacao.previa, sessao, co_entidade, numero)
    escola = _erro(escola_com_barreiras, co_entidade).escola
    return PreviaPlanoPublico(
        versao=versao.versao, escola=escola["no_entidade"], aceito_em=versao.decidida_em, publicado_em=versao.publicada_em,
        retirado_em=versao.retirada_em, itens=[ItemPlanoPublico(**i) for i in itens],
        pontos=[PontoPublicacaoPlano(item=p.item, mensagem=p.mensagem, bloqueia=p.bloqueia) for p in pontos],
        pode_publicar=motivo is None, motivo=motivo,
    )


@router.get("/versoes/{numero}/publica", response_model=PreviaPlanoPublico)
def previa_publica(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> PreviaPlanoPublico:
    return _previa_publica(sessao, sessao_gestao.co_entidade, numero)


@router.post("/versoes/{numero}/publicar", response_model=PreviaPlanoPublico)
def publicar(
    numero: int, corpo: AprovacaoPublicacao, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> PreviaPlanoPublico:
    _erro(publicacao.publicar, sessao, co_entidade=sessao_gestao.co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, aprovado=corpo.aprovado)
    return _previa_publica(sessao, sessao_gestao.co_entidade, numero)


@router.post("/versoes/{numero}/retirar", response_model=PreviaPlanoPublico)
def retirar(
    numero: int, corpo: RetiradaPlano, sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)
) -> PreviaPlanoPublico:
    _erro(publicacao.retirar, sessao, co_entidade=sessao_gestao.co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, motivo=corpo.motivo)
    return _previa_publica(sessao, sessao_gestao.co_entidade, numero)


# Administração: retirada a pedido de titular (LGPD, art. 18) ou por dado pessoal publicado.
router_admin = APIRouter(prefix="/gestao/admin/planos", tags=["gestao-admin"], dependencies=[Depends(exigir_configuracao)])


@router_admin.post("/{co_entidade}/versoes/{numero}/retirar", status_code=204)
def retirar_pela_administracao(
    co_entidade: int, numero: int, corpo: RetiradaPlano, sessao_gestao: SessaoGestao = Depends(exigir_admin), sessao: Session = Depends(obter_sessao)
) -> None:
    _erro(publicacao.retirar, sessao, co_entidade=co_entidade, numero=numero, autor_id=sessao_gestao.conta.id, motivo=corpo.motivo)


def plano_publico(sessao: Session, co_entidade: int) -> PlanoPublico | None:
    """Para a página pública da escola (declaracao/router_publico.py)."""
    versao = publicacao.publicado(sessao, co_entidade)
    if versao is None:
        return None
    return PlanoPublico(
        versao=versao.versao, declaracao_versao=versao.declaracao_versao, aceito_em=versao.decidida_em, publicado_em=versao.publicada_em,
        itens=[ItemPlanoPublico(**i.publico) for i in versao.itens if i.publico],
    )
