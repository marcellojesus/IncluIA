from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BarreiraBase(_Camel):
    codigo: str
    eixo: str
    barreira: str
    posicao: str
    texto: str | None = None
    resumo: str | None = None


class Sugestao(_Camel):
    id: str
    codigo: str
    acao: str
    relacao: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None
    premissas: str | None = None
    fontes: list[str] = []
    incertezas: str | None = None
    lacunas: list[str] = []
    ajustada: bool = False
    """Versão reescrita pela IA a pedido do diretor ("Ajustar com a IA")."""


class Acao(_Camel):
    id: str
    codigo: str
    acao: str
    relacao: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None
    premissas: str | None = None
    fontes: list[str] = []
    origem: Literal["ia", "diretor"]
    editada: bool


class Apontamento(_Camel):
    """Barreira (sem item) ou ação (com item) que a secretaria marcou para ajuste."""

    codigo: str
    item_id: str | None = None
    acao_id: str | None = None
    """Ação do rascunho que originou o item apontado, para o diretor achar o que mudar."""
    texto: str | None = None


class ResumoVersaoPlano(_Camel):
    versao: int
    declaracao_versao: int
    submetida_em: datetime
    estado: str
    decidida_em: datetime | None = None
    decidida_por: str | None = None
    """Nome de quem decidiu, visível à escola (RN-SFR-04)."""
    publicada_em: datetime | None = None
    retirada_em: datetime | None = None
    comentario: str | None = None


class EstadoPlano(_Camel):
    escola: str
    declaracao_base: int
    ultima_declaracao: int
    desatualizado: bool
    barreiras: list[BarreiraBase]
    sugestoes: list[Sugestao]
    acoes: list[Acao]
    versoes: list[ResumoVersaoPlano]
    pode_submeter: bool
    motivo: str | None = None
    fontes: dict[str, str] = {}
    """Identificador → citação legível dos trechos citados nas sugestões e ações."""
    aviso_guardiao: str | None = None
    apontamentos: list[Apontamento] = []
    """Pontos marcados pela secretaria na última versão, quando ela pediu ajustes ou reprovou."""
    """Preenchido quando a última operação trocou ou descartou trechos com dados pessoais (AD-05)."""


class NovaAcao(_Camel):
    codigo: str = Field(max_length=10)
    acao: str = Field(max_length=3000)
    relacao: str | None = Field(default=None, max_length=3000)
    responsavel: str | None = Field(default=None, max_length=200)
    prazo: str | None = Field(default=None, max_length=100)
    horizonte: Literal["LOA", "PPA"]
    custo_estimado: str | None = Field(default=None, max_length=200)
    premissas: str | None = Field(default=None, max_length=3000)


class PedidoSugestoes(_Camel):
    orientacao: str | None = Field(default=None, max_length=1000)


class PedidoAjuste(_Camel):
    pedido: str = Field(max_length=1000)


class AceiteSugestao(_Camel):
    edicao: NovaAcao | None = None
    """Campos editados pelo diretor antes de incluir; sem ela, a sugestão entra como veio."""


class Confirmacao(_Camel):
    confirmado: bool


class ItemVersao(_Camel):
    codigo: str
    id: str
    barreira: str
    acao: str
    relacao: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    horizonte: str
    custo_estimado: str | None = None
    premissas: str | None = None
    fontes: list[str] = []
    origem: str
    editada: bool


class VersaoPlano(_Camel):
    versao: int
    escola: str
    declaracao_versao: int
    submetida_em: datetime
    estado: str
    decidida_em: datetime | None = None
    decidida_por: str | None = None
    comentario: str | None = None
    itens: list[ItemVersao]
    fontes: dict[str, str] = {}
    apontamentos: list[Apontamento] = []


# --- Revisão pelo secretário (fila-revisao-planos.md) -------------------------------------------

class PlanoNaFila(_Camel):
    co_entidade: int
    escola: str
    versao: int
    estado: str
    submetida_em: datetime
    decidida_em: datetime | None = None
    declaracao_versao: int
    ultima_declaracao: int
    acoes: int
    loa: int
    ppa: int
    versoes: int


class FilaPlanos(_Camel):
    municipio: str
    uf: str
    planos: list[PlanoNaFila]


class RevisaoPlano(_Camel):
    co_entidade: int
    versao: VersaoPlano
    ultima_declaracao: int
    """Se maior que versao.declaracao_versao, a escola emitiu Declaração mais nova depois do envio (SFR-RF-03)."""
    versao_atual: int
    """Só a versão atual, em análise, pode ser decidida; as anteriores aparecem como substituídas."""
    historico: list[ResumoVersaoPlano]
    barreiras: list[BarreiraBase] = []
    """Barreiras da Declaração base, para agrupar o plano e apontar barreira sem ação."""
    aviso_guardiao: str | None = None
    """Preenchido quando o comentário da decisão teve trechos com dados pessoais mascarados (AD-05)."""


class ApontamentoEntrada(_Camel):
    codigo: str = Field(max_length=10)
    item_id: str | None = Field(default=None, max_length=36)
    texto: str | None = Field(default=None, max_length=500)


class Decisao(_Camel):
    decisao: Literal["aceitar", "ajustes", "reprovar"]
    comentario: str | None = Field(default=None, max_length=2000)
    apontamentos: list[ApontamentoEntrada] = Field(default_factory=list, max_length=60)


# --- Publicação do plano aceito (plano/publicacao.py) --------------------------------------------

class ItemPlanoPublico(_Camel):
    codigo: str
    barreira: str
    horizonte: str
    acao: str | None = None
    relacao: str | None = None
    responsavel: str | None = None
    prazo: str | None = None
    custo_estimado: str | None = None
    fontes: list[str] = []
    """Citações legíveis da base normativa."""


class PlanoPublico(_Camel):
    """O que o público vê: versão aceita e publicada, sem autoria, sem rascunho nem sugestões da IA."""

    versao: int
    declaracao_versao: int
    aceito_em: datetime | None = None
    publicado_em: datetime
    itens: list[ItemPlanoPublico]


class PontoPublicacaoPlano(_Camel):
    item: str
    mensagem: str
    bloqueia: bool


class PreviaPlanoPublico(_Camel):
    versao: int
    escola: str
    aceito_em: datetime | None = None
    publicado_em: datetime | None = None
    retirado_em: datetime | None = None
    itens: list[ItemPlanoPublico]
    pontos: list[PontoPublicacaoPlano]
    pode_publicar: bool
    motivo: str | None = None


class AprovacaoPublicacao(_Camel):
    aprovado: bool


class RetiradaPlano(_Camel):
    motivo: str = Field(max_length=30)
