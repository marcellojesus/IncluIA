"""Base da rede para o Plano Estratégico Municipal: calculada pelo sistema, nunca pela IA (SPM-RF-05).

Para cada barreira da metodologia: quantas escolas da rede municipal a têm no Censo e as ações dos
Planos de Ação **aceitos** pela secretaria (decisão do responsável em 2026-10-26: só aceitos).
Cada ação escolar recebe uma referência curta, [E<n>-A<m>], que é o que vai à IA no lugar do nome da
escola; o sistema traduz de volta para escola e item.
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_connection
from app.features.acesso import censo
from app.features.declaracao.modelos import Declaracao
from app.features.plano.modelos import VersaoPlano
from app.features.plano.publicacao import MOTIVOS_LGPD
from app.shared.contexto_ia import base_normativa
from app.shared.contexto_ia.barreiras import identificar


@dataclass(frozen=True)
class ItemDaRede:
    ref: str
    co_entidade: int
    escola: str
    item_id: str
    codigo: str
    acao: str
    relacao: str | None
    responsavel: str | None
    prazo: str | None
    horizonte: str
    custo_estimado: str | None


@dataclass
class BarreiraDaRede:
    codigo: str
    eixo: str
    eixo_nome: str
    nome: str
    escolas_com_barreira: list[int] = field(default_factory=list)
    """Escolas municipais com a barreira no Censo."""
    itens: list[ItemDaRede] = field(default_factory=list)


@dataclass
class BaseDaRede:
    co_municipio: int
    municipio: str
    uf: str
    escolas: dict[int, str]
    """Escolas municipais do Censo: código → nome."""
    planos: dict[int, int]
    """Escola → versão aceita mais recente do Plano de Ação."""
    barreiras: list[BarreiraDaRede]

    def item(self, ref: str) -> ItemDaRede | None:
        return next((i for b in self.barreiras for i in b.itens if i.ref == ref), None)

    def itens_por_id(self) -> dict[str, ItemDaRede]:
        return {i.item_id: i for b in self.barreiras for i in b.itens}

    def barreira(self, codigo: str) -> BarreiraDaRede | None:
        return next((b for b in self.barreiras if b.codigo == codigo), None)


def _escolas_municipais(co_municipio: int) -> list:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM escolas WHERE co_municipio = ? AND rede = ? ORDER BY co_entidade", (co_municipio, censo.REDE_DO_PILOTO)
        ).fetchall()
    finally:
        conn.close()


def _ultimas_aceitas(sessao: Session, co_municipio: int) -> dict[int, VersaoPlano]:
    """Último plano aceito de cada escola. Fica de fora o plano retirado por dado pessoal ou pedido de
    titular, ou feito sobre Declaração retirada por esses motivos: o texto dele vai ser apagado
    (RN-RET-05) e não pode seguir para a base da rede (revisão do AgLGPD de 2026-11-03, M1)."""
    retiradas = set(sessao.execute(
        select(Declaracao.co_entidade, Declaracao.versao).where(Declaracao.co_municipio == co_municipio, Declaracao.retirada_motivo.in_(MOTIVOS_LGPD))
    ).tuples())
    aceitas: dict[int, VersaoPlano] = {}
    for v in sessao.scalars(
        select(VersaoPlano).where(VersaoPlano.co_municipio == co_municipio, VersaoPlano.estado == "aceito").order_by(VersaoPlano.versao)
    ):
        if v.retirada_motivo in MOTIVOS_LGPD or v.texto_apagado_em or (v.co_entidade, v.declaracao_versao) in retiradas:
            continue
        aceitas[v.co_entidade] = v
    return aceitas


def montar(sessao: Session, co_municipio: int) -> BaseDaRede:
    metodologia = base_normativa.carregar().metodologia
    linhas = _escolas_municipais(co_municipio)
    escolas = {linha["co_entidade"]: linha["no_entidade"] for linha in linhas}
    barreiras = {
        codigo: BarreiraDaRede(codigo=codigo, eixo=regra.eixo, eixo_nome=regra.eixo_nome, nome=regra.barreira)
        for codigo, regra in sorted(metodologia.items(), key=lambda par: (par[1].eixo, par[0]))
    }
    for linha in linhas:
        for b in identificar(linha, metodologia):
            barreiras[b.codigo].escolas_com_barreira.append(linha["co_entidade"])

    aceitas = _ultimas_aceitas(sessao, co_municipio)
    for n, co_entidade in enumerate(sorted(aceitas), start=1):
        versao = aceitas[co_entidade]
        for m, item in enumerate(versao.itens, start=1):
            if item.codigo not in barreiras:
                continue
            barreiras[item.codigo].itens.append(ItemDaRede(
                ref=f"E{n}-A{m}", co_entidade=co_entidade, escola=escolas.get(co_entidade, f"INEP {co_entidade}"), item_id=item.id,
                codigo=item.codigo, acao=item.acao, relacao=item.relacao, responsavel=item.responsavel, prazo=item.prazo,
                horizonte=item.horizonte, custo_estimado=item.custo_estimado,
            ))

    municipio = censo.municipio(co_municipio)
    return BaseDaRede(
        co_municipio=co_municipio, municipio=municipio.nome if municipio else "", uf=municipio.uf if municipio else "",
        escolas=escolas, planos={co: v.versao for co, v in aceitas.items()},
        barreiras=[b for b in barreiras.values() if b.escolas_com_barreira or b.itens],
    )
