from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

Posicao = Literal["sem_posicao", "rascunho", "obstaculo", "divergencia", "sem_relato"]


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EixoEscola(_Camel):
    eixo: str
    nome: str
    score: float | None
    faixa: str | None
    barreiras: int
    com_posicao: int


class BarreiraEscola(_Camel):
    codigo: str
    eixo: str
    nome: str
    dado_censo: str
    pontos: float
    nota: str | None = None
    posicao: Posicao
    resumo: str | None = None


class SituacaoDeclaracao(_Camel):
    estado: Literal["rascunho", "emitida", "publicada"]
    """Estado da última versão; "rascunho" quando nenhuma foi emitida."""
    versao: int | None
    com_posicao: int
    total: int
    ha_alteracoes: bool = False
    """Rascunho mudou depois da última versão emitida."""
    emitida_em: datetime | None = None
    publicada_em: datetime | None = None


class SituacaoPlano(_Camel):
    estado: Literal["sem_declaracao", "rascunho", "aguardando_analise", "aceito", "ajustes_solicitados", "reprovado"]
    """Estado da última versão submetida; "rascunho" se nenhuma foi enviada."""
    versao: int | None = None
    acoes_no_rascunho: int = 0
    declaracao_base: int | None = None
    desatualizado: bool = False
    """O plano usa uma Declaração anterior à última emitida (RN-PAE-00)."""
    comentario: str | None = None
    """Comentário da secretaria sobre a última versão (já passou pelo Guardião ao ser gravado)."""
    decidida_em: datetime | None = None
    versao_aceita: int | None = None
    """Última versão aceita pela secretaria (pode ser anterior à última enviada)."""
    versao_publicada: int | None = None
    """Versão publicada e não retirada; só aparece ao público com a Declaração publicada."""


class DashboardEscola(_Camel):
    co_entidade: int
    nome: str
    municipio: str
    uf: str
    rede: str
    censo_versao: str
    score: float
    faixa: str
    matriculas_educacao_especial: int
    matriculas_classe_comum: int
    eixos: list[EixoEscola]
    barreiras: list[BarreiraEscola]
    metodologia_versao: str
    declaracao: SituacaoDeclaracao
    plano: SituacaoPlano | None = None
