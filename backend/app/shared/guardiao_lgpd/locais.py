"""Camada 5 do Guardião LGPD (AD-05): nomes de escola, bairro e município no que vai à IA.

O reconhecimento de nomes trata "EMEF Santa Rita" e município de nome composto como nome público e
não mascara, o que está certo para texto público. No que vai à IA, porém, o local identifica a escola
e, com ela, quem escreveu e os estudantes citados (PBD-029 e 112; pendência 16 da arquitetura).

A comparação é por palavras, não por texto literal (revisão do AgLGPD de 2026-11-03, A2):
- texto e nomes viram palavras sem acento e em minúsculas, então hífen, pontuação, quebra de linha e
  "esc. mun." não atrapalham;
- abreviações viram a forma longa ("profa" → "professora", "br" → "barao");
- títulos ("professora", "doutor", "barão") são opcionais dos dois lados e podem vir no fim do nome,
  como no Censo de São Paulo ("MARIO ALVES DE CARVALHO DR");
- o código numérico no início do nome (Rio de Janeiro) e o prefixo da escola ("ESC MUN", "CIEP",
  "UMEI") saem, e a escola casa com e sem o prefixo.

Para não estragar o texto (M1 e M3), um nome **fraco** só casa com inicial maiúscula no original.
Um nome é fraco quando é uma palavra só, curta ("Belém", "Natal") ou comum ("Independência",
"Esperança"), ou quando todas as suas palavras são comuns. Nome feito só de palavras de tipo de escola
("ESCOLA MUNICIPAL", "EDUCACAO INFANTIL") é ignorado.

Números de 8 dígitos, com ou sem pontuação, saem como código: é a forma do código INEP, mas a regra
também pega CEP, protocolo e outros números do mesmo tamanho. Escrita abreviada do município ("LRV") e
nome pela metade ("em Lucas") não são reconhecidos.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from app.shared.guardiao_lgpd.texto import Trecho, normalizar

MARCADOR_LOCAL = "[escola ou município da rede]"
MARCADOR_INEP = "[código]"

_PALAVRA = re.compile(r"[^\W_]+")
_INEP = re.compile(r"(?<![\d.,])(?:\d(?:[.\-]?\d){7}|\d{2}\s\d{3}\s\d{3})(?![\d]|,\d)")

_ABREVIACOES = {
    "esc": "escola", "mun": "municipal", "mul": "municipal", "munic": "municipal", "unid": "unidade", "est": "estadual",
    "prof": "professor", "profa": "professora", "profo": "professor", "dr": "doutor", "dra": "doutora", "pe": "padre",
    "dep": "deputado", "ver": "vereador", "cel": "coronel", "mal": "marechal", "gal": "general", "sen": "senador",
    "pres": "presidente", "gov": "governador", "eng": "engenheiro", "br": "barao", "cap": "capitao", "ten": "tenente",
    "maj": "major", "mons": "monsenhor", "des": "desembargador", "min": "ministro", "sto": "santo", "sta": "santa",
    "n": "nossa", "sra": "senhora", "sr": "senhor",
}
_TITULOS = frozenset({
    "professor", "professora", "doutor", "doutora", "padre", "deputado", "deputada", "vereador", "vereadora", "coronel",
    "marechal", "general", "senador", "senadora", "presidente", "governador", "governadora", "engenheiro", "barao", "baronesa",
    "capitao", "tenente", "major", "monsenhor", "desembargador", "ministro", "dom", "dona", "frei", "irma", "madre", "maestro",
})
_TIPO_DE_ESCOLA = frozenset({
    "escola", "escolas", "municipal", "estadual", "federal", "ensino", "fundamental", "medio", "infantil", "educacao",
    "educacional", "centro", "unidade", "grupo", "colegio", "creche", "instituto", "integrada", "integral", "basica",
    "emef", "emei", "emeif", "emeief", "emeb", "cmei", "cemei", "cei", "umei", "ciep", "edi", "ee", "eeef", "em", "ue", "e", "u",
    "de", "do", "da", "dos", "das", "anexo", "polo", "rural", "urbana", "nucleo", "tempo",
})
_CONECTORES = frozenset({"de", "do", "da", "dos", "das", "e"})
_ESTENDE = _TIPO_DE_ESCOLA - _CONECTORES - {"em", "u", "ue", "ee"}
"""Prefixo que sai junto com o nome casado; "em" e siglas de uma letra também são palavras comuns."""
_COMUNS = frozenset({
    # Palavras do dia a dia e do domínio que também são nome de escola, bairro ou município.
    "independencia", "esperanca", "progresso", "liberdade", "alegria", "modelo", "futuro", "amizade", "jardim", "central",
    "vitoria", "palmas", "bonito", "formosa", "horizonte", "floresta", "centro", "saude", "paz", "uniao", "harmonia",
    "aurora", "primavera", "felicidade", "conquista", "vista", "bela", "boa", "nova", "novo", "alto", "baixo", "sao",
    "santa", "santo", "nossa", "senhora", "vila", "parque", "cidade", "estrela", "sol", "lua", "luz", "mar", "rio", "lago",
    "campo", "campos", "serra", "monte", "morro", "porto", "ponte", "fonte", "praia", "ilha", "bosque", "chacara",
    "fazenda", "sitio", "industrial", "comercial", "popular", "operario", "agua", "aguas", "verde", "azul", "branca",
    "branco", "preta", "preto", "dourado", "dourados", "brasil", "brasilia", "america", "inclusao", "acolhimento",
    "aprender", "saber", "crescer", "caminho", "caminhos", "sonho", "sonhos", "vida", "mundo", "terra", "cristo",
    "jesus", "deus", "fe", "gloria", "graca", "piedade", "carmo", "conceicao", "aparecida", "fatima", "lourdes",
    "natal", "pascoa", "palmeira", "palmeiras", "coqueiro", "coqueiros", "eldorado", "planalto", "pioneiro", "pioneiros",
    "bandeirantes", "tiradentes", "imperial", "republica", "democracia", "cidadania", "trabalho", "ordem",
})
_TAMANHO_MINIMO = 6


def _canonica(palavra: str) -> str:
    return _ABREVIACOES.get(palavra, palavra)


def _palavras(texto: str) -> list[tuple[int, int, str]]:
    """(início, fim, forma canônica) de cada palavra; posições no texto original."""
    norm = normalizar(texto)
    return [(m.start(), m.end(), _canonica(m.group())) for m in _PALAVRA.finditer(norm)]


@dataclass(frozen=True)
class _Nome:
    palavras: tuple[str, ...]
    """Sem títulos, que são opcionais dos dois lados."""
    fraco: bool


@dataclass(eq=False)
class Locais:
    """Nomes de uma rede, prontos para busca: índice pela primeira palavra. Sem nomes, a camada só tira
    os números de 8 dígitos."""

    nomes: tuple[_Nome, ...] = ()
    _indice: dict[str, list[_Nome]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for nome in sorted(self.nomes, key=lambda n: len(n.palavras), reverse=True):
            self._indice.setdefault(nome.palavras[0], []).append(nome)

    def __len__(self) -> int:
        return len(self.nomes)


SEM_LOCAIS = Locais()


def _variantes(nome: str) -> list[tuple[str, ...]]:
    palavras = [p for _, _, p in _palavras(nome)]
    while palavras and palavras[0].isdigit():
        palavras.pop(0)
    # Título no fim ("MARIO ALVES DE CARVALHO DR", "MAUA BR DE") vai para o começo.
    fim = len(palavras)
    while fim > 0 and (palavras[fim - 1] in _TITULOS or palavras[fim - 1] in _CONECTORES):
        fim -= 1
    if fim < len(palavras) and any(p in _TITULOS for p in palavras[fim:]):
        palavras = palavras[fim:] + palavras[:fim]
    sem_titulos = [p for p in palavras if p not in _TITULOS]
    completo = list(sem_titulos)
    inicio = 0
    while inicio < len(sem_titulos) and sem_titulos[inicio] in _TIPO_DE_ESCOLA:
        inicio += 1
    nucleo = sem_titulos[inicio:]
    while nucleo and nucleo[0] in _CONECTORES:
        nucleo = nucleo[1:]
    variantes = []
    if nucleo:
        variantes.append(tuple(nucleo))
        if completo != nucleo:
            variantes.append(tuple(completo))
    return variantes


def _eh_fraco(palavras: tuple[str, ...]) -> bool:
    uteis = [p for p in palavras if p not in _CONECTORES and p not in _TIPO_DE_ESCOLA]
    if not uteis:
        return True
    if len(uteis) == 1:
        return len(uteis[0]) < _TAMANHO_MINIMO or uteis[0] in _COMUNS or uteis[0].isdigit()
    return all(p in _COMUNS for p in uteis)


def nomes_da_rede(municipio: str, escolas: Iterable[str], bairros: Iterable[str] = ()) -> Locais:
    """Município, escolas (todas as redes do município) e bairros de duas ou mais palavras."""
    vistos: dict[tuple[str, ...], bool] = {}

    def incluir(variante: tuple[str, ...], fraco: bool) -> None:
        if all(p in _TIPO_DE_ESCOLA for p in variante):
            return  # "ESCOLA MUNICIPAL", "EDUCACAO INFANTIL": nada a casar
        vistos[variante] = vistos.get(variante, True) and fraco

    for variante in _variantes(municipio or ""):
        incluir(variante, _eh_fraco(variante))
    for escola in escolas:
        variantes = _variantes(escola or "")
        for variante in variantes:
            # A forma com o prefixo ("emef maua") é forte mesmo quando o núcleo ("maua") é fraco.
            com_prefixo = len(variantes) == 2 and variante == variantes[1] and variante[0] in _TIPO_DE_ESCOLA
            incluir(variante, False if com_prefixo and len(variante) > 1 else _eh_fraco(variante))
    for bairro in bairros:
        palavras = tuple(p for _, _, p in _palavras(bairro or "") if p not in _TITULOS)
        uteis = [p for p in palavras if p not in _CONECTORES]
        if len(uteis) >= 2 and not all(p in _COMUNS for p in uteis):
            incluir(palavras, False)
    return Locais(tuple(_Nome(v, f) for v, f in vistos.items()))


def _casa(palavras: list[tuple[int, int, str]], i: int, nome: _Nome, texto: str) -> int | None:
    """Índice da palavra depois do nome, se ele casa a partir de i; títulos do texto são pulados."""
    j = i
    for alvo in nome.palavras:
        while j < len(palavras) and palavras[j][2] in _TITULOS and palavras[j][2] != alvo:
            j += 1
        if j >= len(palavras) or palavras[j][2] != alvo:
            return None
        j += 1
    if nome.fraco and not texto[palavras[i][0]].isupper():
        return None
    return j


def encontrar(texto: str, locais: Locais | None) -> list[Trecho]:
    """Trechos LOCAL (nomes da rede) e INEP (números de 8 dígitos). Com `locais` None, a camada não roda."""
    if locais is None:
        return []
    trechos = [Trecho(m.start(), m.end(), "INEP", MARCADOR_INEP) for m in _INEP.finditer(texto)]
    if not locais.nomes:
        return trechos
    palavras = _palavras(texto)
    i = 0
    while i < len(palavras):
        fim = None
        for nome in locais._indice.get(palavras[i][2], ()):
            fim = _casa(palavras, i, nome, texto)
            if fim is not None:
                break
        if fim is None:
            i += 1
            continue
        # Prefixo e título logo antes ("EMEF", "Escola Municipal", "Profa.") saem junto com o nome.
        k = i
        while k > 0 and (palavras[k - 1][2] in _ESTENDE or palavras[k - 1][2] in _TITULOS):
            k -= 1
        trechos.append(Trecho(palavras[k][0], palavras[fim - 1][1], "LOCAL", MARCADOR_LOCAL))
        i = fim
    return trechos


def contem_local(texto: str, locais: Locais | None) -> bool:
    """Para conferir a saída da IA: algum nome da rede ou número de 8 dígitos no texto."""
    return bool(encontrar(texto, locais))

