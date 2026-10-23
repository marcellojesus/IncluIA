"""Camada 1 do Guardião LGPD (AD-05): documentos e contatos por regras determinísticas.

Documentos de identificação bloqueiam o envio; contatos, datas de nascimento e matrículas são
mascarados. O código INEP da escola (8 dígitos) e o código IBGE do município (7 dígitos) são dados
públicos e não são tocados.
"""

import re

from app.shared.guardiao_lgpd.texto import Trecho, normalizar

_ROTULO_NUM = r"[\s:.ºo°n]*"  # separadores entre o rótulo e o número ("CPF:", "RG nº", "NIS n.")

_CPF_FORMATADO = re.compile(r"(?<!\d)\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)")
_CPF_ROTULADO = re.compile(rf"\bcpf\b{_ROTULO_NUM}(\d[\d\s./-]{{9,16}}\d)")
_ONZE_DIGITOS = re.compile(r"(?<!\d)\d{11}(?!\d)")
_RG_FORMATADO = re.compile(r"(?<!\d)\d{1,2}\.\d{3}\.\d{3}-[\dxX](?!\d)")
_RG_ROTULADO = re.compile(
    rf"(?<![a-z])(?:r\.?\s?g\.?|identidade|registro geral|carteira de identidade)(?![a-z]){_ROTULO_NUM}"
    r"(?:[a-z]{2}-?\s?)?(\d[\d.\-x]{4,})"
)
_NIS_FORMATADO = re.compile(r"(?<!\d)\d{3}\.\d{5}\.\d{2}-\d(?!\d)")
_NIS_ROTULADO = re.compile(rf"\b(?:nis|pis|pasep)\b{_ROTULO_NUM}(\d[\d.\-]{{9,}})")
_CNS = re.compile(r"(?<!\d)[1-9]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}(?!\d)")
_OUTROS_DOCUMENTOS = re.compile(
    rf"\b(?:passaporte|titulo de eleitor|certidao de nascimento|certidao|cnh|carteira de motorista)\b{_ROTULO_NUM}"
    r"([a-z]{0,2}\d[\d\s.\-]{4,}\d)"
)

_TELEFONE = [
    re.compile(r"(?:\+55\s?)?\(\d{2}\)\s?9?\d{4}[\s.-]?\d{4}(?!\d)"),
    re.compile(r"(?<!\d)(?:\+55\s?)?(?:\d{2}\s)?9?\d{4}-\d{4}(?!\d)"),
    re.compile(r"(?<!\d)(?:\+55\s?)?\d{2}\s?9\d{4}\s?\d{4}(?!\d)"),
]
_TELEFONE_ROTULADO = re.compile(r"\b(?:tel|telefone|celular|cel|whatsapp|whats|zap|fone)\b[\s:.]*(\+?[\d()\s.\-]{8,}\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_EMAIL_POR_EXTENSO = re.compile(r"[\w.+-]+\s+arroba\s+[\w-]+(?:\s*(?:\.|ponto)\s*[\w-]+)+")

_DATA_NASCIMENTO = re.compile(
    r"\b(?:nasc\w*|data de nascimento|aniversario|aniversaria|dn)\b[^\d]{0,25}?"
    r"(\d{1,2}[/.-]\d{1,2}(?:[/.-]\d{2,4})?|\d{1,2} de [a-z]+(?: de \d{4})?)"
)
_MATRICULA = re.compile(
    r"\b(?:matricula|mat\.|ra|registro do alun[oa]|codigo do alun[oa]|id do alun[oa]|id inep do alun[oa])"
    rf"(?![a-z]){_ROTULO_NUM}(?=[a-z0-9./-]*\d)([a-z0-9./-]{{3,}})"
)
# ID INEP do estudante tem 12 dígitos; qualquer sequência de 11 ou mais dígitos que não seja
# telefone sai como identificador (inclui CPF digitado com erro no dígito verificador).
_NUMERO_LONGO = re.compile(r"(?<!\d)\d{11,}(?!\d)")


def _cpf_valido(digitos: str) -> bool:
    if len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(digitos[:tamanho], range(tamanho + 1, 1, -1)))
        verificador = (soma * 10) % 11 % 10
        if verificador != int(digitos[tamanho]):
            return False
    return True


def encontrar(texto: str) -> list[Trecho]:
    norm = normalizar(texto)
    trechos: list[Trecho] = []

    def bloquear(m: re.Match, tipo: str, grupo: int = 0) -> None:
        trechos.append(Trecho(m.start(grupo), m.end(grupo), tipo, f"[{tipo}]", "bloquear"))

    def mascarar(m: re.Match, tipo: str, grupo: int = 0) -> None:
        trechos.append(Trecho(m.start(grupo), m.end(grupo), tipo, f"[{tipo}]"))

    for m in _CPF_FORMATADO.finditer(texto):
        bloquear(m, "CPF")
    for m in _CPF_ROTULADO.finditer(norm):
        bloquear(m, "CPF", 1)  # com rótulo, bloqueia mesmo com dígito verificador errado
    for m in _ONZE_DIGITOS.finditer(texto):
        if _cpf_valido(m.group()):
            bloquear(m, "CPF")
    for m in _RG_FORMATADO.finditer(texto):
        bloquear(m, "RG")
    for m in _RG_ROTULADO.finditer(norm):
        bloquear(m, "RG", 1)
    for m in _NIS_FORMATADO.finditer(texto):
        bloquear(m, "NIS")
    for m in _NIS_ROTULADO.finditer(norm):
        bloquear(m, "NIS", 1)
    for m in _CNS.finditer(texto):
        bloquear(m, "CARTAO_SUS")
    for m in _OUTROS_DOCUMENTOS.finditer(norm):
        bloquear(m, "DOCUMENTO", 1)

    # Padrões com rótulo primeiro: em empate de tamanho, o primeiro candidato define o tipo.
    for m in _DATA_NASCIMENTO.finditer(norm):
        mascarar(m, "DATA_NASCIMENTO", 1)
    for m in _MATRICULA.finditer(norm):
        mascarar(m, "MATRICULA", 1)
    for m in _TELEFONE_ROTULADO.finditer(norm):
        mascarar(m, "TELEFONE", 1)
    for padrao in _TELEFONE:
        for m in padrao.finditer(texto):
            mascarar(m, "TELEFONE")
    for m in _EMAIL.finditer(texto):
        mascarar(m, "EMAIL")
    for m in _EMAIL_POR_EXTENSO.finditer(norm):
        mascarar(m, "EMAIL")
    for m in _NUMERO_LONGO.finditer(texto):
        mascarar(m, "ID_ESTUDANTE")

    return trechos
