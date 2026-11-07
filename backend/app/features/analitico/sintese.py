"""Síntese da rede pela IA (SAB-RF-02 e 06; RN-SAB-02, 03 e 05).

A IA recebe, por barreira, proporções arredondadas calculadas pelo sistema e os resumos das posições
das Declarações emitidas, cada um com uma referência [R<n>] no lugar da escola. Nem o município, nem
as escolas, nem contagens exatas vão à IA (revisão do AgLGPD de 2026-10-27: o conjunto de contagens
exatas identifica o município nos microdados do Censo). Ela separa observação, hipótese e
recomendação, e cada achado cita as barreiras e os relatos em que se apoia; o validador recusa código
ou referência fora do contexto, e a cadeia passa ao próximo provedor. O texto da IA não conta nada:
as contagens da tela vêm de `base.py`.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.analitico import base as base_rede
from app.features.analitico.modelos import SinteseAnalitica
from app.features.plano.sugestoes import _Mascara
from app.shared import ai_client
from app.shared.contexto_ia.barreiras import CLASSE_EXCLUSIVA
from app.shared.guardiao_lgpd import TextoBloqueado, delimitar, juntar_protegidos, liberar_dados_publicos, proteger_para_ia

RELATOS_POR_BARREIRA = 8
"""Resumos de relato enviados por barreira; as barreiras vão na ordem de alunos atingidos."""
POUCAS_ESCOLAS = 3
"""Abaixo disto a contagem vai à IA só como "poucas escolas" ou "algumas" (revisão do AgLGPD)."""
GUARDAR = 5
"""Sínteses guardadas por município; as mais antigas são apagadas (retenção provisória, pendência de AD-03)."""
REAPROVEITAR_POR = timedelta(hours=1)
"""Sem registro novo, um pedido dentro deste prazo devolve a síntese guardada, sem chamar a IA."""

INSTRUCOES_ANALITICO = """Você apoia a secretaria municipal de educação a ler os registros da rede sobre as barreiras à educação
inclusiva. Recebe, por barreira, proporções calculadas pelo sistema a partir do Censo Escolar, das Declarações de Obstáculos
emitidas pelas escolas e dos Planos de Ação enviados, e resumos das posições das escolas, cada um com uma referência [R1].

Escreva de 3 a 10 achados sobre a rede como um todo. Cada achado tem um "tipo":
- "observacao": o que os dados e relatos mostram, sem interpretar;
- "hipotese": uma explicação possível para um padrão, que a secretaria precisa verificar;
- "recomendacao": o que a secretaria pode examinar ou fazer, sem valores em reais e sem prazos inventados.
Em cada achado, "barreiras" lista os códigos (como B-I-01) e "relatos" as referências [R1] em que ele se apoia. Use só
códigos e referências que aparecem no contexto. Não escreva números de escolas ou de alunos e não faça contas: o sistema
mostra as contagens ao lado do seu texto. Barreira presente em quase todas as escolas sugere resposta da rede, não de cada
escola, mas diga isso como hipótese. Escola sem relato ou sem plano não é escola sem dificuldade. Linguagem factual e
neutra, sem culpar pessoas, escolas ou órgãos. Em "limitacoes", diga o que a base não permite afirmar (por exemplo, poucas
Declarações emitidas).

Responda APENAS com um JSON válido, sem markdown, neste formato:
{"achados": [{"tipo": "observacao", "texto": "...", "barreiras": ["B-I-01"], "relatos": ["R1"]}], "limitacoes": ["..."]}"""

PEDIDO_ANALITICO = "Escreva a síntese da rede a partir do contexto."
_CABECALHO_RELATOS = "## Resumos das posições das escolas"

_ROTULO_POSICAO = {"obstaculo": "obstáculo relatado", "divergencia": "divergência com o Censo"}


class Achado(BaseModel):
    tipo: Literal["observacao", "hipotese", "recomendacao"]
    texto: str = Field(max_length=900)
    barreiras: list[str] = Field(default_factory=list, max_length=11)
    relatos: list[str] = Field(default_factory=list, max_length=12)


class RespostaAnalitica(BaseModel):
    achados: list[Achado] = Field(min_length=1, max_length=12)
    limitacoes: list[str] = Field(default_factory=list, max_length=5)


class ReferenciaInvalida(ai_client.RespostaReprovada):
    """A IA citou barreira ou relato fora do contexto; a cadeia segue para o próximo provedor."""


class ContextoBloqueado(Exception):
    """Os relatos, juntos, formam dado de risco alto para o Guardião; nada foi à IA."""


_REF_RELATO = re.compile(r"\s*\(?\[?\bR\d{1,3}\b\]?(?:\s*(?:,|e)\s*\[?\bR\d{1,3}\b\]?)*\)?")


def _sem_referencias(texto: str | None) -> str | None:
    if not texto:
        return texto
    limpo = _REF_RELATO.sub("", texto)
    return re.sub(r"\s+([.,;:])", r"\1", re.sub(r"\s{2,}", " ", limpo)).strip()


def _proporcao(parte: int, total: int) -> str:
    """Percentual arredondado a 5 pontos; abaixo de POUCAS_ESCOLAS, só "poucas escolas"."""
    if parte == 0:
        return "nenhuma escola"
    if parte < POUCAS_ESCOLAS:
        return "poucas escolas"
    return f"cerca de {max(5, round(100 * parte / total / 5) * 5)}% das escolas"


def _quantas(n: int) -> str:
    return "nenhuma" if n == 0 else "algumas" if n < POUCAS_ESCOLAS else "várias"


def renderizar_rede(rede: base_rede.Rede) -> str:
    """Rede sem município, escolas, edição do Censo nem contagens exatas."""
    total = len(rede.escolas)
    linhas = [
        "## Rede municipal (dados calculados pelo sistema; não reavalie nem faça contas)",
        f"Declaração de Obstáculos emitida: {_proporcao(rede.com_declaracao, total)}. "
        f"Plano de Ação enviado: {_proporcao(rede.com_plano, total)}.",
        "",
        "## Barreiras, da que atinge mais alunos da educação especial para a que atinge menos",
    ]
    for b in rede.barreiras:
        linhas.append(
            f"- {b.codigo} {b.nome} (Eixo {b.eixo} — {b.eixo_nome}): presente em {_proporcao(len(b.escolas), total)} da rede"
            + (f" ({b.nota})" if b.nota else "")
            + f". Nas Declarações emitidas, obstáculo relatado em {_quantas(b.contar('obstaculo'))}, "
            f"divergência com o Censo em {_quantas(b.contar('divergencia'))}, sem relato em {_quantas(b.contar('sem_relato'))}. "
            f"Planos enviados com ação para a barreira: {_quantas(b.com_acao)}."
        )
    return "\n".join(linhas)


def _vai_a_ia(b: base_rede.BarreiraNaRede, e: base_rede.Evidencia) -> bool:
    """Relato de Declaração retirada por motivo LGPD nunca vai. O de escola pequena não vai quando ficaria
    perto de um estudante: barreira de classe exclusiva ou barreira em poucas escolas da rede."""
    if e.retirada_lgpd:
        return False
    return not (e.escola_pequena and (b.codigo == CLASSE_EXCLUSIVA or len(b.escolas) < POUCAS_ESCOLAS))


def _relatos(rede: base_rede.Rede):
    """Resumos das posições com referência [R<n>], já protegidos. Ficam de fora os que `_vai_a_ia` recusa
    e os que o Guardião bloqueia. Devolve também os (declaração, barreira) enviados, para a trilha."""
    locais = censo.locais_da_rede(rede.co_municipio)  # nomes da rede não vão à IA (pendência 16)
    protegidos, referencias, enviados, fora, mascarados = [], {}, [], 0, 0
    for b in rede.barreiras:
        for e in [e for e in b.evidencias if e.posicao in _ROTULO_POSICAO and e.resumo][:RELATOS_POR_BARREIRA]:
            if not _vai_a_ia(b, e):
                fora += 1
                continue
            ref = f"R{len(referencias) + 1}"
            resultado = proteger_para_ia(f"[{ref}] {b.codigo}, {_ROTULO_POSICAO[e.posicao]}: {e.resumo}", locais)
            if resultado.texto_protegido is None:
                fora += 1
                continue
            mascarados += bool(resultado.trechos)
            referencias[ref] = (e.co_entidade, b.codigo)
            enviados.append({"declaracao_id": e.declaracao_id, "codigo": b.codigo})
            protegidos.append(resultado.texto_protegido)
    return protegidos, referencias, enviados, fora, mascarados


def ultima(sessao: Session, co_municipio: int) -> SinteseAnalitica | None:
    return sessao.scalar(
        select(SinteseAnalitica).where(SinteseAnalitica.co_municipio == co_municipio).order_by(SinteseAnalitica.gerada_em.desc())
    )


def _com_fuso(momento: datetime) -> datetime:
    """O SQLite devolve datas sem fuso; tudo é gravado em UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def _apagar_antigas(sessao: Session, co_municipio: int) -> None:
    antigas = sessao.scalars(
        select(SinteseAnalitica).where(SinteseAnalitica.co_municipio == co_municipio)
        .order_by(SinteseAnalitica.gerada_em.desc()).offset(GUARDAR)
    ).all()
    for sintese in antigas:
        sessao.delete(sintese)


async def gerar(sessao: Session, *, co_municipio: int, secretario_id: str) -> tuple[SinteseAnalitica, bool]:
    """Levanta RuntimeError (nenhum provedor respondeu) e ContextoBloqueado."""
    rede = base_rede.montar(sessao, co_municipio)
    anterior = ultima(sessao, co_municipio)
    if anterior and anterior.assinatura == rede.assinatura and datetime.now(timezone.utc) - _com_fuso(anterior.gerada_em) < REAPROVEITAR_POR:
        return anterior, False

    protegidos, referencias, enviados, fora, mascarados = _relatos(rede)
    codigos = {b.codigo for b in rede.barreiras}
    try:
        partes = [liberar_dados_publicos(INSTRUCOES_ANALITICO), liberar_dados_publicos(renderizar_rede(rede))]
        if protegidos:
            partes.append(delimitar(liberar_dados_publicos(_CABECALHO_RELATOS), protegidos))
        sistema = juntar_protegidos(partes)
    except TextoBloqueado:
        raise ContextoBloqueado from None
    mensagens = [{"role": "user", "content": liberar_dados_publicos(PEDIDO_ANALITICO)}]

    def conferir(resposta: RespostaAnalitica) -> None:
        for achado in resposta.achados:
            if any(c not in codigos for c in achado.barreiras) or any(r.strip("[]") not in referencias for r in achado.relatos):
                raise ReferenciaInvalida("barreira ou relato fora do contexto")

    resposta, modelo = await ai_client.gerar_resposta(sistema, mensagens, RespostaAnalitica, validar=conferir)

    mascarar = _Mascara()
    achados = []
    for a in resposta.achados:
        texto = _sem_referencias(mascarar(a.texto))
        if not texto:
            continue
        evidencias = [referencias[r.strip("[]")] for r in dict.fromkeys(a.relatos)]
        achados.append({
            "tipo": a.tipo, "texto": texto, "barreiras": list(dict.fromkeys(a.barreiras)),
            "evidencias": [{"co_entidade": co, "codigo": codigo} for co, codigo in evidencias],
        })
    limitacoes = [l for l in (_sem_referencias(mascarar(l)) for l in resposta.limitacoes) if l]
    sintese = SinteseAnalitica(
        co_municipio=co_municipio, gerada_por=secretario_id, assinatura=rede.assinatura, modelo=modelo,
        # `enviados` é a trilha do que foi à IA (sem o texto), para responder a um titular.
        # A edição do Censo marca quando a síntese deixa de valer (RN-RET-07).
        conteudo={"achados": achados, "limitacoes": limitacoes, "fora": fora, "enviados": enviados, "censo_versao": rede.censo_versao},
    )
    sessao.add(sintese)
    sessao.flush()
    _apagar_antigas(sessao, co_municipio)
    sessao.commit()
    return sintese, mascarar.alterou or mascarados > 0
