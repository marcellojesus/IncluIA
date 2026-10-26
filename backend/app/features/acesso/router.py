"""Spec: docs/sdd/fase-2/requirements/acesso-gestao-ativa.md e business-rules/acesso-gestao-ativa.md.

Rotas sob /gestao, separadas do login da Fase 1 (RF-12).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.features.acesso import censo, servico
from app.features.acesso.dependencias import SessaoGestao, exigir_admin, exigir_qualquer_perfil, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao, limitar_por_ip
from app.features.acesso.schemas import (
    Decisao,
    Entrada,
    Escopo,
    Eu,
    Mensagem,
    NovoSecretario,
    PedidoCodigo,
    RespostaEntrada,
    SolicitacaoDiretor,
    SolicitacaoVinculo,
)
from app.shared.banco_gestao import obter_sessao
from app.shared.email import EnvioIndisponivel

router = APIRouter(prefix="/gestao", tags=["gestao-acesso"], dependencies=[Depends(exigir_configuracao)])
_anonima = [Depends(limitar_por_ip)]


def _executar(funcao, *args, **kwargs):
    try:
        return funcao(*args, **kwargs)
    except servico.ErroAcesso as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except EnvioIndisponivel:
        raise HTTPException(503, "Não foi possível enviar o código agora. Tente de novo em instantes.") from None


@router.post("/acesso/diretor", response_model=Mensagem, status_code=202, dependencies=_anonima)
def solicitar_acesso_diretor(corpo: SolicitacaoDiretor, sessao: Session = Depends(obter_sessao)) -> Mensagem:
    _executar(servico.solicitar_acesso_diretor, sessao, nome=corpo.nome, email=corpo.email, co_entidade=corpo.co_entidade)
    return Mensagem(mensagem=servico.MENSAGEM_CODIGO_ENVIADO)


@router.post("/acesso/codigo", response_model=Mensagem, status_code=202, dependencies=_anonima)
def pedir_codigo(corpo: PedidoCodigo, sessao: Session = Depends(obter_sessao)) -> Mensagem:
    _executar(servico.pedir_codigo_de_entrada, sessao, corpo.email)
    return Mensagem(mensagem=servico.MENSAGEM_CODIGO_ENVIADO)


@router.post("/acesso/entrar", response_model=RespostaEntrada, dependencies=_anonima)
def entrar(corpo: Entrada, sessao: Session = Depends(obter_sessao)) -> RespostaEntrada:
    resultado = _executar(servico.entrar, sessao, email=corpo.email, codigo=corpo.codigo)
    return RespostaEntrada(situacao=resultado.situacao, token=resultado.token, mensagem=resultado.mensagem)


@router.get("/eu", response_model=Eu)
def eu(sessao_gestao: SessaoGestao = Depends(exigir_qualquer_perfil)) -> Eu:
    conta = sessao_gestao.conta
    escopo = Escopo(co_entidade=sessao_gestao.co_entidade, co_municipio=sessao_gestao.co_municipio)
    if sessao_gestao.co_entidade and (escola := censo.escola(sessao_gestao.co_entidade)):
        escopo = Escopo(co_entidade=escola.co_entidade, escola=escola.nome, co_municipio=escola.co_municipio, municipio=escola.municipio, uf=escola.uf)
    elif sessao_gestao.co_municipio and (municipio := censo.municipio(sessao_gestao.co_municipio)):
        escopo = Escopo(co_municipio=municipio.co_municipio, municipio=municipio.nome, uf=municipio.uf)
    return Eu(id=conta.id, nome=conta.nome, email=conta.email, papel=conta.papel, escopo=escopo)


# --- Secretário ------------------------------------------------------------------------------

_ESTADOS_LISTA = {
    "pendentes": ("pendente",),
    "ativos": ("aprovado", "suspenso"),
    "encerrados": ("rejeitado", "revogado"),
}


@router.get("/secretario/vinculos", response_model=list[SolicitacaoVinculo])
def listar_vinculos(
    situacao: Literal["pendentes", "ativos", "encerrados"] = "pendentes",
    sessao_gestao: SessaoGestao = Depends(exigir_secretario),
    sessao: Session = Depends(obter_sessao),
) -> list[SolicitacaoVinculo]:
    vinculos = servico.solicitacoes_da_rede(sessao, sessao_gestao.co_municipio, _ESTADOS_LISTA[situacao])
    escolas = censo.escolas({v.co_entidade for v in vinculos if v.co_entidade})
    return [
        SolicitacaoVinculo(
            id=v.id, nome=v.conta.nome, email=v.conta.email, email_confirmado=v.conta.email_confirmado_em is not None,
            co_entidade=v.co_entidade, escola=escolas[v.co_entidade].nome if v.co_entidade in escolas else "",
            estado=v.estado, categoria=v.categoria, criado_em=v.criado_em, decidido_em=v.decidido_em,
            metodo_verificacao=v.metodo_verificacao, justificativa=v.justificativa,
        )
        for v in vinculos
    ]


@router.post("/secretario/vinculos/{vinculo_id}/{acao}", response_model=Mensagem)
def decidir(
    vinculo_id: str,
    acao: Literal["aprovar", "rejeitar", "suspender", "reativar", "revogar"],
    corpo: Decisao,
    sessao_gestao: SessaoGestao = Depends(exigir_secretario),
    sessao: Session = Depends(obter_sessao),
) -> Mensagem:
    vinculo = _executar(
        servico.decidir_vinculo, sessao, secretario=sessao_gestao.conta, co_municipio=sessao_gestao.co_municipio,
        vinculo_id=vinculo_id, acao=acao, categoria=corpo.categoria, texto=corpo.texto,
    )
    return Mensagem(mensagem=f"Vínculo {vinculo.estado}.")


# --- Administrador ---------------------------------------------------------------------------

@router.post("/admin/secretarios", response_model=Mensagem, status_code=201)
def provisionar_secretario(
    corpo: NovoSecretario, sessao_gestao: SessaoGestao = Depends(exigir_admin), sessao: Session = Depends(obter_sessao)
) -> Mensagem:
    _executar(
        servico.provisionar_secretario, sessao, admin=sessao_gestao.conta, nome=corpo.nome, email=corpo.email,
        co_municipio=corpo.co_municipio, categoria=corpo.categoria, metodo=corpo.metodo_verificacao,
    )
    return Mensagem(mensagem="Secretário provisionado. O acesso começa quando ele confirmar o e-mail com o código enviado.")
