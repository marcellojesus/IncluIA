"""Divide um texto legal em Markdown em trechos por dispositivo (AD-08).

Unidade de trecho:
- artigo sem incisos → um trecho (`LBI-art27`);
- inciso do caput → um trecho com o caput como contexto (`LBI-art28-XII`);
- parágrafo sem incisos → um trecho (`D12686-art1-p3`; parágrafo único: `LBI-art27-pu`);
- inciso de parágrafo → um trecho com o parágrafo como contexto (`LBI-art28-p2-I`).
Caput ou parágrafo que só introduz incisos não vira trecho próprio: aparece como contexto de cada
inciso. Alíneas ficam dentro do inciso. Notas editoriais ("*(Redação dada pelo Decreto…)*") saem
do texto legal e vão para `nota`; artigos vetados não geram trecho.

Formatos aceitos (os de base/legislacao/): artigo em `**Art. 4º-A**`, parágrafo em `§ 1º` ou
`**§ 1º**` ou `*Parágrafo único.*`, inciso em linha própria (`XVI - …`, `**XVI** - …`) ou embutido
(`…: I - …; II - …; e III - …`), títulos `## CAPÍTULO` e `### Seção`.
"""

import re
from dataclasses import dataclass

_ARTIGO = re.compile(r"^\*\*Art\.\s*(\d+)\s*º?(?:-([A-Z]))?\.?\*\*\s*(.*)$")
_PARAGRAFO = re.compile(r"^\**§\s*(\d+)\s*º?\**\s*(.*)$")
_PARAGRAFO_UNICO = re.compile(r"^\*Parágrafo único\.\*\s*(.*)$")
_INCISO = re.compile(r"^\**([IVXLC]+)\**\s*-\s*(.*)$")
_CAPITULO = re.compile(r"^##\s+(.*)$")
_SECAO = re.compile(r"^###\s+(.*)$")
_INCISOS_EMBUTIDOS = re.compile(r"(?:(?<=: )|(?<=; )|(?<=; e ))(?=[IVXLC]+ - )")
_NOTA_EDITORIAL = re.compile(
    r"\s*\*\(([^*]*?)\)\*|\s*\(((?:incluído|incluída|redação dada)[^)]*)\)", re.IGNORECASE
)
_ALTERADO_POR = re.compile(r"(?:Lei|Decreto) nº [\d.]+, de \d{4}")


@dataclass
class Trecho:
    id: str
    documento_id: str
    artigo: str
    paragrafo: str | None
    inciso: str | None
    citacao: str
    capitulo: str | None
    secao: str | None
    contexto: str | None
    """Caput do artigo ou do parágrafo quando o trecho é um inciso."""
    texto: str
    """Texto literal do dispositivo, sem notas editoriais."""
    nota: str | None
    alterado_por: str | None
    ordem: int

    @property
    def texto_busca(self) -> str:
        """Texto indexado e usado para embedding: citação, seção, contexto e dispositivo."""
        return "\n".join(p for p in (self.citacao, self.secao, self.contexto, self.texto) if p)


def _limpar(texto: str) -> tuple[str, str | None, str | None]:
    """Remove notas editoriais e marcação Markdown; devolve (texto, nota, alterado_por)."""
    notas = [m.group(1) or m.group(2) for m in _NOTA_EDITORIAL.finditer(texto)]
    texto = _NOTA_EDITORIAL.sub("", texto)
    texto = texto.replace("**", "")
    texto = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    nota = "; ".join(notas) if notas else None
    alterado = _ALTERADO_POR.search(nota) if nota else None
    return texto, nota, alterado.group() if alterado else None


def _separar_incisos(texto: str) -> tuple[str, list[tuple[str, str]]]:
    """'Caput: I - a; II - b' → ('Caput:', [('I', 'a;'), ('II', 'b')])."""
    partes = _INCISOS_EMBUTIDOS.split(texto)
    incisos = [(m.group(1), m.group(2).strip()) for p in partes[1:] if (m := _INCISO.match(p.strip()))]
    return partes[0].strip(), incisos


def _rotulo_artigo(numero: str, letra: str | None) -> tuple[str, str]:
    """('4', 'A') → ('art4A', 'Art. 4º-A'); ('10', None) → ('art10', 'Art. 10')."""
    ordinal = "º" if int(numero) < 10 else ""
    return f"art{numero}{letra or ''}", f"Art. {numero}{ordinal}{'-' + letra if letra else ''}"


@dataclass
class _Bloco:
    """Artigo (caput) ou parágrafo em leitura. Vira trecho próprio só se não tiver incisos."""

    id: str
    rotulo: str
    paragrafo: str | None
    texto: str
    tem_incisos: bool = False


def dividir(documento_id: str, citacao_documento: str, markdown: str) -> list[Trecho]:
    trechos: list[Trecho] = []
    capitulo = secao = None
    artigo_rotulo = ""
    artigo_id = ""
    bloco: _Bloco | None = None
    vetado = False

    def adicionar(sufixo: str, rotulo: str, texto_bruto: str, contexto: str | None, paragrafo: str | None, inciso: str | None):
        texto, nota, alterado = _limpar(texto_bruto)
        trechos.append(
            Trecho(
                id=f"{documento_id}-{sufixo}",
                documento_id=documento_id,
                artigo=artigo_rotulo,
                paragrafo=paragrafo,
                inciso=inciso,
                citacao=f"{citacao_documento}, {rotulo}",
                capitulo=capitulo,
                secao=secao,
                contexto=_limpar(contexto)[0] if contexto else None,
                texto=texto,
                nota=nota,
                alterado_por=alterado,
                ordem=len(trechos),
            )
        )

    def fechar_bloco():
        nonlocal bloco
        if bloco and not bloco.tem_incisos and not vetado:
            adicionar(bloco.id, bloco.rotulo, bloco.texto, None, bloco.paragrafo, None)
        bloco = None

    def abrir_bloco(sufixo: str, rotulo: str, paragrafo: str | None, texto: str):
        nonlocal bloco
        corpo, embutidos = _separar_incisos(texto)
        bloco = _Bloco(sufixo, rotulo, paragrafo, corpo)
        for numero, texto_inciso in embutidos:
            adicionar_inciso(numero, texto_inciso)

    def adicionar_inciso(numero: str, texto_inciso: str):
        bloco.tem_incisos = True
        adicionar(f"{bloco.id}-{numero}", f"{bloco.rotulo}, {numero}", texto_inciso, bloco.texto, bloco.paragrafo, numero)

    for linha in (l.strip() for l in markdown.splitlines()):
        if not linha:
            continue
        if m := _CAPITULO.match(linha):
            fechar_bloco()
            capitulo, secao = m.group(1).strip(), None
        elif m := _SECAO.match(linha):
            fechar_bloco()
            secao = m.group(1).strip()
        elif m := _ARTIGO.match(linha):
            fechar_bloco()
            artigo_id, artigo_rotulo = _rotulo_artigo(m.group(1), m.group(2))
            vetado = "VETADO" in m.group(3).upper()
            abrir_bloco(artigo_id, artigo_rotulo, None, m.group(3))
        elif not artigo_id or vetado:
            continue  # cabeçalho, ementa e preâmbulo, ou resto de artigo vetado
        elif m := _PARAGRAFO_UNICO.match(linha):
            fechar_bloco()
            abrir_bloco(f"{artigo_id}-pu", f"{artigo_rotulo}, parágrafo único", "parágrafo único", m.group(1))
        elif m := _PARAGRAFO.match(linha):
            fechar_bloco()
            rotulo = f"§ {m.group(1)}º"
            abrir_bloco(f"{artigo_id}-p{m.group(1)}", f"{artigo_rotulo}, {rotulo}", rotulo, m.group(2))
        elif (m := _INCISO.match(linha)) and bloco:
            adicionar_inciso(m.group(1), m.group(2))
        elif bloco and not bloco.tem_incisos:
            bloco.texto = f"{bloco.texto} {linha}"  # continuação do caput ou do parágrafo
        elif trechos:
            trechos[-1].texto = f"{trechos[-1].texto} {_limpar(linha)[0]}"  # continuação do inciso

    fechar_bloco()
    return trechos
