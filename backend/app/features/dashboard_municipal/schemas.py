from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EixoRede(_Camel):
    eixo: str
    nome: str
    peso: int
    """Peso do eixo no score, em % (metodologia_score.md §8)."""
    score: float
    faixa: str


class Cobertura(_Camel):
    escolas_municipais: int
    escolas_com_barreiras: int
    """Escolas da rede com ao menos uma barreira da metodologia no Censo: base das três contagens abaixo."""
    com_declaracao: int
    com_plano_enviado: int
    aguardando_analise: int
    plano_mais_antigo: datetime | None = None


class EscolaPrioritaria(_Camel):
    co_entidade: int
    escola: str
    score: float
    faixa: str
    alunos_esp: int | None
    """None abaixo de LIMIAR_CELULA_PEQUENA, só para a tela não exibir o número. Não é proteção: o
    peso, o score e o total da rede permitem recalculá-lo, o que é aceito porque o secretário é o
    controlador dos dados da própria rede (revisão do AgLGPD de 2026-10-27)."""
    peso: float
    """Pontos que a escola tira do score da rede: (10 − score) × alunos ESP ÷ alunos ESP da rede."""
    eixos_criticos: list[str]
    declaracao: bool
    """Andamento, separado da gravidade (RN-DMS-05)."""
    plano: str | None
    """Estado da última versão enviada do Plano de Ação; None se a escola nunca enviou."""


class DashboardMunicipal(_Camel):
    municipio: str
    uf: str
    censo_versao: str | None
    score: float | None
    """Score da rede municipal, ponderado por alunos ESP (RN-03 do score); None se a rede não tem escolas."""
    faixa: str | None
    ponderacao: Literal["alunos_esp", "media_simples"]
    alunos_esp: int
    score_municipio: float | None
    """Score do município com todas as redes: o mesmo da página pública."""
    escolas_municipio: int
    eixos: list[EixoRede]
    """Do mais crítico ao mais adequado (RN-DMS-02)."""
    cobertura: Cobertura
    prioridades: list[EscolaPrioritaria]
    escolas_no_ranking: int
    escolas_sem_alunos_esp: int
    """Escolas sem matrícula da educação especial: não pesam no score da rede e ficam fora do ranking."""
