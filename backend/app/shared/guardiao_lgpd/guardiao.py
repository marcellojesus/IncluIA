"""Spec: docs/sdd/fase-2/arquitetura.md AD-05 — Guardião LGPD.

Todo texto escrito por usuário passa por `proteger` antes de qualquer chamada externa (provedor de
IA ou API de embeddings). As três camadas rodam no próprio backend; nada é enviado para fora para
decidir se um trecho é dado pessoal.

`TextoProtegido` só é criado aqui: quem chama a IA exige esse tipo, então não há caminho que leve
texto cru ao provedor (AD-05, "obrigatório por construção").
"""

import logging
from collections import Counter
from dataclasses import dataclass, field

from app.shared.guardiao_lgpd import contexto_escolar, documentos, nomes
from app.shared.guardiao_lgpd.texto import Trecho

logger = logging.getLogger("guardiao_lgpd")

_CHAVE = object()


class TextoProtegido:
    """Texto já processado pelo guardião. Não pode ser criado fora deste módulo."""

    __slots__ = ("_texto",)

    def __init__(self, texto: str, *, _chave: object = None):
        if _chave is not _CHAVE:
            raise TypeError("TextoProtegido só é criado pelo Guardião LGPD (use proteger)")
        self._texto = texto

    def __str__(self) -> str:
        return self._texto

    def __repr__(self) -> str:
        return f"TextoProtegido({len(self._texto)} caracteres)"


@dataclass(frozen=True)
class ResultadoGuardiao:
    # Fora do repr: um log ou traceback com o resultado não deve carregar o texto.
    texto_mascarado: str = field(repr=False)
    trechos: tuple[Trecho, ...]
    texto_protegido: TextoProtegido | None
    """None quando o envio está bloqueado: o usuário precisa reescrever o texto."""

    @property
    def bloqueado(self) -> bool:
        return self.texto_protegido is None

    @property
    def motivos_bloqueio(self) -> list[str]:
        return sorted({t.tipo for t in self.trechos if t.acao == "bloquear"})

    def resumo(self) -> dict[str, int]:
        """Tipo → quantidade. É o único dado do guardião que pode ir para log ou auditoria."""
        return dict(Counter(t.tipo for t in self.trechos))


_ROTULOS_BLOQUEIO = {
    "CPF": "CPF",
    "RG": "RG",
    "NIS": "NIS",
    "CARTAO_SUS": "cartão do SUS",
    "DOCUMENTO": "documento de identificação",
    "SAUDE": "dado de saúde de um estudante",
    "SENSIVEL": "situação sensível de um estudante",
}


class TextoBloqueado(Exception):
    """O texto tem dado de risco alto e não pode ir à IA; o usuário precisa reescrevê-lo."""

    def __init__(
        self,
        motivos: list[str],
        inicio: str = "A mensagem não foi enviada à IA",
        orientacao: str = "Reescreva sem esse dado: descreva a necessidade da escola, sem identificar o estudante.",
    ):
        self.motivos = motivos
        rotulos = ", ".join(_ROTULOS_BLOQUEIO.get(m, m) for m in motivos)
        super().__init__(f"{inicio} porque contém {rotulos}. {orientacao}")


def _selecionar(trechos: list[Trecho]) -> list[Trecho]:
    """Resolve sobreposições: bloqueio vence máscara; entre iguais, o trecho mais longo."""
    escolhidos: list[Trecho] = []
    for t in sorted(trechos, key=lambda t: (t.acao == "bloquear", t.fim - t.inicio), reverse=True):
        if not any(t.inicio < e.fim and e.inicio < t.fim for e in escolhidos):
            escolhidos.append(t)
    return sorted(escolhidos, key=lambda t: t.inicio)


def proteger(texto: str) -> ResultadoGuardiao:
    """Levanta `GuardiaoIndisponivel` se o modelo local de nomes não carregar."""
    encontrados_nomes = nomes.encontrar(texto)
    candidatos = documentos.encontrar(texto) + encontrados_nomes + contexto_escolar.encontrar(texto, encontrados_nomes)
    return _aplicar(texto, candidatos)


def _aplicar(texto: str, candidatos: list[Trecho]) -> ResultadoGuardiao:
    trechos = _selecionar(candidatos)

    partes = []
    cursor = 0
    for t in trechos:
        partes.append(texto[cursor : t.inicio])
        partes.append(t.marcador)
        cursor = t.fim
    partes.append(texto[cursor:])
    mascarado = "".join(partes)

    bloqueado = any(t.acao == "bloquear" for t in trechos)
    resultado = ResultadoGuardiao(
        texto_mascarado=mascarado,
        trechos=tuple(trechos),
        texto_protegido=None if bloqueado else TextoProtegido(mascarado, _chave=_CHAVE),
    )
    if trechos:
        logger.info("Guardião LGPD: %s%s", resultado.resumo(), " (bloqueado)" if bloqueado else "")
    return resultado


def liberar_dados_publicos(texto: str) -> TextoProtegido:
    """Libera texto montado pelo CÓDIGO a partir de modelos fixos e dados agregados públicos
    (Censo, score, metodologia, base legal) — nunca texto digitado por usuário nem conteúdo de
    declarações e planos, que passam por `proteger`.

    Dispensa só a camada de nomes, que degrada prompts estruturados ("Score", "Valor" e nomes de
    campos viram [NOME]). Documentos, saúde e situações sensíveis continuam verificados: se algum
    aparecer, é sinal de que texto de usuário entrou por engano, e levanta `TextoBloqueado`.
    O uso é restrito por chamada: `tests/test_arquitetura_ia.py` só aceita os argumentos listados
    lá; acrescentar um exige revisão do AgLGPD."""
    resultado = _aplicar(texto, documentos.encontrar(texto) + contexto_escolar.encontrar(texto, []))
    if resultado.texto_protegido is None:
        raise TextoBloqueado(resultado.motivos_bloqueio)
    return resultado.texto_protegido


def verificar_regras(texto: str) -> ResultadoGuardiao:
    """Só as camadas determinísticas (documentos, contatos e contexto escolar), sem reconhecimento de
    nomes: para conferir de novo um texto já mascarado sem os falsos positivos do modelo."""
    return _aplicar(texto, documentos.encontrar(texto) + contexto_escolar.encontrar(texto, []))


def juntar_protegidos(partes: list[TextoProtegido], separador: str = "\n\n") -> TextoProtegido:
    """Concatena textos já protegidos (por exemplo, o contexto da IA montado por camadas). O
    separador é texto fixo do código; qualquer parte crua levanta TypeError."""
    if not all(isinstance(p, TextoProtegido) for p in partes):
        raise TypeError("Só textos protegidos podem ser juntados (AD-05)")
    if separador.strip():
        raise ValueError("O separador deve ser só espaço em branco")
    # Revisão das camadas 1 e 3 sobre o resultado: um dado partido entre duas partes (telefone,
    # CPF) só se forma na junção.
    texto = separador.join(str(p) for p in partes)
    resultado = _aplicar(texto, documentos.encontrar(texto) + contexto_escolar.encontrar(texto, []))
    if resultado.texto_protegido is None:
        raise TextoBloqueado(resultado.motivos_bloqueio)
    return resultado.texto_protegido


def proteger_ou_falhar(texto: str) -> TextoProtegido:
    """Atalho para quem só precisa do texto protegido: levanta `TextoBloqueado` em risco alto."""
    resultado = proteger(texto)
    if resultado.texto_protegido is None:
        raise TextoBloqueado(resultado.motivos_bloqueio)
    return resultado.texto_protegido
