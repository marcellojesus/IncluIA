"""Sugestões de ações municipais pela IA (SPM-RF-02 e 05; RN-SPM-01, 04 e 06).

Por barreira, a IA recebe os números da rede (calculados pelo sistema), a regra da barreira, a base
normativa e as ações dos planos escolares aceitos, cada uma com uma referência [E<n>-A<m>] no lugar
do nome da escola. Ela propõe de 1 a 3 ações municipais que juntam necessidades comuns e diz quais
ações escolares cada uma atende, com cobertura total ou parcial. O validador recusa fonte fora do
contexto e referência inexistente; o sistema traduz as referências para escolas e itens e é ele
quem conta as escolas atendidas, nunca o texto da IA.
"""

import re
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.plano.servico import ErroPlano
from app.features.plano.sugestoes import _Mascara
from app.features.plano_municipal import base as base_rede
from app.features.plano_municipal.modelos import SugestaoMunicipal
from app.shared import ai_client
from app.shared.contexto_ia import INSTRUCOES_CITACAO, FatosDaRede, gerar_resposta_fundamentada, montar_contexto_rede
from app.shared.guardiao_lgpd import TextoBloqueado, juntar_protegidos, liberar_dados_publicos, proteger_para_ia, proteger_para_ia_ou_falhar

INSTRUCOES_MUNICIPAL = """Você apoia a secretaria municipal de educação a montar o Plano Estratégico Municipal de educação
inclusiva a partir dos Planos de Ação que as escolas da rede enviaram e a secretaria aceitou. Trabalhe só a barreira em foco.

Proponha de 1 a 3 ações municipais que resolvam a barreira de forma sistêmica para a rede, e não escola por escola:
junte necessidades comuns (compra ou contratação conjunta, profissional compartilhado entre escolas, formação para a
rede, ajuste de norma ou fluxo da secretaria, parceria com outro órgão). Para cada ação:
- "acao": o que a secretaria fará, em uma ou duas frases, no infinitivo.
- "justificativa": por que a ação atende às escolas, citando as ações escolares pelas referências [E1-A2].
- "atende": lista de {"ref": "E1-A2", "cobertura": "total" ou "parcial"} com as ações escolares atendidas; use "parcial"
  quando a ação municipal resolve só parte da ação escolar. Use apenas referências que aparecem no contexto.
- "responsavel": órgão ou setor (por exemplo, "secretaria municipal de educação"), nunca nome de pessoa.
- "prazo": prazo estimado. "horizonte": "LOA" (exercício corrente) ou "PPA" (plurianual).
- "custo_estimado": não invente valores; escreva "a estimar" ou a natureza do custo, sem número em reais.
- "premissas": o que precisa ser verdade para a ação dar certo. "prioridade": "alta", "media" ou "baixa".
- "fontes": identificadores da base normativa que fundamentam a ação, quando houver. "incertezas": o que não se sabe.
Não conte escolas nem calcule totais: o sistema faz isso. Linguagem factual e neutra, sem culpar pessoas ou escolas.
Se a base normativa entregue não sustentar alguma ação, diga isso em "lacunas".

Responda APENAS com um JSON válido, sem markdown, neste formato:
{"acoes": [{"acao": "...", "justificativa": "...", "atende": [{"ref": "E1-A1", "cobertura": "total"}], "responsavel": "...",
  "prazo": "...", "horizonte": "PPA", "custo_estimado": "a estimar", "premissas": "...", "prioridade": "alta",
  "fontes": ["identificador"], "incertezas": "..."}],
 "lacunas": ["..."]}"""


def pedido_municipal(codigo: str) -> str:
    return f"Proponha ações municipais para a barreira {codigo}, a partir das ações das escolas no contexto."


class Atendimento(BaseModel):
    ref: str = Field(max_length=12)
    cobertura: Literal["total", "parcial"] = "total"


class AcaoMunicipalIA(BaseModel):
    acao: str = Field(max_length=600)
    justificativa: str = Field(default="", max_length=1500)
    atende: list[Atendimento] = Field(default_factory=list, max_length=60)
    responsavel: str | None = Field(default=None, max_length=200)
    prazo: str | None = Field(default=None, max_length=100)
    horizonte: Literal["LOA", "PPA"] = "PPA"
    custo_estimado: str | None = Field(default=None, max_length=200)
    premissas: str | None = Field(default=None, max_length=1000)
    prioridade: Literal["alta", "media", "baixa"] = "media"
    fontes: list[str] = Field(default_factory=list, max_length=6)
    incertezas: str | None = Field(default=None, max_length=1000)


class RespostaMunicipal(BaseModel):
    acoes: list[AcaoMunicipalIA] = Field(min_length=1, max_length=3)
    lacunas: list[str] = Field(default_factory=list, max_length=5)


class ReferenciaInvalida(ai_client.RespostaReprovada):
    """A IA citou uma ação escolar que não está no contexto; a cadeia segue para o próximo provedor."""


_REF = r"\[?\bE\d{1,3}-A\d{1,3}\b\]?"
_REFERENCIA = re.compile(
    rf"(?P<prep>\s+(?:em|nas|nos|na|no|pelas|pelos|pela|pelo|de|das|dos)\b)?\s*\(?{_REF}(?:\s*(?:,|e)\s*{_REF})*\)?", re.IGNORECASE
)


def _sem_referencias(texto: str | None) -> str | None:
    """"expressas em [E1-A1] e [E1-A2]." → "expressas nos planos das escolas."; sem preposição, a referência só sai."""
    if not texto:
        return texto
    limpo = _REFERENCIA.sub(lambda m: " nos planos das escolas" if m.group("prep") else "", texto)
    return re.sub(r"\s+([.,;:])", r"\1", re.sub(r"\s{2,}", " ", limpo)).strip()


def _linha(item: base_rede.ItemDaRede) -> str:
    detalhes = "; ".join(p for p in (
        f"horizonte {item.horizonte}", item.responsavel and f"responsável {item.responsavel}", item.prazo and f"prazo {item.prazo}",
        item.custo_estimado and f"custo {item.custo_estimado}",
    ) if p)
    return f"[{item.ref}] {item.acao} ({detalhes})"


async def sugerir(sessao: Session, *, co_municipio: int, codigo: str, orientacao: str | None) -> tuple[list[SugestaoMunicipal], bool]:
    """Levanta ErroPlano (barreira, sem ações escolares, texto bloqueado) e RuntimeError (IA indisponível)."""
    base = base_rede.montar(sessao, co_municipio)
    barreira = base.barreira(codigo)
    if barreira is None:
        raise ErroPlano("Barreira não identificada na rede.", 404)
    if not barreira.itens:
        raise ErroPlano("Nenhum plano escolar aceito traz ação para esta barreira. Escreva a ação municipal diretamente.", 409)

    # Cada ação escolar passa de novo pelo Guardião; a que bloquear fica de fora (e vira lacuna).
    # Nomes da rede e códigos INEP também saem (pendência 16).
    locais = censo.locais_da_rede(co_municipio)
    protegidas, fora, mascaradas = [], 0, 0
    for item in barreira.itens:
        resultado = proteger_para_ia(_linha(item), locais)
        if resultado.texto_protegido is None:
            fora += 1
        else:
            mascaradas += bool(resultado.trechos)
            protegidas.append(resultado.texto_protegido)
    if not protegidas:
        raise ErroPlano("As ações escolares desta barreira têm dado sensível e não podem ir ao assistente.", 409)
    referencias = {i.ref for i in barreira.itens}

    mensagens = [{"role": "user", "content": liberar_dados_publicos(pedido_municipal(codigo))}]
    if orientacao and orientacao.strip():
        try:
            mensagens.append({"role": "user", "content": proteger_para_ia_ou_falhar(orientacao.strip()[:1000], locais)})
        except TextoBloqueado as erro:
            raise ErroPlano(str(erro)) from None

    fatos = FatosDaRede(
        escolas_municipais=len(base.escolas), escolas_com_barreira=len(barreira.escolas_com_barreira),
        escolas_com_plano_aceito=len(base.planos),
    )
    try:
        contexto = await montar_contexto_rede(codigo, fatos, juntar_protegidos(protegidas, "\n"))
        sistema = juntar_protegidos([liberar_dados_publicos(INSTRUCOES_MUNICIPAL), liberar_dados_publicos(INSTRUCOES_CITACAO), contexto.texto])
    except TextoBloqueado:
        raise ErroPlano("O contexto da rede tem dado sensível; revise os planos escolares.", 409) from None

    def conferir_referencias(resposta: RespostaMunicipal) -> None:
        if any(a.ref.strip("[]") not in referencias for acao in resposta.acoes for a in acao.atende):
            raise ReferenciaInvalida("referência a ação escolar fora do contexto")

    resposta, _modelo = await gerar_resposta_fundamentada(sistema, mensagens, RespostaMunicipal, contexto, validar_extra=conferir_referencias)

    mascarar = _Mascara()
    lacunas = [_sem_referencias(l) for l in (mascarar(l) for l in resposta.lacunas) if l]
    if fora:
        lacunas.append(f"{fora} ação(ões) escolar(es) com dado sensível ficaram fora da análise.")
    novas = []
    for a in resposta.acoes:
        acao = mascarar(a.acao)
        if not acao:
            continue
        escolas: dict[int, dict] = {}
        for atendimento in a.atende:
            item = base.item(atendimento.ref.strip("[]"))
            e = escolas.setdefault(item.co_entidade, {"co_entidade": item.co_entidade, "item_ids": [], "cobertura": "total"})
            e["item_ids"].append(item.item_id)
            if atendimento.cobertura == "parcial":
                e["cobertura"] = "parcial"
        sugestao = SugestaoMunicipal(co_municipio=co_municipio, codigo=codigo, conteudo={
            # A numeração [E<n>-A<m>] muda quando outras escolas têm plano aceito: as escolas ficam na lista estruturada.
            "acao": _sem_referencias(acao), "justificativa": _sem_referencias(mascarar(a.justificativa)), "responsavel": mascarar.responsavel(a.responsavel),
            "prazo": mascarar(a.prazo), "horizonte": a.horizonte, "custo_estimado": mascarar(a.custo_estimado) or "a estimar",
            "premissas": _sem_referencias(mascarar(a.premissas)), "prioridade": a.prioridade, "fontes": [f.strip("[]") for f in a.fontes],
            "incertezas": _sem_referencias(mascarar(a.incertezas)), "lacunas": lacunas, "escolas": list(escolas.values()),
        })
        sessao.add(sugestao)
        novas.append(sugestao)
    sessao.commit()
    # Aviso também quando o Guardião mascarou trechos das ações escolares que foram à IA.
    return novas, mascarar.alterou or mascaradas > 0
