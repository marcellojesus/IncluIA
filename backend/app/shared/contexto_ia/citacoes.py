"""Validador de citações (AD-08): a IA só pode fundamentar no que o montador entregou.

Três regras, todas determinísticas:
1. todo identificador citado — em campos `fontes` ou entre colchetes no texto — está em
   `ContextoIA.ids_citaveis`;
2. toda menção livre a lei, decreto ou artigo ("Art. 59 da LDB") corresponde a um documento e a um
   artigo dos trechos entregues — pega a citação inventada que não usa o identificador;
3. resposta com campo `lacunas` que não usa nenhuma fonte precisa declarar a lacuna (RN-SAB-03).

Resposta reprovada levanta `CitacaoInvalida`; `gerar_resposta_fundamentada` faz o `ai_client`
descartá-la e tentar o próximo provedor.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.shared import ai_client
from app.shared.contexto_ia.montador import ContextoIA
from app.shared.guardiao_lgpd import TextoProtegido

# Formato fechado de identificador (`LBI-art28-p2-I`, `D12686-art4A`): sufixos só de parágrafo,
# parágrafo único ou inciso romano — um nome não cabe nele.
_FORMATO_ID = r"[A-Z][A-Z0-9]{1,9}-art\d{1,4}[A-Z]?(?:-p\d{1,2}|-pu)?(?:-[IVXLC]{1,8})?"
_ID_ENTRE_COLCHETES = re.compile(rf"\[({_FORMATO_ID})\]")
_ID_COMPLETO = re.compile(rf"^{_FORMATO_ID}$")
_ARTIGO = re.compile(r"\bart(?:igo)?s?\.?\s*(\d{1,4})(?!\d)\s*[ºo°]?(?:\s*-\s*([A-Z])\b)?", re.IGNORECASE)
_NORMA = re.compile(
    r"\b(?:lei|decreto|portaria|resolu[cç][aã]o|parecer|medida provis[oó]ria)\s*(?:federal\s*)?"
    r"(?:complementar\s*)?(?:n[ºo°.]*\s*)?(\d{1,2}\.?\d{3})(?![\d.]*\d)",
    re.IGNORECASE,
)
# Número muito longo depois de "art." ou de "lei" não é referência legal; conta como problema.
_REFERENCIA_LONGA = re.compile(
    r"\b(?:art(?:igo)?s?\.?|lei|decreto|portaria)\s*(?:n[ºo°.]*\s*)?\d[\d.]{6,}", re.IGNORECASE
)
_NUMERO_NORMA = re.compile(r"\b(\d{1,2}\.\d{3})/\d{4}")

INSTRUCOES_CITACAO = """Regras de fundamentação:
- Cite base legal só com os identificadores entre colchetes da seção "Base normativa", por exemplo [LBI-art28-XII], e liste-os em "fontes".
- Não mencione lei, decreto, portaria ou artigo que não esteja nessa seção, nem de memória.
- Se a seção não tiver trecho que sustente o que foi perguntado, diga isso em "lacunas" em vez de fundamentar."""


FORMATO_RESPOSTA_FUNDAMENTADA = """Responda APENAS com um JSON válido, sem markdown, neste formato:
{"resposta": "texto para a equipe da escola, em português do Brasil",
 "fundamentos": [{"afirmacao": "afirmação normativa", "fontes": ["identificador"]}],
 "lacunas": ["o que a base normativa entregue não cobre"]}"""


class RespostaFundamentada(BaseModel):
    """Formato mínimo de resposta com fundamentação; as features podem estender com campos próprios."""

    resposta: str
    fundamentos: list["Fundamento"]
    lacunas: list[str]


class Fundamento(BaseModel):
    """Afirmação normativa e os trechos que a sustentam."""

    afirmacao: str
    fontes: list[str] = Field(min_length=1)


class CitacaoInvalida(ai_client.RespostaReprovada):
    """`problemas` é uma lista de (tipo, valor). O valor vem da resposta da IA e fica só na memória,
    para quem precisar mostrar ao usuário; o log recebe apenas a contagem por tipo."""

    def __init__(self, problemas: list[tuple[str, str]]):
        self.problemas = problemas
        super().__init__(f"{len(problemas)} problema(s) de citação")

    def tipos(self) -> dict[str, int]:
        contagem: dict[str, int] = {}
        for tipo, _ in self.problemas:
            contagem[tipo] = contagem.get(tipo, 0) + 1
        return contagem

    def resumo_seguro(self) -> str:
        return "CitacaoInvalida: " + ", ".join(f"{t}={n}" for t, n in sorted(self.tipos().items()))


@dataclass(frozen=True)
class RelatorioCitacoes:
    ids_usados: frozenset[str]


def _percorrer(valor, campo: str | None = None) -> Iterator[tuple[str | None, object]]:
    """(nome do campo, valor) de todas as folhas de um modelo Pydantic, inclusive aninhadas."""
    if isinstance(valor, BaseModel):
        for nome in type(valor).model_fields:
            yield from _percorrer(getattr(valor, nome), nome)
    elif isinstance(valor, (list, tuple)):
        for item in valor:
            yield from _percorrer(item, campo)
    else:
        yield campo, valor


def _referencias_permitidas(contexto: ContextoIA) -> tuple[set[str], set[str]]:
    """Artigos e números de norma que a resposta pode mencionar: os dos trechos entregues, inclusive
    os citados dentro do texto deles (o Art. 19-A menciona a Lei 14.113, do Fundeb)."""
    artigos: set[str] = set()
    normas: set[str] = set()
    for t in contexto.trechos:
        numero, _, letra = t.artigo.removeprefix("Art. ").partition("-")
        artigos.add(re.sub(r"\D", "", numero) + letra)
        normas.update(n.replace(".", "") for n in _NUMERO_NORMA.findall(t.citacao))
        corpo = f"{t.contexto or ''} {t.texto}"
        artigos.update(m.group(1) + (m.group(2) or "").upper() for m in _ARTIGO.finditer(corpo))
        normas.update(m.group(1).replace(".", "") for m in _NORMA.finditer(corpo))
    return artigos, normas


def validar_citacoes(resposta: BaseModel, contexto: ContextoIA) -> RelatorioCitacoes:
    permitidos = contexto.ids_citaveis
    artigos, normas = _referencias_permitidas(contexto)

    problemas: list[tuple[str, str]] = []
    usados: set[str] = set()
    textos: list[str] = []
    for campo, valor in _percorrer(resposta):
        if not isinstance(valor, str):
            continue
        if campo == "fontes":
            fonte = valor.strip().strip("[]")
            if _ID_COMPLETO.match(fonte):
                usados.add(fonte)
            else:
                problemas.append(("fonte_mal_formada", fonte))
        else:
            textos.append(valor)
            usados.update(_ID_ENTRE_COLCHETES.findall(valor))

    for trecho_id in sorted(usados - permitidos):
        problemas.append(("trecho_fora", trecho_id))

    texto_livre = _ID_ENTRE_COLCHETES.sub(" ", "\n".join(textos))
    for m in _REFERENCIA_LONGA.finditer(texto_livre):
        problemas.append(("referencia_invalida", m.group(0)))
    for m in _NORMA.finditer(texto_livre):
        if m.group(1).replace(".", "") not in normas:
            problemas.append(("norma_fora", m.group(0).strip()))
    for m in _ARTIGO.finditer(texto_livre):
        if m.group(1) + (m.group(2) or "").upper() not in artigos:
            problemas.append(("artigo_fora", m.group(0).strip()))

    lacunas = getattr(resposta, "lacunas", None)
    if lacunas is not None and not usados and not problemas and not any(l.strip() for l in lacunas):
        problemas.append(("sem_lacuna", ""))

    if problemas:
        raise CitacaoInvalida(problemas)
    return RelatorioCitacoes(frozenset(usados))


async def gerar_resposta_fundamentada(
    system_prompt: TextoProtegido, mensagens: list[dict], schema_model: type[BaseModel], contexto: ContextoIA,
    validar_extra: Callable[[BaseModel], object] | None = None,
):
    """`ai_client.gerar_resposta` com o validador: resposta com citação inválida vale como falha do
    provedor e a cadeia segue para o próximo. `validar_extra` (que levanta RespostaReprovada) confere o
    que for próprio da funcionalidade. Levanta RuntimeError se nenhum provedor passar."""

    def validar(resposta):
        validar_citacoes(resposta, contexto)
        if validar_extra is not None:
            validar_extra(resposta)

    return await ai_client.gerar_resposta(system_prompt, mensagens, schema_model, validar=validar)


RespostaFundamentada.model_rebuild()
