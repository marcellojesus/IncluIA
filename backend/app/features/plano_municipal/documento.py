"""PDF de uma versão confirmada do Plano Estratégico Municipal (PDF-RF-03; RN-PDF-01 a 07).

Só o secretário baixa. A narrativa executiva fica fora (pendência 16 da arquitetura: a edição do
secretário ainda não passa pela troca de nomes).
"""

from app.features.acesso import censo
from app.features.plano.documento import HORIZONTES
from app.features.plano.fontes import citacoes
from app.features.plano_municipal.base import _escolas_municipais
from app.features.plano_municipal.modelos import VersaoPlanoMunicipal
from app.shared.contexto_ia import BaseNormativaIndisponivel, base_normativa
from app.shared.pdf import Bloco, Campo, Documento, Secao, data_hora

PRIORIDADES = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}

RESSALVAS = [
    "Confirmar o plano não é aprovar orçamento, financiar nem executar as ações.",
    "Custos são estimativas da secretaria.",
    "Este plano não altera os Planos de Ação das escolas.",
    "As fontes legais citadas ainda não foram validadas por especialista.",
]


def _barreiras() -> dict[str, str]:
    try:
        return {codigo: regra.barreira for codigo, regra in base_normativa.carregar().metodologia.items()}
    except BaseNormativaIndisponivel:
        return {}


def _origem(acao: dict) -> str:
    if acao.get("origem") == "ia":
        return "Proposta pela IA e editada pelo secretário" if acao.get("editada") else "Proposta pela IA e aceita pelo secretário"
    return "Escrita pelo secretário"


def _nome_escola(nomes: dict[int, str], co_entidade: int) -> str:
    return nomes.get(co_entidade, f"INEP {co_entidade}")


def documento(versao: VersaoPlanoMunicipal) -> Documento:
    municipio = censo.municipio(versao.co_municipio)
    sujeito = f"{municipio.nome}/{municipio.uf}" if municipio else f"Município {versao.co_municipio}"
    planos_base = (versao.base or {}).get("planos") or []
    atendidas = {e["co_entidade"] for a in versao.acoes for e in a.get("escolas") or []}
    nomes = {co: e.nome for co, e in censo.escolas(atendidas | {p["co_entidade"] for p in planos_base}).items()}
    fontes = citacoes({f for a in versao.acoes for f in a.get("fontes") or []})
    barreiras = _barreiras()

    blocos = []
    for n, acao in enumerate(versao.acoes, start=1):
        escolas = "; ".join(
            f"{_nome_escola(nomes, e['co_entidade'])} (cobertura {e.get('cobertura', 'total')})" for e in acao.get("escolas") or []
        )
        blocos.append(Bloco(f"A{n} · prioridade {PRIORIDADES.get(acao.get('prioridade'), acao.get('prioridade'))}", [
            Campo("Ação", acao.get("acao"), livre=True),
            Campo("Barreiras", "; ".join(f"{c} {barreiras.get(c, '')}".strip() for c in acao.get("codigos") or [])),
            Campo("Justificativa", acao.get("justificativa"), livre=True),
            Campo("Responsável", acao.get("responsavel"), livre=True),
            Campo("Prazo", acao.get("prazo"), livre=True),
            Campo("Horizonte", HORIZONTES.get(acao.get("horizonte"), acao.get("horizonte"))),
            Campo("Custo estimado", acao.get("custo_estimado"), livre=True),
            Campo("Premissas", acao.get("premissas"), livre=True),
            Campo("Fontes", "; ".join(fontes.get(f, f) for f in acao.get("fontes") or [])),
            Campo("Escolas atendidas", escolas or "Ação da rede, sem escola específica."),
            Campo("Origem", _origem(acao)),
        ]))

    return Documento(
        tipo="Plano Estratégico Municipal",
        sujeito=f"Rede municipal de {sujeito}",
        versao=versao.versao,
        identificacao=[
            # Só o papel, não o nome (RN-PDF-06; decisão de 2026-11-03).
            Campo("Confirmado em", f"{data_hora(versao.confirmada_em)}, pela Secretaria Municipal de Educação"),
            Campo("Ações", str(len(versao.acoes))),
            Campo("Escolas atendidas", f"{len(atendidas)} de {len(_escolas_municipais(versao.co_municipio))} escolas municipais"),
        ],
        secoes=[
            Secao("Ações da rede", blocos=blocos, vazio="Nenhuma ação nesta versão."),
            Secao("Planos escolares usados como base", campos=[
                Campo(_nome_escola(nomes, p["co_entidade"]), f"Plano de Ação aceito, versão {p['versao']}") for p in planos_base
            ], vazio="Nenhum plano escolar aceito foi usado como base."),
        ],
        ressalvas=RESSALVAS,
        congelado={
            "documento": "plano_municipal",
            "co_municipio": versao.co_municipio,
            "versao": versao.versao,
            "confirmada_em": versao.confirmada_em,
            "acoes": [{k: v for k, v in a.items() if k != "id"} for a in versao.acoes],
            "base": versao.base,
        },
        nome_arquivo=f"plano-estrategico-municipal_{versao.co_municipio}_v{versao.versao}.pdf",
        alvo=("plano_municipal", versao.id),
    )
