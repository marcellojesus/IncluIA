"""Tabelas do Plano Estratégico Municipal (requirements/secretario/plano-estrategico-municipal.md; RN-SPM-01 a 06).

- `sugestoes_municipais`: propostas da IA por barreira, ainda não decididas pelo secretário (RN-SPM-04).
- `acoes_municipais`: rascunho do plano da rede, com as escolas e ações escolares que cada ação
  pretende atender e se a cobertura é total ou parcial (RN-SPM-01 e 06).
- `versoes_plano_municipal`: versões confirmadas, cópias congeladas. Confirmar não é financiar nem
  executar (RN-SPM-05). Nada aqui altera os Planos de Ação das escolas (RN-SPM-02).

Texto livre do secretário é gravado mascarado pelo Guardião LGPD (AD-05).
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.banco_gestao import Base, agora

PRIORIDADES = ("alta", "media", "baixa")
COBERTURAS = ("total", "parcial")


def _novo_id() -> str:
    return str(uuid.uuid4())


class SugestaoMunicipal(Base):
    __tablename__ = "sugestoes_municipais"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    codigo: Mapped[str] = mapped_column(String(10))
    conteudo: Mapped[dict] = mapped_column(JSON)
    """Ação, justificativa, responsável, prazo, horizonte, custo, premissas, prioridade, fontes,
    incertezas, lacunas e `escolas` ([{co_entidade, item_ids, cobertura}])."""
    estado: Mapped[str] = mapped_column(String(15), default="pendente")
    """"pendente", "aceita" ou "descartada"."""
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)


class AcaoMunicipal(Base):
    __tablename__ = "acoes_municipais"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    codigos: Mapped[list] = mapped_column(JSON)
    """Barreiras que a ação enfrenta."""
    acao: Mapped[str] = mapped_column(Text)
    justificativa: Mapped[str | None] = mapped_column(Text)
    responsavel: Mapped[str | None] = mapped_column(String(200))
    prazo: Mapped[str | None] = mapped_column(String(100))
    horizonte: Mapped[str] = mapped_column(String(5))
    custo_estimado: Mapped[str | None] = mapped_column(String(200))
    premissas: Mapped[str | None] = mapped_column(Text)
    prioridade: Mapped[str] = mapped_column(String(10), default="media")
    fontes: Mapped[list] = mapped_column(JSON, default=list)
    escolas: Mapped[list] = mapped_column(JSON, default=list)
    """[{"co_entidade": int, "item_ids": [str], "cobertura": "total" | "parcial"}] (RN-SPM-01)."""
    origem: Mapped[str] = mapped_column(String(12))
    """"ia" (aceita de uma sugestão) ou "secretario"."""
    editada: Mapped[bool] = mapped_column(Boolean, default=False)
    sugestao_id: Mapped[str | None] = mapped_column(String(36))
    autor_id: Mapped[str] = mapped_column(ForeignKey("contas.id", name="fk_acoes_municipais_autor"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)


class VersaoPlanoMunicipal(Base):
    __tablename__ = "versoes_plano_municipal"
    __table_args__ = (UniqueConstraint("co_municipio", "versao", name="uq_versao_plano_municipal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    versao: Mapped[int] = mapped_column(Integer)
    confirmada_por: Mapped[str] = mapped_column(ForeignKey("contas.id", name="fk_versoes_plano_municipal_autor"))
    confirmada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    acoes: Mapped[list] = mapped_column(JSON)
    """Cópia congelada das ações (mesmos campos de AcaoMunicipal, sem autoria)."""
    base: Mapped[dict] = mapped_column(JSON)
    """Planos escolares considerados: {"planos": [{"co_entidade": int, "versao": int}]}."""
