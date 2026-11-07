"""Prazos de retenção da Gestão Ativa, escolhidos pelo responsável em 2026-11-03 (AD-07; RN-RET-01 a 08).

Ainda a validar pelo jurídico e pelo encarregado de dados (PBD-120). Uma só rotina aplica todos os
prazos, na subida do servidor e pela linha de comando (`python -m app.features.acesso.cli limpar`):
- códigos de acesso (24 h) e pedidos nunca confirmados (72 h): `acesso.servico.limpar`, de antes;
- rascunhos (RN-RET-01): conversa parada e sugestão da IA descartada, substituída, esquecida ou
  aceita e depois editada ou removida saem em 30 dias; da sugestão fica só a linha, sem o conteúdo;
- pedido recusado sai em 30 dias (RN-RET-02);
- auditoria fica 5 anos e não muda (RN-RET-03); o banco impede alteração e exclusão antes do prazo;
- conta revogada é pseudonimizada 6 meses depois do fim do último vínculo, e conta que nunca teve
  vínculo aprovado, 30 dias depois (RN-RET-04);
- versão retirada por dado pessoal ou pedido de titular tem o texto livre apagado 30 dias depois,
  junto com as outras cópias da escola: versões com o mesmo texto, planos feitos sobre a Declaração
  retirada, rascunhos, conversas e sugestões (RN-RET-05);
- versões ficam enquanto durar o programa (RN-RET-06);
- síntese do Analítico sai em 1 ano, na edição nova do Censo ou quando usou relato de Declaração
  depois retirada por dado pessoal ou pedido de titular (RN-RET-07).

Cada regra grava em separado: a falha de uma fica no log, sem conteúdo, e não desfaz as outras nem
impede a subida do servidor (revisão do AgLGPD de 2026-11-03, A1 e M4).
"""

import logging
import re
import unicodedata
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.acesso import servico as acesso
from app.features.acesso.modelos import ESTADOS_VIGENTES, CodigoUsoUnico, Conta, EventoAuditoria, Vinculo
from app.features.analitico.modelos import SinteseAnalitica
from app.features.declaracao.conversa import limpar_conversas_paradas
from app.features.declaracao.modelos import Declaracao, MensagemObstaculo, Posicao
from app.features.plano.modelos import AcaoPlano, Plano, SugestaoPlano, VersaoPlano
from app.features.plano.publicacao import MOTIVOS_LGPD
from app.features.plano_municipal.modelos import AcaoMunicipal, SugestaoMunicipal
from app.shared.banco_gestao import agora

logger = logging.getLogger(__name__)

PRAZO_RASCUNHO = timedelta(days=30)
PRAZO_PEDIDO_RECUSADO = timedelta(days=30)
PRAZO_AUDITORIA = timedelta(days=1827)
"""5 anos, com um dia bissexto; o mesmo corte dos gatilhos da migração 7d1e0c5a9b42."""
PRAZO_CONTA_ENCERRADA = timedelta(days=183)
PRAZO_CONTA_NUNCA_APROVADA = timedelta(days=30)
PRAZO_TEXTO_RETIRADO = timedelta(days=30)
PRAZO_SINTESE = timedelta(days=365)

TEXTO_APAGADO = "[Texto apagado: versão retirada por proteção de dados]"
NOME_PSEUDONIMIZADO = "Conta encerrada"


def _utc(momento: datetime | None) -> datetime | None:
    """O SQLite devolve datas sem fuso; tudo é gravado em UTC."""
    return momento.replace(tzinfo=timezone.utc) if momento and momento.tzinfo is None else momento


def _norma(texto: str | None) -> str:
    """Para achar a mesma frase com outra pontuação, acento ou caixa (AgLGPD, A2)."""
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", sem_acento.lower()))


def _auditar(sessao: Session, acao: str, alvo_tipo: str, alvo_id: str, detalhe: str) -> None:
    sessao.add(EventoAuditoria(ator_id=None, acao=acao, alvo_tipo=alvo_tipo, alvo_id=alvo_id, resultado="ok", detalhe=detalhe))


# --- RN-RET-01: rascunhos ----------------------------------------------------------------------

def _usada_sem_mudanca(sessao: Session, modelo, sugestao_id: str) -> bool:
    acao_modelo = AcaoPlano if modelo is SugestaoPlano else AcaoMunicipal
    return sessao.scalar(select(acao_modelo.id).where(acao_modelo.sugestao_id == sugestao_id, acao_modelo.editada.is_(False))) is not None


def apagar_sugestoes(sessao: Session, momento: datetime) -> int:
    """Sugestão descartada, substituída ou pendente há mais de 30 dias perde o conteúdo; a pendente
    vira "expirada". A aceita só fica enquanto a ação dela existe sem edição: aí o texto é o mesmo da ação."""
    apagadas = 0
    for modelo in (SugestaoPlano, SugestaoMunicipal):
        for sugestao in sessao.scalars(select(modelo).where(modelo.criado_em < momento - PRAZO_RASCUNHO)):
            if not sugestao.conteudo and sugestao.estado != "pendente":
                continue
            if sugestao.estado == "aceita" and _usada_sem_mudanca(sessao, modelo, sugestao.id):
                continue
            if sugestao.estado == "expirada":
                continue
            sugestao.conteudo = {}
            sugestao.estado = "expirada" if sugestao.estado == "pendente" else sugestao.estado
            apagadas += 1
    return apagadas


# --- RN-RET-02 e 04: pedidos recusados e contas encerradas -------------------------------------

def apagar_pedidos_recusados(sessao: Session, momento: datetime) -> int:
    """O pedido recusado guarda a justificativa e o método de verificação; sai em 30 dias."""
    return sessao.execute(
        delete(Vinculo).where(Vinculo.estado == "rejeitado", Vinculo.decidido_em < momento - PRAZO_PEDIDO_RECUSADO)
        .execution_options(synchronize_session=False)
    ).rowcount


def pseudonimizar_contas(sessao: Session, momento: datetime) -> int:
    """Conta sem vínculo vigente: nome e e-mail apagados. É pseudonimização, não anonimização (AgLGPD,
    M2): o id continua ligado às versões, aos vínculos e à auditoria, para a prestação de contas. O
    administrador fica de fora: é provisionado à mão."""
    feitas = 0
    for conta in sessao.scalars(select(Conta).where(Conta.papel != "admin", Conta.anonimizada_em.is_(None))):
        if any(v.estado in ESTADOS_VIGENTES for v in conta.vinculos):
            continue
        fins = [_utc(v.decidido_em) for v in conta.vinculos if v.decidido_em]
        fim = max(fins) if fins else _utc(conta.atualizado_em)
        prazo = PRAZO_CONTA_ENCERRADA if any(v.estado == "revogado" for v in conta.vinculos) else PRAZO_CONTA_NUNCA_APROVADA
        if fim >= momento - prazo:
            continue
        sessao.execute(delete(CodigoUsoUnico).where(CodigoUsoUnico.email == conta.email).execution_options(synchronize_session=False))
        conta.nome = NOME_PSEUDONIMIZADO
        conta.email = f"conta-encerrada-{conta.id}@anonimizada.invalid"
        conta.anonimizada_em = momento
        for vinculo in conta.vinculos:
            vinculo.justificativa = None
            vinculo.metodo_verificacao = None
        _auditar(sessao, "conta_pseudonimizada", "conta", conta.id, "retenção: conta sem vínculo vigente")
        feitas += 1
    return feitas


# --- RN-RET-05: texto da versão retirada por proteção de dados ---------------------------------

def _apagar_itens_da_declaracao(declaracao: Declaracao, textos: set[str] | None = None) -> set[str]:
    """Apaga o texto de todos os itens (textos None) ou só dos que repetem um dos textos. Devolve os
    códigos das barreiras atingidas."""
    codigos = set()
    for item in declaracao.itens:
        if item.texto and item.texto != TEXTO_APAGADO and (textos is None or _norma(item.texto) in textos):
            item.texto = TEXTO_APAGADO
            item.resumo = item.texto_publico = None
            codigos.add(item.codigo)
        elif textos is None:
            item.resumo = item.texto_publico = None
    return codigos


def _apagar_versao_do_plano(sessao: Session, versao: VersaoPlano, momento: datetime) -> set[str]:
    textos = {_norma(i.acao) for i in versao.itens if i.acao != TEXTO_APAGADO}
    for item in versao.itens:
        item.acao = TEXTO_APAGADO
        item.relacao = item.responsavel = item.prazo = item.custo_estimado = item.premissas = item.publico = None
    versao.comentario = None
    for apontamento in versao.apontamentos:
        apontamento.texto = None
    if versao.texto_apagado_em is None:
        versao.texto_apagado_em = momento
        _auditar(sessao, "texto_apagado", "plano", versao.id, f"retenção: escola {versao.co_entidade} v{versao.versao}")
    return textos


def _apagar_rascunho_do_plano(sessao: Session, co_entidade: int, declaracao_versao: int, textos: set[str]) -> None:
    """Ação em edição feita sobre a Declaração retirada, ou com o mesmo texto de versão apagada, e as
    sugestões dessa base."""
    plano = sessao.get(Plano, co_entidade)
    sobre_a_retirada = plano is not None and plano.declaracao_versao == declaracao_versao
    for acao in sessao.scalars(select(AcaoPlano).where(AcaoPlano.co_entidade == co_entidade)):
        if sobre_a_retirada or _norma(acao.acao) in textos:
            acao.acao = TEXTO_APAGADO
            acao.relacao = acao.responsavel = acao.prazo = acao.custo_estimado = acao.premissas = None
    for sugestao in sessao.scalars(
        select(SugestaoPlano).where(SugestaoPlano.co_entidade == co_entidade, SugestaoPlano.declaracao_versao == declaracao_versao)
    ):
        sugestao.conteudo = {}


def _retiradas(sessao: Session, modelo, momento: datetime) -> list:
    return list(sessao.scalars(select(modelo).where(
        modelo.retirada_motivo.in_(MOTIVOS_LGPD), modelo.retirada_em < momento - PRAZO_TEXTO_RETIRADO, modelo.texto_apagado_em.is_(None),
    )))


def apagar_texto_retirado(sessao: Session, momento: datetime) -> int:
    """A versão fica (AD-03), com a estrutura (barreira, posição, dado do Censo, horizonte); o texto
    livre sai, junto com as cópias da mesma escola (AgLGPD, A2)."""
    apagadas = 0
    for declaracao in _retiradas(sessao, Declaracao, momento):
        co = declaracao.co_entidade
        textos = {_norma(i.texto) for i in declaracao.itens if i.texto and i.texto != TEXTO_APAGADO}
        codigos = _apagar_itens_da_declaracao(declaracao)
        declaracao.texto_apagado_em = momento
        _auditar(sessao, "texto_apagado", "declaracao", declaracao.id, f"retenção: escola {co} v{declaracao.versao}")
        for outra in sessao.scalars(select(Declaracao).where(Declaracao.co_entidade == co, Declaracao.id != declaracao.id)):
            codigos |= _apagar_itens_da_declaracao(outra, textos)
        for posicao in sessao.scalars(select(Posicao).where(Posicao.co_entidade == co, Posicao.codigo.in_(codigos))):
            # O relato original da conversa sai sempre; o texto confirmado, se ainda é o retirado.
            posicao.relato_original = None
            if _norma(posicao.texto) in textos:
                posicao.texto = posicao.resumo = None
        sessao.execute(delete(MensagemObstaculo).where(MensagemObstaculo.co_entidade == co, MensagemObstaculo.codigo.in_(codigos))
                       .execution_options(synchronize_session=False))
        textos_do_plano: set[str] = set()
        for versao in sessao.scalars(select(VersaoPlano).where(VersaoPlano.co_entidade == co, VersaoPlano.declaracao_versao == declaracao.versao)):
            textos_do_plano |= _apagar_versao_do_plano(sessao, versao, momento)
        _apagar_rascunho_do_plano(sessao, co, declaracao.versao, textos_do_plano)
        apagadas += 1
    for versao in _retiradas(sessao, VersaoPlano, momento):
        textos = set()
        # Versões feitas sobre a mesma Declaração repetem as ações (ajustes pedidos pela secretaria).
        for irma in sessao.scalars(select(VersaoPlano).where(
            VersaoPlano.co_entidade == versao.co_entidade, VersaoPlano.declaracao_versao == versao.declaracao_versao,
        )):
            textos |= _apagar_versao_do_plano(sessao, irma, momento)
        _apagar_rascunho_do_plano(sessao, versao.co_entidade, versao.declaracao_versao, textos)
        apagadas += 1
    return apagadas


# --- RN-RET-07: sínteses do Analítico ----------------------------------------------------------

def apagar_sinteses(sessao: Session, momento: datetime) -> int:
    retiradas = set(sessao.scalars(select(Declaracao.id).where(Declaracao.retirada_motivo.in_(MOTIVOS_LGPD))))
    edicoes: dict[int, str | None] = {}
    apagadas = 0
    for sintese in sessao.scalars(select(SinteseAnalitica)):
        if sintese.co_municipio not in edicoes:
            edicoes[sintese.co_municipio] = censo.edicao_do_municipio(sintese.co_municipio)
        atual, edicao = edicoes[sintese.co_municipio], (sintese.conteudo or {}).get("censo_versao")
        # Sem a edição atual (município fora do artefato), não dá para dizer que mudou (AgLGPD, M4).
        mudou = bool(edicao and atual and edicao != atual)
        usou_retirada = any(e.get("declaracao_id") in retiradas for e in (sintese.conteudo or {}).get("enviados") or [])
        if _utc(sintese.gerada_em) < momento - PRAZO_SINTESE or mudou or usou_retirada:
            sessao.delete(sintese)
            apagadas += 1
    return apagadas


# --- RN-RET-03: auditoria ----------------------------------------------------------------------

def apagar_auditoria_antiga(sessao: Session, momento: datetime) -> int:
    return sessao.execute(
        delete(EventoAuditoria).where(EventoAuditoria.criado_em < momento - PRAZO_AUDITORIA).execution_options(synchronize_session=False)
    ).rowcount


_REGRAS: list[tuple[str, Callable[[Session, datetime], int]]] = [
    ("conversas_paradas", lambda sessao, _momento: limpar_conversas_paradas(sessao)),
    ("sugestoes_apagadas", apagar_sugestoes),
    # Antes de apagar o pedido recusado, que guarda a data da recusa.
    ("contas_pseudonimizadas", pseudonimizar_contas),
    ("pedidos_recusados", apagar_pedidos_recusados),
    ("versoes_com_texto_apagado", apagar_texto_retirado),
    ("sinteses_apagadas", apagar_sinteses),
    ("auditoria_antiga", apagar_auditoria_antiga),
]


def aplicar(sessao: Session, momento: datetime | None = None) -> dict[str, int]:
    """Aplica todos os prazos e devolve quantos registros cada regra atingiu (sem conteúdo). Regra que
    falha fica com -1 e o erro vai ao log só com o tipo."""
    agora_ = agora()
    momento = momento or agora_
    if momento > agora_ + timedelta(minutes=1):
        raise ValueError("A retenção não pode ser aplicada com data futura.")
    resultado: dict[str, int] = {}
    regras = [("acesso", lambda s, _m: acesso.limpar(s)), *_REGRAS]
    for nome, regra in regras:
        try:
            atingidos = regra(sessao, momento)
            sessao.commit()
        except Exception as erro:  # noqa: BLE001 — uma regra não derruba as outras nem a subida
            sessao.rollback()
            logger.error("Retenção: a regra %s falhou (%s)", nome, type(erro).__name__)
            resultado[nome] = -1
            continue
        if isinstance(atingidos, dict):
            resultado.update(atingidos)
        else:
            resultado[nome] = atingidos
    return resultado
