"""Sugestões de ação pela IA (PAE-RF-01 a 03; RN-PAE-01 a 03 e 05).

Para uma barreira da Declaração usada como base, a IA recebe a posição registrada pela escola (já
mascarada), o contexto do montador do AD-08 com foco na barreira e, se houver, a orientação do
diretor (passada pelo Guardião LGPD). Ela propõe de 1 a 3 ações; o validador recusa fonte fora do
contexto e exige lacuna declarada quando não há norma de apoio. Barreira "sem relato" não recebe
proposta automática: é lacuna da Declaração.
"""

from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.plano.modelos import SugestaoPlano
from app.features.plano.servico import ErroPlano, estado, item_da_base
from app.shared.contexto_ia import INSTRUCOES_CITACAO, gerar_resposta_fundamentada
from app.shared.contexto_ia.montador import RegistroDaEscola, montar_contexto
from app.shared.guardiao_lgpd import TextoBloqueado, TextoProtegido, juntar_protegidos, liberar_dados_publicos, proteger, proteger_para_ia, proteger_para_ia_ou_falhar

INSTRUCOES_PLANO = """Você apoia a direção de uma escola pública municipal a montar o Plano de Ação Escolar a partir da
Declaração de Obstáculos que a escola emitiu. Trabalhe só a barreira em foco e a posição que a escola registrou para ela.

Proponha de 1 a 3 ações concretas e viáveis para superar a barreira, considerando o obstáculo ou a divergência relatados:
- "acao": o que fazer, em uma ou duas frases, no infinitivo.
- "relacao": como a ação responde ao obstáculo ou à divergência registrados pela escola.
- "responsavel": cargo ou órgão (por exemplo, "direção da escola", "secretaria municipal de educação"), nunca nome de pessoa.
- "prazo": prazo estimado (por exemplo, "até 6 meses").
- "horizonte": "LOA" se cabe no exercício corrente (ação administrativa, de baixo custo ou já prevista);
  "PPA" se é estrutural e plurianual (obra, contratação permanente, compra de grande porte).
- "custo_estimado": não invente valores. Escreva "a estimar" ou, se der para indicar, a natureza do custo (por exemplo,
  "custo de contratação de profissional"), sem número em reais.
- "premissas": o que precisa ser verdade para a ação dar certo.
- "fontes": identificadores dos trechos da base normativa que fundamentam a ação, quando houver.
- "incertezas": o que você não sabe e a escola precisa confirmar.
Linguagem factual e neutra, sem culpar pessoas ou órgãos. Não use dados de outras escolas. Não identifique estudantes.
Se a base normativa entregue não sustentar alguma ação, diga isso em "lacunas".

Responda APENAS com um JSON válido, sem markdown, neste formato:
{"sugestoes": [{"acao": "...", "relacao": "...", "responsavel": "...", "prazo": "...", "horizonte": "LOA",
  "custo_estimado": "a estimar", "premissas": "...", "fontes": ["identificador"], "incertezas": "..."}],
 "lacunas": ["..."]}"""

_ROTULOS = {"obstaculo": "obstáculo relatado", "divergencia": "divergência com o dado do Censo"}


def pedido_de_sugestoes(codigo: str) -> str:
    return f"Proponha ações para a barreira {codigo}, a partir da posição registrada pela escola."


class SugestaoIA(BaseModel):
    acao: str = Field(max_length=600)
    relacao: str = Field(default="", max_length=1000)
    responsavel: str | None = Field(default=None, max_length=200)
    prazo: str | None = Field(default=None, max_length=100)
    horizonte: Literal["LOA", "PPA"] = "PPA"
    custo_estimado: str | None = Field(default=None, max_length=200)
    premissas: str | None = Field(default=None, max_length=1000)
    fontes: list[str] = Field(default_factory=list, max_length=6)
    incertezas: str | None = Field(default=None, max_length=1000)


class RespostaPlano(BaseModel):
    sugestoes: list[SugestaoIA] = Field(min_length=1, max_length=3)
    lacunas: list[str] = Field(default_factory=list, max_length=5)


class _Mascara:
    """Texto da IA mascarado antes de gravar; com dado de risco alto, o campo não é guardado.
    Registra se algo foi trocado ou descartado, para avisar o diretor (AD-05: mascarar e avisar)."""

    def __init__(self) -> None:
        self.alterou = False

    def __call__(self, texto: str | None) -> str | None:
        if not texto:
            return None
        resultado = proteger(texto)
        if resultado.trechos:
            self.alterou = True
        return None if resultado.bloqueado else resultado.texto_mascarado

    def responsavel(self, texto: str | None) -> str | None:
        """Cargo ou órgão; com nome de pessoa, o campo fica vazio para o diretor preencher."""
        if not texto:
            return None
        if proteger(texto).trechos:
            self.alterou = True
            return None
        return texto


INSTRUCAO_AJUSTE = """A direção da escola pediu um ajuste numa proposta anterior para a mesma barreira. Reescreva essa proposta
atendendo ao pedido, mantendo o que não foi pedido para mudar e as mesmas regras acima (fontes só do contexto,
custo sem valor em reais, responsável como cargo ou órgão). Se o pedido não couber na base normativa entregue, diga
isso em "lacunas". Devolva exatamente UMA sugestão em "sugestoes"."""


def pedido_de_ajuste(codigo: str) -> str:
    return f"Reescreva a proposta anterior para a barreira {codigo} conforme o pedido da direção."


async def _preparar(sessao: Session, co_entidade: int, codigo: str, instrucoes: list):
    """Posição da Declaração (mascarada) e contexto AD-08 da barreira. Devolve (estado, sistema, contexto)."""
    atual = estado(sessao, co_entidade)
    item = item_da_base(atual, codigo)
    if item.posicao not in _ROTULOS or not item.texto:
        raise ErroPlano("A escola não apresentou relato sobre esta barreira na Declaração: fica como lacuna, sem sugestão automática.", 409)
    registro = proteger_para_ia(
        f"Posição registrada na Declaração v{atual.base.versao} para {codigo} ({_ROTULOS[item.posicao]}): {item.texto}",
        censo.locais_da_escola(co_entidade),  # nomes da rede não vão à IA (pendência 16)
    ).texto_protegido
    if registro is None:
        raise ErroPlano("O texto da posição tem dado sensível; retifique a Declaração antes de pedir sugestões.", 409)
    try:
        contexto = await montar_contexto(
            co_entidade, pergunta=registro, barreiras_foco=[codigo], registros=[RegistroDaEscola(co_entidade, registro)]
        )
        sistema = juntar_protegidos([*instrucoes, liberar_dados_publicos(INSTRUCOES_CITACAO), contexto.texto])
    except TextoBloqueado:
        raise ErroPlano("O contexto da escola tem dado sensível; retifique a Declaração antes de pedir sugestões.", 409) from None
    return atual, sistema, contexto


def _texto_do_diretor(texto: str, co_entidade: int) -> TextoProtegido:
    try:
        return proteger_para_ia_ou_falhar(texto.strip()[:1000], censo.locais_da_escola(co_entidade))
    except TextoBloqueado as erro:
        raise ErroPlano(str(erro)) from None


def _gravar(sessao: Session, co_entidade: int, codigo: str, versao_base: int, resposta: RespostaPlano, limite: int, ajustada: bool) -> tuple[list[SugestaoPlano], bool]:
    mascarar = _Mascara()
    novas = []
    lacunas = [l for l in (mascarar(l) for l in resposta.lacunas) if l]
    for s in resposta.sugestoes[:limite]:
        acao = mascarar(s.acao)
        if not acao:
            continue
        sugestao = SugestaoPlano(
            co_entidade=co_entidade, codigo=codigo, declaracao_versao=versao_base,
            conteudo={
                "acao": acao, "relacao": mascarar(s.relacao), "responsavel": mascarar.responsavel(s.responsavel), "prazo": mascarar(s.prazo),
                "horizonte": s.horizonte, "custo_estimado": mascarar(s.custo_estimado) or "a estimar",
                "premissas": mascarar(s.premissas), "fontes": [f.strip("[]") for f in s.fontes], "incertezas": mascarar(s.incertezas),
                "lacunas": lacunas, "ajustada": ajustada,
            },
        )
        sessao.add(sugestao)
        novas.append(sugestao)
    return novas, mascarar.alterou


async def sugerir(sessao: Session, *, co_entidade: int, codigo: str, orientacao: str | None) -> tuple[list[SugestaoPlano], bool]:
    """Devolve as sugestões e se algum trecho da resposta foi mascarado ou descartado.
    Levanta ErroPlano (barreira, lacuna, texto bloqueado) e RuntimeError (IA indisponível)."""
    mensagens = [{"role": "user", "content": liberar_dados_publicos(pedido_de_sugestoes(codigo))}]
    if orientacao and orientacao.strip():
        mensagens.append({"role": "user", "content": _texto_do_diretor(orientacao, co_entidade)})
    atual, sistema, contexto = await _preparar(sessao, co_entidade, codigo, [liberar_dados_publicos(INSTRUCOES_PLANO)])
    resposta, _modelo = await gerar_resposta_fundamentada(sistema, mensagens, RespostaPlano, contexto)
    novas, alterou = _gravar(sessao, co_entidade, codigo, atual.base.versao, resposta, limite=3, ajustada=False)
    sessao.commit()
    return novas, alterou


def _proposta_anterior(conteudo: dict) -> str:
    rotulos = (("acao", "Ação"), ("relacao", "Relação com o obstáculo"), ("responsavel", "Responsável"), ("prazo", "Prazo"),
               ("horizonte", "Horizonte"), ("custo_estimado", "Custo estimado"), ("premissas", "Premissas"), ("incertezas", "Incertezas"))
    linhas = [f"{r}: {conteudo[c]}" for c, r in rotulos if conteudo.get(c)]
    if conteudo.get("fontes"):
        linhas.append("Fontes: " + ", ".join(conteudo["fontes"]))
    return "Proposta anterior:\n" + "\n".join(linhas)


async def ajustar(sessao: Session, *, co_entidade: int, sugestao_id: str, pedido: str) -> tuple[SugestaoPlano, bool]:
    """PAE-RF-02: a direção pede um ajuste numa sugestão; a IA devolve uma nova versão dela, que
    substitui a anterior na tela. A anterior fica como "substituida". Só a escolha do diretor leva ao plano."""
    sugestao = sessao.get(SugestaoPlano, sugestao_id)
    if sugestao is None or sugestao.co_entidade != co_entidade or sugestao.estado != "pendente":
        raise ErroPlano("Sugestão não encontrada.", 404)
    if not pedido or len(pedido.strip()) < 3:
        raise ErroPlano("Diga o que ajustar na sugestão.")
    pedido_protegido = _texto_do_diretor(pedido, co_entidade)
    # A proposta veio da IA e já foi mascarada ao ser gravada; passa de novo pelo Guardião antes de voltar à IA.
    anterior = proteger_para_ia(_proposta_anterior(sugestao.conteudo), censo.locais_da_escola(co_entidade)).texto_protegido
    if anterior is None:
        raise ErroPlano("A sugestão anterior não pode ser reenviada ao assistente. Peça uma nova proposta.", 409)
    mensagens = [
        {"role": "user", "content": liberar_dados_publicos(pedido_de_ajuste(sugestao.codigo))},
        {"role": "user", "content": anterior},
        {"role": "user", "content": pedido_protegido},
    ]
    atual, sistema, contexto = await _preparar(
        sessao, co_entidade, sugestao.codigo, [liberar_dados_publicos(INSTRUCOES_PLANO), liberar_dados_publicos(INSTRUCAO_AJUSTE)]
    )
    resposta, _modelo = await gerar_resposta_fundamentada(sistema, mensagens, RespostaPlano, contexto)
    novas, alterou = _gravar(sessao, co_entidade, sugestao.codigo, atual.base.versao, resposta, limite=1, ajustada=True)
    if not novas:
        sessao.rollback()
        raise ErroPlano("O assistente não devolveu uma proposta utilizável. Tente reformular o pedido.", 409)
    novas[0].criado_em = sugestao.criado_em  # aparece no lugar da anterior
    sugestao.estado = "substituida"
    sessao.commit()
    return novas[0], alterou
