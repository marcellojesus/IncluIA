"""Camada 2 do Guardião LGPD (AD-05): nomes de pessoas.

Três fontes, todas locais:
- spaCy com `pt_core_news_sm` (cerca de 80 MB de memória com só `tok2vec` e `ner`); palavras em
  caixa alta são passadas ao modelo com só a inicial maiúscula ("MARIA" → "Maria"), que é como ele
  reconhece nomes;
- lista de prenomes e sobrenomes frequentes, em qualquer caixa e com diminutivo;
- vocativo escolar ("a aluna Ana Clara", "professora Maria").

Se o modelo não carregar, ou carregar sem reconhecer pessoas, levanta `GuardiaoIndisponivel`:
sem a camada de nomes, nada vai à IA.
"""

import re
from functools import lru_cache

from app.shared.guardiao_lgpd.nomes_frequentes import CONECTORES, SOBRENOMES, prenome_base
from app.shared.guardiao_lgpd.texto import Trecho, normalizar


class GuardiaoIndisponivel(RuntimeError):
    """O guardião não pôde verificar o texto; a chamada à IA não deve acontecer."""


# Termos do domínio que o modelo às vezes marca como pessoa e que nunca identificam ninguém.
_TERMOS_DO_DOMINIO = {
    "aee", "apae", "braille", "caps", "capsi", "cras", "creas", "libras", "pneei", "censo", "censo escolar",
    "educacenso", "inep", "ibge", "identidade", "lbi", "fundeb", "mec", "loa", "ppa", "paee", "pei", "srm",
    "sus", "tea", "tdah", "ubs", "undime", "consed", "seduc", "sme", "sala de recursos", "secretaria",
    "escola sem barreiras", "lgpd", "seedf", "sedf", "seec", "bncc", "pne", "fnde", "pdde", "eja", "cnpj",
    "sei", "inss", "atendimento educacional especializado", "decreto", "lei", "diagnostico", "eixo",
    "score", "valor", "taxa", "piso", "elevador", "rampa",
    # Verbos no imperativo que o modelo confunde com nome no início da frase do chat.
    "recalcule", "considere", "inclua", "reduza", "aumente", "explique", "detalhe", "priorize", "ajuste",
    "sugira", "refaca", "compare", "resuma", "liste", "mostre", "revise", "simplifique",
}

# Nomes de pessoas que são nomes de leis, escolas ou autores, não de quem está no relato.
_NOMES_PUBLICOS = (
    "paulo freire", "maria da penha", "maria montessori", "anisio teixeira", "darcy ribeiro",
    "helen keller", "louis braille", "dom pedro",
)
# "São José", "Escola Municipal Paulo Freire", "Lei Maria da Penha": o nome que vem depois é público.
_PREFIXO_PUBLICO = (
    r"(?:sao|santa|santo|dom|escola|emef|emei|ee|eef|cef|caic|ciep|colegio|creche|centro de ensino|"
    r"instituto|lei|municipal|estadual|federal)"
)
_ANTES_DE_NOME_PUBLICO = re.compile(rf"\b{_PREFIXO_PUBLICO}\s+$")
# O modelo às vezes inclui o prefixo no trecho ("Lei Maria da Penha" inteiro como pessoa).
_COMECA_COM_PREFIXO = re.compile(rf"^(?:{_PREFIXO_PUBLICO}\s+)+")

_MAIUSCULA = "A-ZÁÂÃÀÉÊÍÓÔÕÚÜÇ"
_MINUSCULA = "a-záâãàéêíóôõúüç"
_PALAVRA_NOME = rf"[{_MAIUSCULA}][{_MINUSCULA}]+"
_VOCATIVO = re.compile(
    r"(?i:\b(?:alun[oa]|estudante|professor[a]?|prof\.?|menin[oa]|crian[cç]a|m[aã]e|pai|respons[aá]vel|"
    r"diretor[a]?|coordenador[a]?|cuidador[a]?|int[eé]rprete|monitor[a]?|filh[oa]|irm[aã]o?|"
    r"chamad[oa]|se chama|nome [eé])\b)\s+"
    rf"({_PALAVRA_NOME}(?:\s+(?:d[aeo]s?\s+)?{_PALAVRA_NOME})*)"
)
# A partir de 3 letras: siglas de 2 ("ID", "RG", "DF") ficam como estão.
_CAIXA_ALTA = re.compile(rf"\b[{_MAIUSCULA}]{{3,}}\b")
_PALAVRA = re.compile(r"[a-z]+")


@lru_cache(maxsize=1)
def _modelo():
    try:
        import spacy

        nlp = spacy.load("pt_core_news_sm", exclude=["parser", "lemmatizer", "morphologizer", "attribute_ruler"])
    except Exception as exc:  # noqa: BLE001 — qualquer falha deixa o guardião indisponível
        raise GuardiaoIndisponivel("Modelo local de nomes indisponível") from exc
    if "ner" not in nlp.pipe_names or "PER" not in nlp.get_pipe("ner").labels:
        raise GuardiaoIndisponivel("Modelo local carregado sem reconhecimento de pessoas")
    return nlp


def carregar() -> None:
    """Carrega o modelo antecipadamente (por exemplo, na subida do servidor)."""
    _modelo()


def _eh_termo_do_dominio(trecho: str) -> bool:
    return normalizar(trecho).strip() in _TERMOS_DO_DOMINIO


@lru_cache(maxsize=1)
def _municipios_compostos() -> tuple[str, ...]:
    """Municípios de duas ou mais palavras ("Lucas do Rio Verde", "Pedro Leopoldo"), do artefato do
    Censo. Sem o banco, a lista fica vazia: o guardião mascara a mais, nunca a menos."""
    try:
        from app.database import get_connection

        conn = get_connection()
        try:
            linhas = conn.execute("SELECT DISTINCT no_municipio FROM municipios").fetchall()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return ()
    nomes = {normalizar(linha[0]) for linha in linhas if linha[0] and " " in linha[0].strip()}
    return tuple(sorted(nomes, key=len, reverse=True))


def _eh_nome_publico(norm: str, trecho: Trecho) -> bool:
    if _ANTES_DE_NOME_PUBLICO.search(norm[max(0, trecho.inicio - 40) : trecho.inicio]):
        return True
    prefixo = _COMECA_COM_PREFIXO.match(norm[trecho.inicio : trecho.fim])
    if prefixo:
        trecho = Trecho(trecho.inicio + prefixo.end(), trecho.fim, trecho.tipo, trecho.marcador)
    resto = norm[trecho.inicio :]
    for nome in _NOMES_PUBLICOS + _municipios_compostos():
        if resto.startswith(nome) and trecho.fim - trecho.inicio <= len(nome):
            if len(resto) == len(nome) or not resto[len(nome)].isalnum():
                return True
    return False


def _sem_caixa_alta(texto: str) -> str:
    """'MARIA EDUARDA faltou' → 'Maria Eduarda faltou', com o mesmo comprimento. Siglas curtas que
    não são prenomes (LGPD, SEEC) ficam como estão, para o modelo não tomá-las por pessoa."""
    def capitalizar(m: re.Match) -> str:
        palavra = m.group()
        norm = normalizar(palavra)
        if _eh_termo_do_dominio(palavra) or (len(palavra) <= 4 and prenome_base(norm) is None):
            return palavra
        return palavra[0] + palavra[1:].lower()

    return _CAIXA_ALTA.sub(capitalizar, texto)


def _pelo_modelo(texto: str) -> list[Trecho]:
    trechos = []
    for ent in _modelo()(_sem_caixa_alta(texto)).ents:
        trecho = texto[ent.start_char : ent.end_char]
        if ent.label_ != "PER" or any(c.isdigit() for c in trecho) or _eh_termo_do_dominio(trecho):
            continue
        trechos.append(Trecho(ent.start_char, ent.end_char, "NOME", "[NOME]"))
    return trechos


def _pela_lista(texto: str) -> list[Trecho]:
    palavras = list(_PALAVRA.finditer(normalizar(texto)))
    trechos = []
    i = 0
    while i < len(palavras):
        if prenome_base(palavras[i].group()) is None:
            i += 1
            continue
        inicio, fim = palavras[i].start(), palavras[i].end()
        j = i + 1
        while j < len(palavras):
            palavra = palavras[j].group()
            if prenome_base(palavra) or palavra in SOBRENOMES:
                fim = palavras[j].end()
                j += 1
            elif palavra in CONECTORES and j + 1 < len(palavras) and palavras[j + 1].group() in SOBRENOMES:
                fim = palavras[j + 1].end()
                j += 2
            else:
                break
        trechos.append(Trecho(inicio, fim, "NOME", "[NOME]"))
        i = j
    return trechos


def _pelo_vocativo(texto: str) -> list[Trecho]:
    return [
        Trecho(m.start(1), m.end(1), "NOME", "[NOME]")
        for m in _VOCATIVO.finditer(texto)
        if not _eh_termo_do_dominio(m.group(1))
    ]


def encontrar(texto: str) -> list[Trecho]:
    norm = normalizar(texto)
    candidatos = _pelo_modelo(texto) + _pela_lista(texto) + _pelo_vocativo(texto)
    return [t for t in candidatos if not _eh_nome_publico(norm, t)]
