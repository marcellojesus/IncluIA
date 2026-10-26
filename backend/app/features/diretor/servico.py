"""Spec: docs/sdd/fase-2/requirements/diretor/dashboard-situacao-escola.md (DSE-RF-01 a 04) e regras.

Os números vêm do cálculo da Fase 1 e as barreiras da metodologia; nada é recalculado aqui nem
decidido por IA (RN-DSE-02). As posições e o estado da Declaração vêm da feature de declaração.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.declaracao.modelos import POSICOES_FINAIS
from app.features.declaracao.servico import estado as estado_declaracao
from app.features.diretor.schemas import BarreiraEscola, DashboardEscola, EixoEscola, SituacaoDeclaracao, SituacaoPlano
from app.features.plano.modelos import AcaoPlano, Plano, VersaoPlano
from etl.score import classificar_faixa

_EIXOS = [
    ("I", "AEE", "score_eixo_i"),
    ("II", "Acessibilidade", "score_eixo_ii"),
    ("III", "Profissionais", "score_eixo_iii"),
    ("IV", "Classe comum", "score_eixo_iv"),
]


def _situacao(declaracao) -> SituacaoDeclaracao:
    ultima = declaracao.ultima
    com_posicao = sum(1 for b in declaracao.barreiras if b.posicao in POSICOES_FINAIS)
    if ultima is None:
        return SituacaoDeclaracao(estado="rascunho", versao=None, com_posicao=com_posicao, total=len(declaracao.barreiras))
    return SituacaoDeclaracao(
        estado="publicada" if ultima.publicada_em and not ultima.retirada_em else "emitida", versao=ultima.versao, com_posicao=com_posicao,
        total=len(declaracao.barreiras), ha_alteracoes=declaracao.ha_alteracoes, emitida_em=ultima.emitida_em,
        publicada_em=None if ultima.retirada_em else ultima.publicada_em,
    )


def _situacao_plano(sessao: Session, co_entidade: int, declaracao) -> SituacaoPlano:
    """Só leitura: o dashboard não cria o rascunho do plano."""
    if declaracao.ultima is None:
        return SituacaoPlano(estado="sem_declaracao")
    plano = sessao.get(Plano, co_entidade)
    acoes = sessao.scalar(select(func.count()).select_from(AcaoPlano).where(AcaoPlano.co_entidade == co_entidade))
    ultima_versao = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == co_entidade).order_by(VersaoPlano.versao.desc()))
    base = plano.declaracao_versao if plano else declaracao.ultima.versao
    return SituacaoPlano(
        estado=ultima_versao.estado if ultima_versao else "rascunho", versao=ultima_versao.versao if ultima_versao else None,
        acoes_no_rascunho=acoes, declaracao_base=base, desatualizado=base < declaracao.ultima.versao,
        comentario=ultima_versao.comentario if ultima_versao else None, decidida_em=ultima_versao.decidida_em if ultima_versao else None,
        versao_aceita=sessao.scalar(
            select(func.max(VersaoPlano.versao)).where(VersaoPlano.co_entidade == co_entidade, VersaoPlano.estado == "aceito")
        ),
        versao_publicada=sessao.scalar(
            select(VersaoPlano.versao).where(
                VersaoPlano.co_entidade == co_entidade, VersaoPlano.publicada_em.is_not(None), VersaoPlano.retirada_em.is_(None)
            )
        ),
    )


def dashboard(sessao: Session, co_entidade: int) -> DashboardEscola:
    declaracao = estado_declaracao(sessao, co_entidade)
    escola = declaracao.escola.escola
    eixos = []
    for codigo, nome, coluna in _EIXOS:
        score = escola[coluna]
        do_eixo = [b for b in declaracao.barreiras if b.barreira.eixo == codigo]
        eixos.append(EixoEscola(
            eixo=codigo, nome=nome, score=score, faixa=classificar_faixa(score)[0] if score is not None else None,
            barreiras=len(do_eixo), com_posicao=sum(1 for b in do_eixo if b.posicao in POSICOES_FINAIS),
        ))

    return DashboardEscola(
        co_entidade=escola["co_entidade"], nome=escola["no_entidade"], municipio=escola["no_municipio"], uf=escola["sg_uf"],
        rede=escola["rede"], censo_versao=escola["censo_versao"], score=escola["score"], faixa=escola["faixa"],
        matriculas_educacao_especial=int(escola["qt_mat_esp"] or 0), matriculas_classe_comum=int(escola["qt_mat_esp_cc"] or 0),
        eixos=eixos,
        barreiras=[
            BarreiraEscola(
                codigo=b.barreira.codigo, eixo=b.barreira.eixo, nome=b.barreira.nome, dado_censo=b.barreira.texto,
                pontos=b.barreira.pontos, nota=b.barreira.nota, posicao=b.posicao, resumo=b.resumo,
            )
            for b in declaracao.barreiras
        ],
        metodologia_versao=declaracao.escola.metodologia_versao,
        declaracao=_situacao(declaracao),
        plano=_situacao_plano(sessao, co_entidade, declaracao),
    )
