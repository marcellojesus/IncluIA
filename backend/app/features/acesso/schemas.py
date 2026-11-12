from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SolicitacaoDiretor(_Camel):
    nome: str = Field(max_length=200)
    email: str = Field(max_length=254)
    co_entidade: int


class PedidoCodigo(_Camel):
    email: str = Field(max_length=254)


class Entrada(_Camel):
    email: str = Field(max_length=254)
    codigo: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class Mensagem(_Camel):
    mensagem: str


class RespostaEntrada(_Camel):
    situacao: str
    token: str | None = None
    mensagem: str = ""


class Escopo(_Camel):
    co_entidade: int | None = None
    escola: str | None = None
    co_municipio: int | None = None
    municipio: str | None = None
    uf: str | None = None


class Eu(_Camel):
    id: str
    nome: str
    email: str
    papel: str
    escopo: Escopo


class Decisao(_Camel):
    categoria: str = Field(max_length=30)
    """Motivo em lista fechada (servico.CATEGORIAS); é o que vai para a auditoria."""
    texto: str = Field(max_length=1000)
    """Método de verificação (aprovar) ou justificativa (rejeitar, suspender, reativar, revogar)."""


class SolicitacaoVinculo(_Camel):
    id: str
    nome: str
    email: str
    email_confirmado: bool
    co_entidade: int
    escola: str
    estado: str
    categoria: str | None = None
    criado_em: datetime
    decidido_em: datetime | None = None
    metodo_verificacao: str | None = None
    justificativa: str | None = None


class ContaDaGestao(_Camel):
    """Uma linha da tela "Contas da Gestão Ativa" do administrador: quem é, por qual e-mail e onde."""

    papel: str
    nome: str
    email: str
    email_confirmado: bool
    estado: str
    """Estado do vínculo mais recente (pendente, aprovado, suspenso, rejeitado, revogado)."""
    pedido_confirmado: bool
    """Diretor: usou o código deste pedido. Sem isso o pedido não aparece para a secretaria."""
    co_municipio: int
    municipio: str
    uf: str
    co_entidade: int | None = None
    escola: str | None = None
    criado_em: datetime


class NovoSecretario(_Camel):
    nome: str = Field(max_length=200)
    email: str = Field(max_length=254)
    co_municipio: int
    categoria: str = Field(max_length=30)
    metodo_verificacao: str = Field(max_length=1000)
