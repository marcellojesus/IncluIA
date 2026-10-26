"""Tabelas da Declaração de Obstáculos (requirements/diretor/declaracao-obstaculos.md, RN-DO-01 a 09).

- `posicoes`: o rascunho da escola, uma linha por barreira; é o que o diretor edita.
- `declaracoes` + `declaracao_itens`: versões emitidas, cópias congeladas do rascunho (RN-DO-06):
  a aplicação só insere, nunca altera o conteúdo de uma versão emitida.
- `mensagens_obstaculo`: a conversa com a IA sobre uma barreira, até o diretor confirmar.

Todo texto escrito pelo diretor é gravado já mascarado pelo Guardião LGPD (AD-05, AD-03).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.banco_gestao import Base, agora

POSICOES_FINAIS = ("obstaculo", "divergencia", "sem_relato")
"""Posições que contam para a emissão; "rascunho" é relato em andamento."""


def _novo_id() -> str:
    return str(uuid.uuid4())


class Posicao(Base):
    __tablename__ = "posicoes"
    __table_args__ = (UniqueConstraint("co_entidade", "codigo", name="uq_posicoes_escola_barreira"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    posicao: Mapped[str] = mapped_column(String(20))
    relato_original: Mapped[str | None] = mapped_column(Text)
    """O que o diretor contou na conversa, mascarado (DO-RF-03: o relato original fica guardado)."""
    texto: Mapped[str | None] = mapped_column(Text)
    """Texto confirmado: obstáculo formalizado ou descrição da divergência, mascarado."""
    resumo: Mapped[str | None] = mapped_column(String(300))
    autor_id: Mapped[str] = mapped_column(ForeignKey("contas.id"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class Declaracao(Base):
    __tablename__ = "declaracoes"
    __table_args__ = (UniqueConstraint("co_entidade", "versao", name="uq_declaracoes_escola_versao"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    versao: Mapped[int] = mapped_column(Integer)
    censo_versao: Mapped[str] = mapped_column(String(10))
    metodologia_versao: Mapped[str] = mapped_column(String(10))
    emitida_por: Mapped[str] = mapped_column(ForeignKey("contas.id"))
    emitida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    publicada_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id"))
    publicada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirada_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id"))
    retirada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Publicação retirada (pelo diretor ou pela administração, inclusive a pedido de titular). A
    versão emitida continua guardada (AD-03); só deixa de aparecer na página pública."""
    retirada_motivo: Mapped[str | None] = mapped_column(String(30))

    itens: Mapped[list["DeclaracaoItem"]] = relationship(back_populates="declaracao", order_by="DeclaracaoItem.ordem")


class DeclaracaoItem(Base):
    """Cópia congelada de uma barreira e da posição no momento da emissão."""

    __tablename__ = "declaracao_itens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    declaracao_id: Mapped[str] = mapped_column(ForeignKey("declaracoes.id"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    codigo: Mapped[str] = mapped_column(String(10))
    eixo: Mapped[str] = mapped_column(String(5))
    barreira: Mapped[str] = mapped_column(String(200))
    dado_censo: Mapped[str] = mapped_column(Text)
    pontos: Mapped[float] = mapped_column(Float)
    posicao: Mapped[str] = mapped_column(String(20))
    texto: Mapped[str | None] = mapped_column(Text)
    resumo: Mapped[str | None] = mapped_column(String(300))
    texto_publico: Mapped[str | None] = mapped_column(Text)
    """Texto aprovado pelo diretor para a página pública; gravado uma única vez, na publicação."""

    declaracao: Mapped[Declaracao] = relationship(back_populates="itens")


class MensagemObstaculo(Base):
    __tablename__ = "mensagens_obstaculo"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    papel: Mapped[str] = mapped_column(String(10))
    """"diretor" ou "ia"."""
    texto: Mapped[str] = mapped_column(Text)
    """Mensagem do diretor mascarada pelo guardião, ou resposta da IA."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
