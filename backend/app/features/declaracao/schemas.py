from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.features.plano.schemas import PlanoPublico


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BarreiraDeclaracao(_Camel):
    codigo: str
    eixo: str
    nome: str
    dado_censo: str
    pontos: float
    nota: str | None = None
    posicao: Literal["sem_posicao", "rascunho", "obstaculo", "divergencia", "sem_relato"]
    texto: str | None = None
    resumo: str | None = None
    relato_original: str | None = None
    pergunta_inicial: str = ""
    atualizado_em: datetime | None = None


class ResumoVersao(_Camel):
    versao: int
    emitida_em: datetime
    publicada_em: datetime | None = None
    retirada_em: datetime | None = None


class EstadoDeclaracao(_Camel):
    escola: str
    co_entidade: int
    censo_versao: str
    metodologia_versao: str
    barreiras: list[BarreiraDeclaracao]
    faltam: int
    ha_alteracoes: bool
    pode_emitir: bool
    versoes: list[ResumoVersao]


class NovaPosicao(_Camel):
    posicao: Literal["obstaculo", "divergencia", "sem_relato"]
    texto: str | None = Field(default=None, max_length=3000)
    resumo: str | None = Field(default=None, max_length=300)


class ItemVersao(_Camel):
    codigo: str
    eixo: str
    barreira: str
    dado_censo: str
    pontos: float
    posicao: str
    texto: str | None = None
    resumo: str | None = None


class VersaoDeclaracao(_Camel):
    versao: int
    escola: str
    censo_versao: str
    metodologia_versao: str
    emitida_em: datetime
    publicada_em: datetime | None = None
    retirada_em: datetime | None = None
    itens: list[ItemVersao]


class MensagemConversa(_Camel):
    papel: Literal["diretor", "ia"]
    texto: str
    criado_em: datetime


class PedidoConversa(_Camel):
    mensagem: str | None = Field(default=None, max_length=2000)
    formalizar: bool = False


class RespostaConversa(_Camel):
    resposta: str
    texto_formal: str | None = None
    resumo: str | None = None


# --- Publicação ----------------------------------------------------------------------------------

class ItemPublico(_Camel):
    codigo: str
    eixo: str
    barreira: str
    dado_censo: str
    posicao: str
    texto_publico: str


class PontoDeAtencao(_Camel):
    codigo: str
    barreira: str
    mensagem: str
    bloqueia: bool


class PreviaPublica(_Camel):
    versao: int
    escola: str
    emitida_em: datetime
    publicada_em: datetime | None = None
    retirada_em: datetime | None = None
    itens: list[ItemPublico]
    pontos: list[PontoDeAtencao]
    pode_publicar: bool


class Aprovacao(_Camel):
    aprovado: bool


class DeclaracaoPublica(_Camel):
    """O que o público vê: sem autoria, sem relato original, sem rascunho (RN-DO-07)."""

    co_entidade: int
    escola: str
    versao: int
    emitida_em: datetime
    publicada_em: datetime
    censo_versao: str
    metodologia_versao: str
    itens: list[ItemPublico]
    plano: PlanoPublico | None = None
    """Plano de Ação aceito e publicado pela escola; só aparece junto com a Declaração publicada."""


# --- Secretário ----------------------------------------------------------------------------------

class DeclaracaoDaEscola(_Camel):
    co_entidade: int
    escola: str
    versao: int
    emitida_em: datetime
    publicada_em: datetime | None = None
    retirada_em: datetime | None = None
    total: int
    obstaculos: int
    divergencias: int
    sem_relato: int


class DeclaracoesDaRede(_Camel):
    municipio: str
    uf: str
    escolas_municipais: int
    com_declaracao: int
    escolas: list[DeclaracaoDaEscola]


class Retirada(_Camel):
    motivo: str = Field(max_length=30)
    """Categoria fechada (publicacao.MOTIVOS_RETIRADA)."""


class PublicacaoDaEscola(_Camel):
    co_entidade: int
    declaracao_versao: int
    plano_versao: int | None = None


class PublicacoesDoMunicipio(_Camel):
    """Lista pública: escolas com Declaração publicada e, delas, as com Plano de Ação publicado."""

    escolas: list[PublicacaoDaEscola]
