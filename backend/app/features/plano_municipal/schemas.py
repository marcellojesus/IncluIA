from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ItemEscolarDaRede(_Camel):
    ref: str
    co_entidade: int
    escola: str
    item_id: str
    acao: str
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None


class BarreiraDaRede(_Camel):
    codigo: str
    eixo: str
    eixo_nome: str
    nome: str
    escolas_com_barreira: int
    """Escolas municipais com a barreira no Censo (calculado)."""
    escolas_com_acao: int
    """Escolas com plano aceito que trazem ação para a barreira (calculado)."""
    itens: list[ItemEscolarDaRede]


class EscolaAtendida(_Camel):
    co_entidade: int
    escola: str = ""
    item_ids: list[str] = []
    cobertura: Literal["total", "parcial"] = "total"


class SugestaoMunicipal(_Camel):
    id: str
    codigo: str
    acao: str
    justificativa: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None
    premissas: str | None = None
    prioridade: str = "media"
    fontes: list[str] = []
    incertezas: str | None = None
    lacunas: list[str] = []
    escolas: list[EscolaAtendida] = []


class AcaoMunicipal(_Camel):
    id: str
    codigos: list[str]
    acao: str
    justificativa: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None
    premissas: str | None = None
    prioridade: str
    fontes: list[str] = []
    escolas: list[EscolaAtendida] = []
    origem: str
    editada: bool


class ResumoVersaoMunicipal(_Camel):
    versao: int
    confirmada_em: datetime
    confirmada_por: str | None = None
    acoes: int
    escolas_atendidas: int


class EstadoPlanoMunicipal(_Camel):
    municipio: str
    uf: str
    escolas_municipais: int
    escolas_com_plano_aceito: int
    barreiras: list[BarreiraDaRede]
    sugestoes: list[SugestaoMunicipal]
    acoes: list[AcaoMunicipal]
    escolas_atendidas: int
    """Escolas distintas atendidas pelas ações do rascunho (calculado)."""
    versoes: list[ResumoVersaoMunicipal]
    fontes: dict[str, str] = {}
    aviso_guardiao: str | None = None


class VersaoPlanoMunicipal(_Camel):
    versao: int
    municipio: str
    confirmada_em: datetime
    confirmada_por: str | None = None
    acoes: list[AcaoMunicipal]
    escolas_atendidas: int
    fontes: dict[str, str] = {}


class NovaAcaoMunicipal(_Camel):
    codigos: list[str] = Field(min_length=1, max_length=10)
    acao: str = Field(max_length=3000)
    justificativa: str | None = Field(default=None, max_length=3000)
    responsavel: str | None = Field(default=None, max_length=200)
    prazo: str | None = Field(default=None, max_length=100)
    horizonte: Literal["LOA", "PPA"]
    custo_estimado: str | None = Field(default=None, max_length=200)
    premissas: str | None = Field(default=None, max_length=3000)
    prioridade: Literal["alta", "media", "baixa"] = "media"
    escolas: list[EscolaAtendida] = Field(default_factory=list, max_length=500)


class AceiteSugestaoMunicipal(_Camel):
    edicao: NovaAcaoMunicipal | None = None


class PedidoSugestoesMunicipais(_Camel):
    orientacao: str | None = Field(default=None, max_length=1000)


class Confirmacao(_Camel):
    confirmado: bool


# --- Diretor: ações municipais que atendem a própria escola (RN-SPM-03) -------------------------

class AcaoMunicipalDaEscola(_Camel):
    acao: str
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    prioridade: str
    cobertura: Literal["total", "parcial"]
    barreiras: list[str]
    escolas_atendidas: int
    """Quantas escolas da rede a ação atende (sem nomes de outras escolas)."""


class AcoesMunicipaisDaEscola(_Camel):
    versao: int | None = None
    confirmada_em: datetime | None = None
    acoes: list[AcaoMunicipalDaEscola] = []
