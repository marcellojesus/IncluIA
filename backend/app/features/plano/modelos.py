"""Tabelas do Plano de Ação Escolar (requirements/diretor/plano-acao-escolar.md; RN-PAE-00 a 05).

- `planos`: o rascunho da escola e a versão da Declaração que ele usa como base (PAE-RF-00).
- `sugestoes_plano`: propostas da IA ainda não decididas pelo diretor (RN-PAE-01).
- `acoes_plano`: ações do rascunho, aceitas de uma sugestão ou escritas pelo diretor (PAE-RF-04/05).
- `versoes_plano` + `itens_versao_plano`: versões submetidas, cópias congeladas (RN-PAE-04). A
  decisão da secretaria entra na própria versão, uma única vez.

Todo texto livre do diretor é gravado mascarado pelo Guardião LGPD (AD-05).
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.banco_gestao import Base, agora

HORIZONTES = ("LOA", "PPA")
"""LOA: exercício corrente; PPA: horizonte de quatro anos (PRD, Plano de Ação)."""


def _novo_id() -> str:
    return str(uuid.uuid4())


class Plano(Base):
    __tablename__ = "planos"

    co_entidade: Mapped[int] = mapped_column(Integer, primary_key=True)
    declaracao_versao: Mapped[int] = mapped_column(Integer)
    """Versão emitida da Declaração usada como contexto (RN-PAE-00)."""
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class SugestaoPlano(Base):
    __tablename__ = "sugestoes_plano"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    declaracao_versao: Mapped[int] = mapped_column(Integer)
    conteudo: Mapped[dict] = mapped_column(JSON)
    """Ação, relação com o obstáculo, responsável, prazo, horizonte, custo, premissas, fontes e incertezas."""
    estado: Mapped[str] = mapped_column(String(15), default="pendente")
    """"pendente", "aceita", "descartada" ou "substituida" (trocada por um ajuste pedido à IA)."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class AcaoPlano(Base):
    __tablename__ = "acoes_plano"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    acao: Mapped[str] = mapped_column(Text)
    relacao: Mapped[str | None] = mapped_column(Text)
    """Como a ação responde ao obstáculo ou à divergência da Declaração (RN-PAE-02)."""
    responsavel: Mapped[str | None] = mapped_column(String(200))
    prazo: Mapped[str | None] = mapped_column(String(100))
    horizonte: Mapped[str] = mapped_column(String(5))
    custo_estimado: Mapped[str | None] = mapped_column(String(200))
    premissas: Mapped[str | None] = mapped_column(Text)
    fontes: Mapped[list] = mapped_column(JSON, default=list)
    """Identificadores de trechos da base normativa citados na proposta."""
    origem: Mapped[str] = mapped_column(String(10))
    """"ia" (aceita de uma sugestão) ou "diretor" (escrita por ele) — PAE-RF-05."""
    editada: Mapped[bool] = mapped_column(Boolean, default=False)
    """Sugestão da IA alterada pelo diretor depois de aceita."""
    sugestao_id: Mapped[str | None] = mapped_column(ForeignKey("sugestoes_plano.id"))
    autor_id: Mapped[str] = mapped_column(ForeignKey("contas.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class VersaoPlano(Base):
    __tablename__ = "versoes_plano"
    __table_args__ = (UniqueConstraint("co_entidade", "versao", name="uq_versoes_plano_escola_versao"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_entidade: Mapped[int] = mapped_column(Integer, index=True)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    versao: Mapped[int] = mapped_column(Integer)
    declaracao_versao: Mapped[int] = mapped_column(Integer)
    submetida_por: Mapped[str] = mapped_column(ForeignKey("contas.id"))
    submetida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    estado: Mapped[str] = mapped_column(String(25), default="aguardando_analise")
    """"aguardando_analise", "aceito", "ajustes_solicitados" ou "reprovado" (decisão da secretaria)."""
    decidida_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id"))
    decidida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comentario: Mapped[str | None] = mapped_column(Text)
    publicada_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id", name="fk_versoes_plano_publicada_por"))
    publicada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Só versão aceita pela secretaria, com Declaração publicada, por decisão do diretor."""
    retirada_por: Mapped[str | None] = mapped_column(ForeignKey("contas.id", name="fk_versoes_plano_retirada_por"))
    retirada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirada_motivo: Mapped[str | None] = mapped_column(String(30))

    itens: Mapped[list["ItemVersaoPlano"]] = relationship(back_populates="versao_plano", order_by="ItemVersaoPlano.ordem")
    apontamentos: Mapped[list["ApontamentoPlano"]] = relationship(order_by="ApontamentoPlano.criado_em")


class ItemVersaoPlano(Base):
    __tablename__ = "itens_versao_plano"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    versao_id: Mapped[str] = mapped_column(ForeignKey("versoes_plano.id"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    codigo: Mapped[str] = mapped_column(String(10))
    barreira: Mapped[str] = mapped_column(String(200))
    acao: Mapped[str] = mapped_column(Text)
    relacao: Mapped[str | None] = mapped_column(Text)
    responsavel: Mapped[str | None] = mapped_column(String(200))
    prazo: Mapped[str | None] = mapped_column(String(100))
    horizonte: Mapped[str] = mapped_column(String(5))
    custo_estimado: Mapped[str | None] = mapped_column(String(200))
    premissas: Mapped[str | None] = mapped_column(Text)
    fontes: Mapped[list] = mapped_column(JSON, default=list)
    origem: Mapped[str] = mapped_column(String(10))
    editada: Mapped[bool] = mapped_column(Boolean, default=False)
    publico: Mapped[dict | None] = mapped_column(JSON)
    """Texto público congelado na publicação (ação, relação, responsável, prazo, custo), já conferido."""
    acao_id: Mapped[str | None] = mapped_column(String(36))
    """Ação do rascunho que originou o item (sem chave estrangeira: a ação pode ser removida depois),
    para destacar ao diretor a ação apontada pela secretaria."""

    versao_plano: Mapped[VersaoPlano] = relationship(back_populates="itens")


class ApontamentoPlano(Base):
    """Barreira ou ação que a secretaria marcou para ajuste ao decidir uma versão (SFR-RF-04)."""

    __tablename__ = "apontamentos_plano"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    versao_id: Mapped[str] = mapped_column(ForeignKey("versoes_plano.id", name="fk_apontamentos_plano_versao"), index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    item_id: Mapped[str | None] = mapped_column(ForeignKey("itens_versao_plano.id", name="fk_apontamentos_plano_item"))
    """Sem item, o apontamento é sobre a barreira (ex.: falta ação para ela)."""
    texto: Mapped[str | None] = mapped_column(Text)
    """Nota curta da secretaria, já passada pelo Guardião LGPD."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
