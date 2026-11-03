"""Spec: docs/sdd/fase-2/requirements/secretario/plano-estrategico-municipal.md.

O município vem sempre do vínculo do secretário (sem parâmetro na URL); o diretor vê só as ações
municipais confirmadas que atendem a própria escola (RN-SPM-03).
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.features.acesso import censo, entrega_pdf
from app.features.acesso.dependencias import SessaoGestao, exigir_diretor, exigir_secretario
from app.features.acesso.protecao import exigir_configuracao
from app.features.plano.fontes import citacoes
from app.features.plano.router import nome_de
from app.features.plano.servico import AVISO_MASCARA, ErroPlano
from app.features.plano_municipal import base as base_rede
from app.features.plano_municipal import narrativa as narrativa_ia
from app.features.plano_municipal import documento, servico, sugestoes
from app.features.plano_municipal.schemas import (
    AceiteSugestaoMunicipal,
    AcaoMunicipal,
    AcaoMunicipalDaEscola,
    AcoesMunicipaisDaEscola,
    BarreiraDaRede,
    Confirmacao,
    EdicaoNarrativa,
    EscolaAtendida,
    EstadoPlanoMunicipal,
    ItemEscolarDaRede,
    NarrativaExecutiva,
    NovaAcaoMunicipal,
    NumerosDoPlano,
    PedidoSugestoesMunicipais,
    ResumoVersaoMunicipal,
    SugestaoMunicipal,
    VersaoPlanoMunicipal,
)
from app.shared.banco_gestao import obter_sessao
from app.shared.contexto_ia import BaseNormativaIndisponivel
from app.shared.guardiao_lgpd import GuardiaoIndisponivel

router = APIRouter(prefix="/gestao/secretario/plano-municipal", tags=["gestao-plano-municipal"], dependencies=[Depends(exigir_configuracao)])
router_diretor = APIRouter(prefix="/gestao/diretor/acoes-municipais", tags=["gestao-plano-municipal"], dependencies=[Depends(exigir_configuracao)])

AVISO_SUGESTAO = "Trechos da resposta do assistente com dados pessoais foram trocados por marcadores ou deixados em branco. Revise antes de incluir."


def _erro(funcao, *args, **kwargs):
    try:
        return funcao(*args, **kwargs)
    except ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Base normativa indisponível no servidor.") from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None


def _escolas(lista: list[dict], nomes: dict[int, str]) -> list[EscolaAtendida]:
    return [
        EscolaAtendida(co_entidade=e["co_entidade"], escola=nomes.get(e["co_entidade"], f"INEP {e['co_entidade']}"),
                       item_ids=e.get("item_ids") or [], cobertura=e.get("cobertura", "total"))
        for e in lista
    ]


def _acao(a: dict, nomes: dict[int, str]) -> AcaoMunicipal:
    return AcaoMunicipal(**{**a, "escolas": _escolas(a.get("escolas") or [], nomes)})


def _atendidas(acoes: list[dict]) -> int:
    return len({e["co_entidade"] for a in acoes for e in a.get("escolas") or []})


def _como_dict(a) -> dict:
    campos = ("id", *servico.CAMPOS_CONGELADOS)
    return {c: getattr(a, c) for c in campos}


def _estado(sessao: Session, co_municipio: int, aviso: str | None = None) -> EstadoPlanoMunicipal:
    atual = _erro(servico.estado, sessao, co_municipio)
    base = atual.base
    acoes = [_como_dict(a) for a in atual.acoes]
    sugestoes_ = [SugestaoMunicipal(id=s.id, codigo=s.codigo, **{**s.conteudo, "escolas": _escolas(s.conteudo.get("escolas") or [], base.escolas)})
                  for s in atual.sugestoes]
    usados = {f for s in sugestoes_ for f in s.fontes} | {f for a in acoes for f in a["fontes"] or []}
    return EstadoPlanoMunicipal(
        municipio=base.municipio, uf=base.uf, escolas_municipais=len(base.escolas), escolas_com_plano_aceito=len(base.planos),
        barreiras=[
            BarreiraDaRede(
                codigo=b.codigo, eixo=b.eixo, eixo_nome=b.eixo_nome, nome=b.nome, escolas_com_barreira=len(b.escolas_com_barreira),
                escolas_com_acao=len({i.co_entidade for i in b.itens}),
                itens=[ItemEscolarDaRede(ref=i.ref, co_entidade=i.co_entidade, escola=i.escola, item_id=i.item_id, acao=i.acao,
                                         responsavel=i.responsavel, prazo=i.prazo, horizonte=i.horizonte, custo_estimado=i.custo_estimado)
                       for i in b.itens],
            )
            for b in base.barreiras
        ],
        sugestoes=sugestoes_, acoes=[_acao(a, base.escolas) for a in acoes], escolas_atendidas=_atendidas(acoes),
        versoes=[
            ResumoVersaoMunicipal(versao=v.versao, confirmada_em=v.confirmada_em, confirmada_por=nome_de(sessao, v.confirmada_por),
                                  acoes=len(v.acoes), escolas_atendidas=_atendidas(v.acoes))
            for v in atual.versoes
        ],
        fontes=citacoes(usados), aviso_guardiao=aviso,
    )


def _dados(corpo: NovaAcaoMunicipal) -> servico.DadosAcaoMunicipal:
    return servico.DadosAcaoMunicipal(
        codigos=tuple(corpo.codigos), acao=corpo.acao, justificativa=corpo.justificativa, responsavel=corpo.responsavel, prazo=corpo.prazo,
        horizonte=corpo.horizonte, custo_estimado=corpo.custo_estimado, premissas=corpo.premissas, prioridade=corpo.prioridade,
        escolas=tuple(servico.EscolaAtendida(e.co_entidade, tuple(e.item_ids), e.cobertura) for e in corpo.escolas),
    )


@router.get("", response_model=EstadoPlanoMunicipal)
def obter(sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> EstadoPlanoMunicipal:
    return _estado(sessao, sessao_gestao.co_municipio)


@router.post("/barreiras/{codigo}/sugestoes", response_model=EstadoPlanoMunicipal)
async def sugerir(
    codigo: str, corpo: PedidoSugestoesMunicipais, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> EstadoPlanoMunicipal:
    try:
        _novas, alterou = await sugestoes.sugerir(sessao, co_municipio=sessao_gestao.co_municipio, codigo=codigo, orientacao=corpo.orientacao)
    except ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
    except (RuntimeError, BaseNormativaIndisponivel):
        raise HTTPException(503, "O assistente está indisponível agora. Você pode escrever a ação municipal diretamente.") from None
    return _estado(sessao, sessao_gestao.co_municipio, AVISO_SUGESTAO if alterou else None)


@router.post("/sugestoes/{sugestao_id}/aceitar", response_model=EstadoPlanoMunicipal)
def aceitar(
    sugestao_id: str, corpo: AceiteSugestaoMunicipal | None = None, sessao_gestao: SessaoGestao = Depends(exigir_secretario),
    sessao: Session = Depends(obter_sessao),
) -> EstadoPlanoMunicipal:
    mascarou = _erro(
        servico.aceitar_sugestao, sessao, co_municipio=sessao_gestao.co_municipio, autor_id=sessao_gestao.conta.id, sugestao_id=sugestao_id,
        dados=_dados(corpo.edicao) if corpo and corpo.edicao else None,
    )
    return _estado(sessao, sessao_gestao.co_municipio, AVISO_MASCARA if mascarou else None)


@router.post("/sugestoes/{sugestao_id}/descartar", response_model=EstadoPlanoMunicipal)
def descartar(sugestao_id: str, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> EstadoPlanoMunicipal:
    _erro(servico.descartar_sugestao, sessao, co_municipio=sessao_gestao.co_municipio, sugestao_id=sugestao_id)
    return _estado(sessao, sessao_gestao.co_municipio)


@router.post("/acoes", response_model=EstadoPlanoMunicipal, status_code=201)
def incluir(corpo: NovaAcaoMunicipal, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> EstadoPlanoMunicipal:
    mascarou = _erro(servico.incluir_acao, sessao, co_municipio=sessao_gestao.co_municipio, autor_id=sessao_gestao.conta.id, dados=_dados(corpo))
    return _estado(sessao, sessao_gestao.co_municipio, AVISO_MASCARA if mascarou else None)


@router.put("/acoes/{acao_id}", response_model=EstadoPlanoMunicipal)
def editar(
    acao_id: str, corpo: NovaAcaoMunicipal, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> EstadoPlanoMunicipal:
    mascarou = _erro(servico.editar_acao, sessao, co_municipio=sessao_gestao.co_municipio, acao_id=acao_id, dados=_dados(corpo))
    return _estado(sessao, sessao_gestao.co_municipio, AVISO_MASCARA if mascarou else None)


@router.delete("/acoes/{acao_id}", response_model=EstadoPlanoMunicipal)
def remover(acao_id: str, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> EstadoPlanoMunicipal:
    _erro(servico.remover_acao, sessao, co_municipio=sessao_gestao.co_municipio, acao_id=acao_id)
    return _estado(sessao, sessao_gestao.co_municipio)


@router.post("/confirmar", response_model=VersaoPlanoMunicipal, status_code=201)
def confirmar(corpo: Confirmacao, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> VersaoPlanoMunicipal:
    versao = _erro(servico.confirmar, sessao, co_municipio=sessao_gestao.co_municipio, autor_id=sessao_gestao.conta.id, confirmado=corpo.confirmado)
    return _versao(sessao, versao)


@router.get("/versoes/{numero}", response_model=VersaoPlanoMunicipal)
def obter_versao(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> VersaoPlanoMunicipal:
    return _versao(sessao, _erro(servico.versao, sessao, sessao_gestao.co_municipio, numero))


@router.get("/versoes/{numero}/pdf", response_class=Response)
def baixar_pdf(numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)) -> Response:
    """PDF-RF-03: o PDF da versão confirmada, sem a narrativa executiva (RN-PDF-02)."""
    return entrega_pdf.entregar(sessao, sessao_gestao, documento.documento(_erro(servico.versao, sessao, sessao_gestao.co_municipio, numero)))


def _narrativa(registro) -> NarrativaExecutiva | None:
    if registro is None:
        return None
    return NarrativaExecutiva(
        **registro.conteudo, modelo=registro.modelo, gerada_em=narrativa_ia._com_fuso(registro.gerada_em), editada=registro.editada,
    )


def _versao(sessao: Session, versao, aviso: str | None = None) -> VersaoPlanoMunicipal:
    municipio = censo.municipio(versao.co_municipio)
    nomes = {co: e.nome for co, e in censo.escolas({e["co_entidade"] for a in versao.acoes for e in a.get("escolas") or []}).items()}
    narrativa = narrativa_ia.da_versao(sessao, versao.co_municipio, versao.versao)
    usados = {f for a in versao.acoes for f in a.get("fontes") or []} | set(narrativa.conteudo.get("fontes") or [] if narrativa else [])
    return VersaoPlanoMunicipal(
        versao=versao.versao, municipio=municipio.nome if municipio else "", confirmada_em=versao.confirmada_em,
        confirmada_por=nome_de(sessao, versao.confirmada_por), acoes=[_acao(a, nomes) for a in versao.acoes],
        escolas_atendidas=_atendidas(versao.acoes), fontes=citacoes(usados),
        numeros=NumerosDoPlano(**narrativa_ia.numeros(versao, len(base_rede._escolas_municipais(versao.co_municipio))).__dict__),
        narrativa=_narrativa(narrativa), aviso_guardiao=aviso,
    )


@router.post("/versoes/{numero}/narrativa", response_model=VersaoPlanoMunicipal)
async def gerar_narrativa(
    numero: int, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> VersaoPlanoMunicipal:
    """RF-30: narrativa executiva de uma versão confirmada; gerar de novo substitui o texto anterior."""
    versao = _erro(servico.versao, sessao, sessao_gestao.co_municipio, numero)
    try:
        _, mascarou = await narrativa_ia.gerar(sessao, versao=versao, autor_id=sessao_gestao.conta.id)
    except ErroPlano as erro:
        raise HTTPException(erro.status, erro.mensagem) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
    except (RuntimeError, BaseNormativaIndisponivel):
        raise HTTPException(503, "O assistente está indisponível agora. O plano e seus números continuam disponíveis; tente de novo em instantes.") from None
    return _versao(sessao, versao, AVISO_SUGESTAO if mascarou else None)


@router.put("/versoes/{numero}/narrativa", response_model=VersaoPlanoMunicipal)
def editar_narrativa(
    numero: int, corpo: EdicaoNarrativa, sessao_gestao: SessaoGestao = Depends(exigir_secretario), sessao: Session = Depends(obter_sessao)
) -> VersaoPlanoMunicipal:
    versao = _erro(servico.versao, sessao, sessao_gestao.co_municipio, numero)
    mascarou = _erro(narrativa_ia.editar, sessao, versao=versao, autor_id=sessao_gestao.conta.id, dados=narrativa_ia.EdicaoNarrativa(
        resumo=corpo.resumo, situacao=corpo.situacao, fundamentacao=corpo.fundamentacao, proximos_passos=corpo.proximos_passos,
        estrategia=tuple((b.texto, tuple(b.acoes)) for b in corpo.estrategia), incertezas=tuple(corpo.incertezas),
    ))
    return _versao(sessao, versao, AVISO_MASCARA if mascarou else None)


@router_diretor.get("", response_model=AcoesMunicipaisDaEscola)
def acoes_da_escola(sessao_gestao: SessaoGestao = Depends(exigir_diretor), sessao: Session = Depends(obter_sessao)) -> AcoesMunicipaisDaEscola:
    escola = censo.escola(sessao_gestao.co_entidade)
    if escola is None:
        return AcoesMunicipaisDaEscola()
    versao, acoes = servico.acoes_da_escola(sessao, escola.co_municipio, sessao_gestao.co_entidade)
    if versao is None:
        return AcoesMunicipaisDaEscola()
    return AcoesMunicipaisDaEscola(
        versao=versao.versao, confirmada_em=versao.confirmada_em,
        acoes=[
            AcaoMunicipalDaEscola(
                # Sem justificativa: ela é escrita a partir dos planos de todas as escolas da barreira, que são privados
                # de cada escola (RN-PAE-03), e pode citar outras escolas (RN-SPM-03; revisão do AgLGPD, 2026-10-26).
                acao=a["acao"], responsavel=a.get("responsavel"), prazo=a.get("prazo"),
                horizonte=a["horizonte"], prioridade=a["prioridade"], barreiras=a.get("codigos") or [],
                cobertura=next(e["cobertura"] for e in a["escolas"] if e["co_entidade"] == sessao_gestao.co_entidade),
                escolas_atendidas=len(a["escolas"]),
            )
            for a in acoes
        ],
    )
