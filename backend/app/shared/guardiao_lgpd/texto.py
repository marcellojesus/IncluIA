"""Utilitários de texto compartilhados pelas camadas do Guardião LGPD."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

Acao = Literal["mascarar", "bloquear"]


@dataclass(frozen=True)
class Trecho:
    """Trecho do texto original a substituir. Guarda só posições e tipo, nunca o conteúdo."""

    inicio: int
    fim: int
    tipo: str
    marcador: str
    acao: Acao = "mascarar"


def normalizar(texto: str) -> str:
    """Minúsculas e sem acento, com o MESMO comprimento do original — as posições encontradas no
    texto normalizado valem para o texto original."""
    saida = []
    for caractere in texto:
        base = unicodedata.normalize("NFD", caractere)[0]
        minuscula = base.lower()
        saida.append(minuscula if len(minuscula) == 1 else base)
    return "".join(saida)


_SENTENCA = re.compile(r"[^.!?;\n]+[.!?;]*")


def sentencas(texto: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _SENTENCA.finditer(texto)]
