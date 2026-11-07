"""Tabelas do acesso à Gestão Ativa (requisitos e regras de acesso-gestao-ativa.md).

Dados mínimos (RF-11, RN-11): sem senha, sem documento pessoal; o código de uso único fica só como
hash e é invalidado depois do uso; a auditoria não guarda código nem token (RN-13).
"""

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.banco_gestao import Base, agora

Papel = Literal["diretor", "secretario", "admin"]
EstadoVinculo = Literal["pendente", "aprovado", "rejeitado", "suspenso", "revogado"]
ESTADOS_VIGENTES = ("pendente", "aprovado", "suspenso")
"""Estados em que o vínculo ainda ocupa a conta: no máximo um por conta."""


def _novo_id() -> str:
    return str(uuid.uuid4())


class Conta(Base):
    __tablename__ = "contas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    nome: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    papel: Mapped[str] = mapped_column(String(20))
    email_confirmado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)
    anonimizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Nome e e-mail apagados pela retenção (RN-RET-04); documentos e auditoria mostram "Conta encerrada"."""

    vinculos: Mapped[list["Vinculo"]] = relationship(
        back_populates="conta", foreign_keys="Vinculo.conta_id", order_by="Vinculo.criado_em"
    )

    def vinculo_vigente(self) -> "Vinculo | None":
        return next((v for v in reversed(self.vinculos) if v.estado in ESTADOS_VIGENTES), None)


class Vinculo(Base):
    """Diretor ↔ escola (co_entidade) ou secretário ↔ rede municipal (co_municipio)."""

    __tablename__ = "vinculos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    conta_id: Mapped[str] = mapped_column(ForeignKey("contas.id"), index=True)
    co_entidade: Mapped[int | None] = mapped_column(Integer, index=True)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    estado: Mapped[str] = mapped_column(String(20), default="pendente")
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Quando o dono do e-mail usou o código enviado PARA ESTE pedido. A confirmação antiga da conta
    não vale: sem isto, alguém pediria vínculo com o e-mail de outra pessoa (revisão do AgLGPD)."""
    decidido_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id"))
    decidido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    categoria: Mapped[str | None] = mapped_column(String(30))
    """Categoria fechada da última decisão (ex.: `oficio`, `afastamento`); é o que vai para a auditoria."""
    metodo_verificacao: Mapped[str | None] = mapped_column(Text)
    """Como o aprovador confirmou o vínculo (RF-05), já mascarado pelo Guardião LGPD."""
    justificativa: Mapped[str | None] = mapped_column(Text)
    """Justificativa da última decisão, já mascarada pelo Guardião LGPD."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    conta: Mapped[Conta] = relationship(back_populates="vinculos", foreign_keys=[conta_id])


class CodigoUsoUnico(Base):
    __tablename__ = "codigos_uso_unico"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    email: Mapped[str] = mapped_column(String(254), index=True)
    vinculo_id: Mapped[str | None] = mapped_column(ForeignKey("vinculos.id", ondelete="CASCADE"))
    """Pedido que este código confirma; código de entrada comum não confirma pedido."""
    codigo_hash: Mapped[str] = mapped_column(String(64))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class EventoAuditoria(Base):
    """RF-08 / RN-13: quem fez o quê, quando, sobre qual alvo, com que resultado e método.

    `detalhe` só recebe categoria fechada ou dado público (código INEP), nunca texto livre: a
    auditoria é a tabela de retenção mais longa. Ação anônima (pedido de acesso) tem `ator_id`
    nulo. A aplicação só insere aqui, nunca altera nem apaga."""

    __tablename__ = "auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    ator_id: Mapped[str | None] = mapped_column(ForeignKey("contas.id"))
    acao: Mapped[str] = mapped_column(String(50))
    alvo_tipo: Mapped[str] = mapped_column(String(20))
    alvo_id: Mapped[str] = mapped_column(String(36))
    resultado: Mapped[str] = mapped_column(String(20))
    detalhe: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
