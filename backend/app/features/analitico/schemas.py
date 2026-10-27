from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Evidencia(_Camel):
    co_entidade: int
    escola: str
    posicao: str | None
    resumo: str | None
    acoes: list[str]
    plano_estado: str | None


class BarreiraAnalitica(_Camel):
    codigo: str
    eixo: str
    eixo_nome: str
    nome: str
    nota: str | None
    escolas: int
    alunos: int
    """Matrículas da educação especial nas escolas com a barreira: critério de ordenação (decisão de 2026-10-27)."""
    alta_recorrencia: bool
    com_declaracao: int
    obstaculos: int
    divergencias: int
    sem_relato: int
    com_acao: int
    com_acao_aceita: int
    evidencias: list[Evidencia]


class EvidenciaDoAchado(_Camel):
    co_entidade: int
    escola: str
    codigo: str


class Achado(_Camel):
    tipo: Literal["observacao", "hipotese", "recomendacao"]
    texto: str
    barreiras: list[str]
    evidencias: list[EvidenciaDoAchado]


class Sintese(_Camel):
    gerada_em: datetime
    modelo: str
    desatualizada: bool
    """Alguma escola emitiu Declaração ou enviou plano depois da síntese."""
    achados: list[Achado]
    limitacoes: list[str]
    relatos_fora: int
    """Resumos que o Guardião LGPD bloqueou e não foram à IA."""


class Analitico(_Camel):
    municipio: str
    uf: str
    censo_versao: str | None
    escolas_municipais: int
    alunos: int
    com_declaracao: int
    com_plano: int
    alta_recorrencia: int
    barreiras: list[BarreiraAnalitica]
    sintese: Sintese | None
    aviso_guardiao: str | None = None
