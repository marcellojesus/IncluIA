"""Tabela do Analítico de Barreiras (requirements/secretario/analitico-barreiras.md; RN-SAB-01 a 05).

- `sinteses_analiticas`: síntese da rede escrita pela IA a pedido do secretário. Cada pedido grava uma
  linha nova; a tela mostra a mais recente. A `assinatura` resume as Declarações e os planos usados,
  para avisar quando há registros novos desde a última síntese. Contagens não ficam aqui: são
  recalculadas a cada abertura (RN-SAB-02).
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.banco_gestao import Base, agora


def _novo_id() -> str:
    return str(uuid.uuid4())


class SinteseAnalitica(Base):
    __tablename__ = "sinteses_analiticas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    co_municipio: Mapped[int] = mapped_column(Integer, index=True)
    gerada_por: Mapped[str] = mapped_column(ForeignKey("contas.id", name="fk_sinteses_analiticas_gerada_por"))
    gerada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    assinatura: Mapped[str] = mapped_column(String(64))
    modelo: Mapped[str] = mapped_column(String(80))
    conteudo: Mapped[dict] = mapped_column(JSON)
    """`achados` ([{tipo, texto, barreiras, evidencias: [{co_entidade, codigo}]}]), `limitacoes` e
    `fora` (relatos que o Guardião bloqueou e não foram à IA)."""
