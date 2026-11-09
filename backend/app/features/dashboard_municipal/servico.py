"""Spec: docs/sdd/fase-2/requirements/secretario/dashboard-municipal.md (DMS-RF-01 a 09) e regras.

Tudo aqui é regra determinística sobre o Censo e o andamento registrado; a IA não entra (RN-DMS-02).
O score da rede municipal usa a mesma ponderação por alunos ESP do score público (RN-03 do score),
mas só sobre as escolas da rede do secretário; o do município, com todas as redes, vem como referência.

Prioridade (decisão do responsável em 2026-10-26): o peso de cada escola é quanto ela tira do score
da rede, (10 − score) × alunos ESP ÷ alunos ESP da rede. A soma dos pesos é 10 − score da rede.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_connection
from app.features.acesso import censo
from app.features.dashboard_municipal.schemas import Cobertura, DashboardMunicipal, EixoRede, EscolaPrioritaria
from app.features.declaracao.modelos import Declaracao
from app.features.plano.modelos import VersaoPlano
from app.shared.contexto_ia import base_normativa
from app.shared.contexto_ia.barreiras import celula_pequena, identificar
from etl.score import classificar_faixa

_EIXOS = [
    ("I", "AEE", 30, "score_eixo_i"),
    ("II", "Acessibilidade", 30, "score_eixo_ii"),
    ("III", "Profissionais", 25, "score_eixo_iii"),
    ("IV", "Classe comum", 15, "score_eixo_iv"),
]
LIMIAR_EIXO_CRITICO = 3.0
"""Abaixo disto o eixo está na faixa Crítico (RN-04 do score)."""
PRIORIDADES = 10


def _faixa(score: float) -> str:
    return classificar_faixa(score)[0]


def _ler_censo(co_municipio: int) -> tuple[list, object]:
    conn = get_connection()
    try:
        escolas = conn.execute(
            "SELECT * FROM escolas WHERE co_municipio = ? AND rede = ? AND score IS NOT NULL ORDER BY co_entidade",
            (co_municipio, censo.rede_da_gestao(co_municipio)),
        ).fetchall()
        municipio = conn.execute("SELECT score, qtd_escolas FROM municipios WHERE co_municipio = ?", (co_municipio,)).fetchone()
    finally:
        conn.close()
    return escolas, municipio


def _media(escolas: list, coluna: str, ponderada: bool) -> float:
    if ponderada:
        return sum(e[coluna] * e["qt_mat_esp"] for e in escolas) / sum(e["qt_mat_esp"] for e in escolas)
    return sum(e[coluna] for e in escolas) / len(escolas)


def _andamento(sessao: Session, co_municipio: int) -> tuple[set[int], dict[int, VersaoPlano]]:
    com_declaracao = set(sessao.scalars(select(Declaracao.co_entidade).where(Declaracao.co_municipio == co_municipio)))
    ultimas: dict[int, VersaoPlano] = {}
    for v in sessao.scalars(select(VersaoPlano).where(VersaoPlano.co_municipio == co_municipio).order_by(VersaoPlano.versao)):
        ultimas[v.co_entidade] = v
    return com_declaracao, ultimas


def montar(sessao: Session, co_municipio: int) -> DashboardMunicipal:
    escolas, linha_municipio = _ler_censo(co_municipio)
    municipio = censo.municipio(co_municipio)
    alunos = sum(int(e["qt_mat_esp"] or 0) for e in escolas)
    ponderada = alunos > 0

    score = _media(escolas, "score", ponderada) if escolas else None
    eixos = []
    if escolas:
        for codigo, nome, peso, coluna in _EIXOS:
            valor = _media(escolas, coluna, ponderada)
            eixos.append(EixoRede(eixo=codigo, nome=nome, peso=peso, score=valor, faixa=_faixa(valor)))
        eixos.sort(key=lambda e: e.score)  # sort estável: empate fica na ordem dos eixos

    com_declaracao, ultimas = _andamento(sessao, co_municipio)
    da_rede = {e["co_entidade"] for e in escolas}
    metodologia = base_normativa.carregar().metodologia
    com_barreiras = {e["co_entidade"] for e in escolas if identificar(e, metodologia)}
    aguardando = [v for co, v in ultimas.items() if co in da_rede and v.estado == "aguardando_analise"]

    # Sem nenhum aluno ESP na rede, o score é média simples e cada escola pesa igual (fallback da RN-03).
    no_ranking = [e for e in escolas if e["qt_mat_esp"]] if ponderada else list(escolas)
    prioridades = []
    for e in no_ranking:
        fator = e["qt_mat_esp"] / alunos if ponderada else 1 / len(escolas)
        prioridades.append(EscolaPrioritaria(
            co_entidade=e["co_entidade"], escola=e["no_entidade"], score=e["score"], faixa=_faixa(e["score"]),
            alunos_esp=None if celula_pequena(e) else int(e["qt_mat_esp"] or 0), peso=(10 - e["score"]) * fator,
            eixos_criticos=[c for c, _, _, coluna in _EIXOS if e[coluna] < LIMIAR_EIXO_CRITICO],
            declaracao=e["co_entidade"] in com_declaracao,
            plano=ultimas[e["co_entidade"]].estado if e["co_entidade"] in ultimas else None,
        ))
    prioridades.sort(key=lambda p: (-p.peso, p.score, p.co_entidade))

    return DashboardMunicipal(
        municipio=municipio.nome if municipio else "", uf=municipio.uf if municipio else "",
        censo_versao=escolas[0]["censo_versao"] if escolas else None,
        score=score, faixa=_faixa(score) if score is not None else None,
        ponderacao="alunos_esp" if ponderada else "media_simples", alunos_esp=alunos,
        score_municipio=linha_municipio["score"] if linha_municipio else None,
        escolas_municipio=linha_municipio["qtd_escolas"] if linha_municipio else 0,
        eixos=eixos,
        cobertura=Cobertura(
            escolas_municipais=len(escolas), escolas_com_barreiras=len(com_barreiras),
            com_declaracao=len(com_declaracao & da_rede), com_plano_enviado=len(set(ultimas) & da_rede),
            aguardando_analise=len(aguardando), plano_mais_antigo=min((v.submetida_em for v in aguardando), default=None),
        ),
        prioridades=prioridades[:PRIORIDADES],
        escolas_no_ranking=len(no_ranking),
        escolas_sem_alunos_esp=len(escolas) - len(no_ranking),
    )
