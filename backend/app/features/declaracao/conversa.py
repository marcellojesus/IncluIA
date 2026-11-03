"""Conversa com a IA para formular um obstáculo (DO-RF-02 e DO-RF-03; RN-DO-02 e RN-DO-08).

A IA pergunta, aprofunda e propõe um texto formal; só o diretor registra. Cada mensagem do diretor
passa pelo Guardião LGPD antes de ser gravada e enviada (AD-05). O contexto vem do montador do
AD-08 com foco na barreira, e o validador recusa referência legal fora do contexto entregue.
"""

from datetime import timedelta

from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.declaracao.modelos import MensagemObstaculo
from app.features.declaracao.servico import ErroDeclaracao, _barreira, estado
from app.shared.banco_gestao import agora
from app.shared.contexto_ia import gerar_resposta_fundamentada
from app.shared.contexto_ia.montador import montar_contexto
from app.shared.guardiao_lgpd import TextoBloqueado, juntar_protegidos, liberar_dados_publicos, proteger, proteger_para_ia, proteger_para_ia_ou_falhar

MAX_MENSAGENS_DO_DIRETOR = 8
TAMANHO_MAXIMO_MENSAGEM = 2000
PRAZO_CONVERSA_PARADA = timedelta(days=30)
_FALA_REMOVIDA = "[fala anterior removida pelo Guardião LGPD]"

INSTRUCOES_REGISTRO = """Você é o assistente de registro da Declaração de Obstáculos da Escola Sem Barreiras.
Converse com a equipe da escola sobre UMA barreira identificada no Censo (a barreira em foco, abaixo) para entender
o obstáculo que impede a escola de superá-la.

Como conduzir:
- Faça uma pergunta por vez, curta e concreta. Comece pelo que impede a escola de superar a barreira; depois pergunte
  se a escola formalizou o pedido ou buscou apoio da secretaria e o que aconteceu.
- Com duas ou três respostas, proponha o texto formal em "texto_formal" e um resumo de uma linha em "resumo".
- O texto formal começa com "A gestão escolar relata que", é factual e neutro, descreve fatos e tentativas da escola e
  não atribui culpa a pessoas nem a órgãos.
- Use só o que a equipe contou; não invente datas, números, nomes ou fatos. Se faltar algo, pergunte.
- Não inclua nomes de pessoas nem nada que identifique estudantes ou profissionais. Marcadores como [NOME], [TURMA]
  ou [escola ou município da rede] são dados protegidos: não tente adivinhar o que escondem e não os repita no texto
  formal; no lugar do local, escreva "a escola" ou "o município".
- Não cite leis, decretos ou artigos no texto formal; ele registra a situação da escola.
- Você não registra nada: quem confirma é a equipe da escola.

Responda APENAS com um JSON válido, sem markdown, neste formato:
{"resposta": "sua próxima pergunta ou comentário, em português do Brasil",
 "texto_formal": "texto proposto ou null se ainda faltar informação",
 "resumo": "resumo de uma linha ou null"}"""

# Primeira pergunta de cada barreira: texto fixo (não gasta cota de IA), exibido na tela e enviado
# à IA como a primeira fala do assistente, para ela saber o que já foi perguntado.
PERGUNTAS_INICIAIS = {
    "B-I-01": "O que tem impedido a escola de oferecer o Atendimento Educacional Especializado (AEE)?",
    "B-II-01": "O que tem impedido a escola de ter rampas nas áreas de circulação?",
    "B-II-02": "O que tem impedido a escola de ter banheiro acessível?",
    "B-II-03": "O que tem impedido a escola de instalar corrimão e guarda-corpos?",
    "B-II-04": "O que tem impedido a escola de instalar pisos táteis?",
    "B-II-05": "O que tem impedido a escola de ter sinalização visual?",
    "B-II-06": "O que tem impedido a escola de ter sinalização sonora?",
    "B-II-07": "O que tem impedido a escola de ter elevador? Se o prédio for térreo, você pode informar isso como divergência com o dado do Censo.",
    "B-III-01": "O que tem impedido a escola de contar com tradutor e intérprete de Libras?",
    "B-III-02": "O que tem impedido a escola de contar com revisor de texto em Braille?",
    "B-IV-01": "O que tem levado parte das matrículas da educação especial a ficar em classes exclusivas, e não em classe comum?",
}


def pergunta_inicial(codigo: str) -> str:
    return PERGUNTAS_INICIAIS.get(codigo, "O que tem impedido a escola de superar esta barreira?")


INSTRUCAO_FORMALIZAR = (
    "Com o que já foi contado, proponha agora o texto formal do obstáculo em \"texto_formal\" e o resumo em "
    "\"resumo\". Se faltar algo essencial, diga o que falta em \"resposta\"."
)


class RespostaRegistro(BaseModel):
    # Pode vir vazia quando a IA só entrega a proposta de texto formal (visto com o Groq).
    resposta: str = Field(default="", max_length=2000)
    texto_formal: str | None = Field(default=None, max_length=3000)
    resumo: str | None = Field(default=None, max_length=300)


def mensagens(sessao: Session, co_entidade: int, codigo: str) -> list[MensagemObstaculo]:
    return list(sessao.scalars(
        select(MensagemObstaculo)
        .where(MensagemObstaculo.co_entidade == co_entidade, MensagemObstaculo.codigo == codigo)
        .order_by(MensagemObstaculo.criado_em)
    ))


def reiniciar(sessao: Session, co_entidade: int, codigo: str) -> None:
    sessao.execute(delete(MensagemObstaculo).where(MensagemObstaculo.co_entidade == co_entidade, MensagemObstaculo.codigo == codigo))
    sessao.commit()


def _mascarado(texto: str | None) -> str | None:
    """Texto vindo da IA, mascarado para exibição; se tiver dado de risco alto, não é mostrado."""
    if not texto:
        return None
    resultado = proteger(texto)
    return None if resultado.bloqueado else resultado.texto_mascarado


async def conversar(sessao: Session, *, co_entidade: int, codigo: str, mensagem: str | None, formalizar: bool) -> RespostaRegistro:
    """Levanta ErroDeclaracao (barreira, texto bloqueado ou limite) e RuntimeError (IA indisponível)."""
    _barreira(estado(sessao, co_entidade), codigo)
    historico = mensagens(sessao, co_entidade, codigo)
    locais = censo.locais_da_escola(co_entidade)  # nomes da rede não vão à IA (pendência 16)
    do_diretor = sum(1 for m in historico if m.papel == "diretor")

    nova = None
    if mensagem and mensagem.strip():
        if do_diretor >= MAX_MENSAGENS_DO_DIRETOR:
            raise ErroDeclaracao("A conversa já tem informação suficiente. Peça o texto formal ou escreva-o diretamente.", 409)
        if len(mensagem.strip()) > TAMANHO_MAXIMO_MENSAGEM:
            raise ErroDeclaracao(f"A mensagem passa de {TAMANHO_MAXIMO_MENSAGEM} caracteres. Divida em respostas menores.")
        try:
            nova = proteger_para_ia_ou_falhar(mensagem.strip(), locais)
        except TextoBloqueado as erro:
            raise ErroDeclaracao(str(erro)) from None
    elif not formalizar:
        raise ErroDeclaracao("Escreva sua resposta.")
    if formalizar and do_diretor == 0 and nova is None:
        raise ErroDeclaracao("Conte primeiro a situação da escola.", 409)

    # Histórico: as falas do diretor já foram gravadas mascaradas; passam de novo pelo guardião
    # porque é o único caminho para virar TextoProtegido.
    conversa = [{"role": "assistant", "content": liberar_dados_publicos(pergunta_inicial(codigo))}]
    ultima_fala = None
    for m in historico:
        # Fala antiga que uma regra nova do guardião bloqueia vira marcador fixo, em vez de sumir.
        protegida = proteger_para_ia(m.texto, locais).texto_protegido or liberar_dados_publicos(_FALA_REMOVIDA)
        conversa.append({"role": "user" if m.papel == "diretor" else "assistant", "content": protegida})
        if m.papel == "diretor":
            ultima_fala = protegida
    if nova is not None:
        conversa.append({"role": "user", "content": nova})
    if formalizar:
        conversa.append({"role": "user", "content": liberar_dados_publicos(INSTRUCAO_FORMALIZAR)})

    # A busca normativa usa a fala do diretor, nunca o texto da instrução.
    pergunta = nova or ultima_fala
    contexto = await montar_contexto(co_entidade, pergunta=pergunta, barreiras_foco=[codigo])
    sistema = juntar_protegidos([liberar_dados_publicos(INSTRUCOES_REGISTRO), contexto.texto])

    resposta, _modelo = await gerar_resposta_fundamentada(sistema, conversa, RespostaRegistro, contexto)

    if nova is not None:
        sessao.add(MensagemObstaculo(co_entidade=co_entidade, codigo=codigo, papel="diretor", texto=str(nova)))
    # A IA só viu texto mascarado, mas pode inventar um nome ou adivinhar um marcador: a fala dela
    # também é mascarada antes de gravar e exibir (revisão do AgLGPD).
    fala_da_ia = _mascarado(resposta.resposta.strip()) or ("Proponho o texto formal abaixo para sua revisão." if resposta.texto_formal else "")
    resposta.resposta = fala_da_ia or "Pode contar um pouco mais sobre a situação?"
    sessao.add(MensagemObstaculo(co_entidade=co_entidade, codigo=codigo, papel="ia", texto=resposta.resposta))
    sessao.commit()
    return RespostaRegistro(
        resposta=resposta.resposta, texto_formal=_mascarado(resposta.texto_formal), resumo=_mascarado(resposta.resumo)
    )


def limpar_conversas_paradas(sessao: Session) -> int:
    """Apaga conversas sem mensagem nova há mais de 30 dias (revisão do AgLGPD, retenção). A posição
    confirmada guarda só o relato original; conversa abandonada não precisa ficar."""
    corte = agora() - PRAZO_CONVERSA_PARADA
    ultimas = (
        select(MensagemObstaculo.co_entidade, MensagemObstaculo.codigo, func.max(MensagemObstaculo.criado_em).label("ultima"))
        .group_by(MensagemObstaculo.co_entidade, MensagemObstaculo.codigo)
        .subquery()
    )
    paradas = sessao.execute(select(ultimas.c.co_entidade, ultimas.c.codigo).where(ultimas.c.ultima < corte)).all()
    for co_entidade, codigo in paradas:
        sessao.execute(
            delete(MensagemObstaculo)
            .where(MensagemObstaculo.co_entidade == co_entidade, MensagemObstaculo.codigo == codigo)
            .execution_options(synchronize_session=False)
        )
    sessao.commit()
    return len(paradas)


def total_de_mensagens(sessao: Session, co_entidade: int) -> int:
    return sessao.scalar(select(func.count()).select_from(MensagemObstaculo).where(MensagemObstaculo.co_entidade == co_entidade))
