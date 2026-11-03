"""Layout comum e regras dos documentos em PDF (RN-PDF-01 a 07).

A fonte Noto Sans (licença OFL, em `fontes/`) cobre os acentos e a pontuação do português e é
embutida só com os caracteres usados. O texto é real, com idioma, título e sumário nos metadados,
para o leitor de tela (PDF-RF-06).
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fpdf import FPDF

from app.shared.guardiao_lgpd import proteger, verificar_regras

logger = logging.getLogger(__name__)
# O fpdf2 avisa glifo ausente com o caractere, e o fontTools descreve a fonte em INFO: nada útil no log.
logging.getLogger("fpdf").setLevel(logging.ERROR)
logging.getLogger("fontTools").setLevel(logging.ERROR)

_FONTES = Path(__file__).parent / "fontes"
_BRASILIA = timezone(timedelta(hours=-3), "horário de Brasília")
"""Sem horário de verão desde 2019."""

RESSALVA_GERAL = (
    "Documento informativo gerado pela plataforma Escola Sem Barreiras. Não tem assinatura nem valor jurídico "
    "e não substitui atos oficiais da escola ou da secretaria."
)
RESSALVA_COPIA = "Esta cópia não acompanha correções nem retiradas feitas depois da geração. Consulte a plataforma."
RESSALVA_MASCARA = "Trechos que pareciam nome de pessoa foram trocados por marcadores, como [NOME], na geração deste arquivo."
USO_INTERNO = "Uso interno da escola e da secretaria. Contém registros sujeitos à LGPD: não divulgue."

_TEXTO = (33, 33, 33)
_ROTULO = (74, 74, 74)
"""Cinza com contraste de 8,9:1 sobre o branco (mínimo 4,5:1)."""
_DESTAQUE = (0, 77, 64)
_LINHA = (190, 190, 190)
_ALERTA = (153, 27, 27)
"""Vermelho escuro com contraste de 8,3:1 sobre o branco."""


class DocumentoInseguro(Exception):
    """O Guardião achou dado pessoal em texto da versão (RN-PDF-03). Guarda só os tipos, nunca o texto."""

    def __init__(self, tipos: list[str]):
        super().__init__(", ".join(tipos))
        self.tipos = tipos


@dataclass(frozen=True)
class Campo:
    rotulo: str
    valor: str | None
    livre: bool = False
    """Texto escrito por diretor ou secretário: passa de novo pelo Guardião (RN-PDF-03)."""


@dataclass
class Bloco:
    titulo: str
    campos: list[Campo]


@dataclass
class Secao:
    titulo: str
    campos: list[Campo] = field(default_factory=list)
    blocos: list[Bloco] = field(default_factory=list)
    vazio: str | None = None
    """Frase mostrada quando a seção não tem campos nem blocos."""


@dataclass
class Documento:
    tipo: str
    """"Declaração de Obstáculos", "Plano de Ação Escolar" ou "Plano Estratégico Municipal"."""
    sujeito: str
    """Escola ou município, como aparece no cabeçalho."""
    versao: int
    identificacao: list[Campo]
    secoes: list[Secao]
    ressalvas: list[str]
    """Ressalvas do tipo de documento; a geral (RESSALVA_GERAL) entra sempre."""
    congelado: dict
    """Conteúdo imutável da versão, base do código de conferência (RN-PDF-04)."""
    nome_arquivo: str
    alvo: tuple[str, str]
    """Tipo e identificador da versão, para a auditoria do download (sem conteúdo)."""
    marca: str = USO_INTERNO
    """Repetida no topo de cada página (revisão do AgLGPD, M2)."""


def data_hora(momento: datetime | None) -> str:
    """Data e hora no horário de Brasília; o banco guarda UTC, às vezes sem fuso (SQLite)."""
    if momento is None:
        return "—"
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(_BRASILIA).strftime("%d/%m/%Y às %H:%M")


def _serial(valor):
    if isinstance(valor, datetime):
        return (valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
    raise TypeError(type(valor).__name__)


def codigo_conferencia(congelado: dict) -> str:
    """SHA-256 do conteúdo congelado em ordem fixa, em 12 caracteres (ex.: 3F2A-9C1B-07DE). Identifica a
    versão impressa; não é assinatura e não prova autoria (RN-PDF-04)."""
    canonico = json.dumps(congelado, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=_serial)
    resumo = hashlib.sha256(canonico.encode("utf-8")).hexdigest()[:12].upper()
    return "-".join(resumo[i:i + 4] for i in range(0, 12, 4))


def conferir(documento: Documento) -> Documento:
    """RN-PDF-03. O texto livre já foi gravado mascarado, mas passa de novo pelo Guardião:
    - achado das camadas determinísticas (as mesmas da `conferir_saida`) impede o PDF;
    - nome de pessoa que escapou na gravação é mascarado só no arquivo, que pode mostrar menos que a
      tela, nunca mais (revisão do AgLGPD, M1); bloqueio por saúde ligada a um nome impede o PDF.
    Devolve o documento com os campos mascarados. Levanta `GuardiaoIndisponivel` sem o modelo de nomes."""
    tipos: set[str] = set()
    mascarou = False

    def campo(c: Campo) -> Campo:
        nonlocal mascarou
        if not (c.livre and c.valor):
            return c
        tipos.update(t.tipo for t in verificar_regras(c.valor).trechos)
        resultado = proteger(c.valor)
        if resultado.bloqueado:
            tipos.update(t.tipo for t in resultado.trechos if t.acao == "bloquear")
        if resultado.trechos:
            mascarou = True
            return replace(c, valor=resultado.texto_mascarado)
        return c

    conferido = replace(
        documento,
        identificacao=[campo(c) for c in documento.identificacao],
        secoes=[
            replace(s, campos=[campo(c) for c in s.campos], blocos=[replace(b, campos=[campo(c) for c in b.campos]) for b in s.blocos])
            for s in documento.secoes
        ],
    )
    if tipos:
        raise DocumentoInseguro(sorted(tipos))
    if mascarou:
        conferido.ressalvas = [*conferido.ressalvas, RESSALVA_MASCARA]
    return conferido


class _Pdf(FPDF):
    def __init__(self, documento: Documento, codigo: str, gerado_em: str):
        super().__init__(format="A4")
        self.documento = documento
        self.codigo = codigo
        self.gerado_em = gerado_em
        self.set_margins(18, 20, 18)
        self.set_auto_page_break(True, margin=26)
        for estilo, arquivo in (("", "NotoSans-Regular.ttf"), ("B", "NotoSans-Bold.ttf"), ("I", "NotoSans-Italic.ttf")):
            self.add_font("Noto", estilo, str(_FONTES / arquivo))
        self.alias_nb_pages()

    def header(self) -> None:
        self.set_font("Noto", "", 8)
        self.set_text_color(*_ROTULO)
        self.cell(0, 5, f"Escola Sem Barreiras · Gestão Ativa · {self.documento.tipo} · versão {self.documento.versao}",
                  align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Noto", "B", 8)
        self.set_text_color(*_ALERTA)
        self.multi_cell(0, 4, self.documento.marca, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*_LINHA)
        self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
        self.ln(5)

    def footer(self) -> None:
        self.set_y(-22)
        self.set_draw_color(*_LINHA)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.set_font("Noto", "", 7)
        self.set_text_color(*_ROTULO)
        self.multi_cell(0, 3.5, RESSALVA_GERAL, align="L", new_x="LMARGIN", new_y="NEXT")
        y = self.get_y()
        self.cell(0, 4, f"Código de conferência {self.codigo} · gerado em {self.gerado_em}")
        self.set_xy(self.l_margin, y)
        self.cell(0, 4, f"Página {self.page_no()} de {{nb}}", align="R", new_x="LMARGIN", new_y="NEXT")

    def _quebra_se_faltar(self, altura: float) -> None:
        if self.get_y() + altura > self.page_break_trigger:
            self.add_page()

    def titulo(self, texto: str) -> None:
        self.set_font("Noto", "B", 16)
        self.set_text_color(*_DESTAQUE)
        self.multi_cell(0, 8, texto, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Noto", "", 11)
        self.set_text_color(*_TEXTO)
        self.multi_cell(0, 6, self.documento.sujeito, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def secao(self, texto: str) -> None:
        self._quebra_se_faltar(24)
        self.ln(2)
        self.start_section(texto, level=0)
        self.set_font("Noto", "B", 12.5)
        self.set_text_color(*_DESTAQUE)
        self.multi_cell(0, 7, texto, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def _altura(self, campo: Campo) -> float:
        if not campo.valor:
            return 0
        self.set_font("Noto", "B", 8.5)
        rotulo = self.multi_cell(0, 4.5, campo.rotulo, dry_run=True, output="HEIGHT")
        self.set_font("Noto", "", 10)
        return rotulo + self.multi_cell(0, 5, campo.valor, dry_run=True, output="HEIGHT") + 1

    def bloco(self, bloco: Bloco) -> None:
        """Bloco inteiro na mesma página, quando cabe numa página."""
        self.set_font("Noto", "B", 10.5)
        altura = 1.5 + self.multi_cell(0, 5.5, bloco.titulo, dry_run=True, output="HEIGHT") + sum(self._altura(c) for c in bloco.campos)
        if altura < self.page_break_trigger - self.t_margin - 12:
            self._quebra_se_faltar(altura)
        self.subtitulo(bloco.titulo)
        for campo in bloco.campos:
            self.campo(campo)

    def subtitulo(self, texto: str) -> None:
        self._quebra_se_faltar(20)
        self.ln(1.5)
        self.set_font("Noto", "B", 10.5)
        self.set_text_color(*_TEXTO)
        self.multi_cell(0, 5.5, texto, align="L", new_x="LMARGIN", new_y="NEXT")

    def campo(self, campo: Campo) -> None:
        if not campo.valor:
            return
        self._quebra_se_faltar(10)
        self.set_font("Noto", "B", 8.5)
        self.set_text_color(*_ROTULO)
        self.multi_cell(0, 4.5, campo.rotulo, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Noto", "", 10)
        self.set_text_color(*_TEXTO)
        self.multi_cell(0, 5, campo.valor, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def paragrafo(self, texto: str, italico: bool = False) -> None:
        self.set_font("Noto", "I" if italico else "", 9.5)
        self.set_text_color(*_TEXTO)
        self.multi_cell(0, 5, texto, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(0.5)


def gerar(documento: Documento, agora: datetime | None = None) -> bytes:
    """Confere pelo Guardião e monta o PDF; não há caminho que pule a conferência (revisão do AgLGPD, B4).
    Levanta `DocumentoInseguro` ou `GuardiaoIndisponivel`."""
    documento = conferir(documento)
    gerado_em = data_hora(agora or datetime.now(timezone.utc))
    pdf = _Pdf(documento, codigo_conferencia(documento.congelado), gerado_em)
    pdf.set_lang("pt-BR")
    pdf.set_title(f"{documento.tipo} — versão {documento.versao}")
    pdf.set_subject(documento.sujeito)
    pdf.set_author("Escola Sem Barreiras")
    pdf.set_creator("Escola Sem Barreiras · Gestão Ativa")
    pdf.add_page()
    pdf.titulo(f"{documento.tipo} — versão {documento.versao}")
    for campo in documento.identificacao:
        pdf.campo(campo)

    pdf.secao("Sobre este documento")
    for ressalva in (RESSALVA_GERAL, RESSALVA_COPIA, *documento.ressalvas):
        pdf.paragrafo(f"• {ressalva}")
    pdf.paragrafo(
        f"O código de conferência {pdf.codigo} é calculado a partir do conteúdo desta versão. "
        "Duas cópias com o mesmo código têm o mesmo conteúdo.", italico=True,
    )

    for secao in documento.secoes:
        pdf.secao(secao.titulo)
        for campo in secao.campos:
            pdf.campo(campo)
        for bloco in secao.blocos:
            pdf.bloco(bloco)
        if not secao.campos and not secao.blocos and secao.vazio:
            pdf.paragrafo(secao.vazio, italico=True)
    return bytes(pdf.output())
