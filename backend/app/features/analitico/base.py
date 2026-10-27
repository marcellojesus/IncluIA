"""Números do Analítico de Barreiras, calculados pelo sistema (SAB-RF-01, 03 e 04; RN-SAB-01, 02 e 04).

Para cada barreira da metodologia, na rede municipal do secretário:
- escolas com a barreira no Censo e alunos da educação especial nessas escolas ("alunos atingidos",
  critério de ordenação escolhido pelo responsável em 2026-10-27, o mesmo peso do score da rede);
- posições da última Declaração **emitida** de cada escola (rascunho nunca entra);
- escolas cuja última versão **enviada** do Plano de Ação traz ação para a barreira, e quantas dessas
  versões foram aceitas.
Escola sem Declaração ou sem plano aparece como "sem registro", nunca como escola sem barreira.
"""

import hashlib
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_connection
from app.features.acesso import censo
from app.features.declaracao.modelos import Declaracao
from app.features.plano.publicacao import MOTIVOS_LGPD
from app.features.plano.modelos import VersaoPlano
from app.shared.contexto_ia import base_normativa
from app.shared.contexto_ia.barreiras import celula_pequena, identificar

ALTA_RECORRENCIA = 0.9
"""A partir desta fração de escolas da rede, a barreira é marcada como de alta recorrência (protótipo v2)."""


@dataclass
class Evidencia:
    co_entidade: int
    escola: str
    posicao: str | None
    """Posição na última Declaração emitida; None quando a escola não emitiu ou a barreira não estava nela."""
    resumo: str | None
    acoes: list[str]
    plano_estado: str | None
    declaracao_id: str | None = None
    retirada_lgpd: bool = False
    """A Declaração foi retirada por dado pessoal ou a pedido de titular: o resumo não vai à IA (revisão do AgLGPD)."""
    escola_pequena: bool = False
    """Escola com 1 a 4 matrículas da educação especial (LIMIAR_CELULA_PEQUENA)."""


@dataclass
class BarreiraNaRede:
    codigo: str
    eixo: str
    eixo_nome: str
    nome: str
    nota: str | None
    escolas: list[int] = field(default_factory=list)
    alunos: int = 0
    evidencias: list[Evidencia] = field(default_factory=list)

    def contar(self, posicao: str) -> int:
        return sum(1 for e in self.evidencias if e.posicao == posicao)

    @property
    def com_declaracao(self) -> int:
        return sum(1 for e in self.evidencias if e.posicao is not None)

    @property
    def com_acao(self) -> int:
        return sum(1 for e in self.evidencias if e.acoes)

    @property
    def com_acao_aceita(self) -> int:
        return sum(1 for e in self.evidencias if e.acoes and e.plano_estado == "aceito")


@dataclass
class Rede:
    co_municipio: int
    municipio: str
    uf: str
    censo_versao: str | None
    escolas: dict[int, str]
    alunos: int
    com_declaracao: int
    com_plano: int
    barreiras: list[BarreiraNaRede]
    assinatura: str
    """Resumo das versões de Declaração e de plano usadas; muda quando uma escola emite ou envia."""

    def barreira(self, codigo: str) -> BarreiraNaRede | None:
        return next((b for b in self.barreiras if b.codigo == codigo), None)


def _escolas_municipais(co_municipio: int) -> list:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM escolas WHERE co_municipio = ? AND rede = ? ORDER BY co_entidade", (co_municipio, censo.REDE_DO_PILOTO)
        ).fetchall()
    finally:
        conn.close()


def _ultimas(sessao: Session, modelo, co_municipio: int) -> dict:
    ultimas = {}
    for registro in sessao.scalars(select(modelo).where(modelo.co_municipio == co_municipio).order_by(modelo.versao)):
        ultimas[registro.co_entidade] = registro
    return ultimas


def montar(sessao: Session, co_municipio: int) -> Rede:
    metodologia = base_normativa.carregar().metodologia
    linhas = _escolas_municipais(co_municipio)
    escolas = {linha["co_entidade"]: linha["no_entidade"] for linha in linhas}
    pequenas = {linha["co_entidade"] for linha in linhas if celula_pequena(linha)}
    declaracoes = {co: d for co, d in _ultimas(sessao, Declaracao, co_municipio).items() if co in escolas}
    planos = {co: v for co, v in _ultimas(sessao, VersaoPlano, co_municipio).items() if co in escolas}

    barreiras = {
        codigo: BarreiraNaRede(codigo=codigo, eixo=regra.eixo, eixo_nome=regra.eixo_nome, nome=regra.barreira, nota=None)
        for codigo, regra in metodologia.items()
    }
    for linha in linhas:
        for b in identificar(linha, metodologia):
            barreira = barreiras[b.codigo]
            barreira.escolas.append(linha["co_entidade"])
            barreira.alunos += int(linha["qt_mat_esp"] or 0)
            # Só a nota que vale para a barreira inteira; "não registrada no Censo" é de cada escola.
            if b.codigo == "B-II-07" and b.nota:
                barreira.nota = b.nota

    for barreira in barreiras.values():
        for co in barreira.escolas:
            declaracao, plano = declaracoes.get(co), planos.get(co)
            item = next((i for i in declaracao.itens if i.codigo == barreira.codigo), None) if declaracao else None
            acoes = [i.acao for i in plano.itens if i.codigo == barreira.codigo] if plano else []
            if item is None and not acoes:
                continue
            barreira.evidencias.append(Evidencia(
                co_entidade=co, escola=escolas[co], posicao=item.posicao if item else None, resumo=item.resumo if item else None,
                acoes=acoes, plano_estado=plano.estado if plano and acoes else None,
                declaracao_id=declaracao.id if declaracao else None,
                retirada_lgpd=bool(declaracao and declaracao.retirada_motivo in MOTIVOS_LGPD), escola_pequena=co in pequenas,
            ))

    usadas = sorted([d.id for d in declaracoes.values()] + [v.id for v in planos.values()])
    municipio = censo.municipio(co_municipio)
    return Rede(
        co_municipio=co_municipio, municipio=municipio.nome if municipio else "", uf=municipio.uf if municipio else "",
        censo_versao=linhas[0]["censo_versao"] if linhas else None, escolas=escolas,
        alunos=sum(int(linha["qt_mat_esp"] or 0) for linha in linhas), com_declaracao=len(declaracoes), com_plano=len(planos),
        barreiras=sorted((b for b in barreiras.values() if b.escolas), key=lambda b: (-b.alunos, -len(b.escolas), b.codigo)),
        assinatura=hashlib.sha256("|".join(usadas).encode()).hexdigest(),
    )
