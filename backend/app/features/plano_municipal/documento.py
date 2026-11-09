"""PDFs do Plano Estratégico Municipal (PDF-RF-03 e 07; RN-PDF-01 a 09). Só o secretário baixa.

- `documento`: a versão confirmada, com as ações e as escolas atendidas, para uso interno.
- `documento_narrativa`: a narrativa executiva, em PDF próprio, para quem decide o orçamento (decisão
  de 2026-11-03). Sai sem nome de escola, bairro ou município no texto e sem o texto livre das ações:
  as ações aparecem só pela linha estruturada (barreiras, horizonte, prioridade).
"""

from sqlalchemy.orm import Session

from app.features.acesso import censo
from app.features.analitico.sintese import POUCAS_ESCOLAS
from app.features.plano.documento import HORIZONTES
from app.features.plano.fontes import citacoes
from app.features.plano.servico import ErroPlano
from app.features.plano_municipal import narrativa as narrativa_ia
from app.features.plano_municipal.base import _escolas_municipais
from app.features.plano_municipal.modelos import NarrativaPlanoMunicipal, VersaoPlanoMunicipal
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
    rotulos = censo.rotulos_da_rede(versao.co_municipio)
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
        sujeito=f"{rotulos.rede} de {sujeito}",
        versao=versao.versao,
        identificacao=[
            # Só o papel, não o nome (RN-PDF-06; decisão de 2026-11-03).
            Campo("Confirmado em", f"{data_hora(versao.confirmada_em)}, pela {rotulos.secretaria}"),
            Campo("Ações", str(len(versao.acoes))),
            Campo("Escolas atendidas", f"{len(atendidas)} de {len(_escolas_municipais(versao.co_municipio))} {rotulos.escolas}"),
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


def marca_narrativa(secretaria: str) -> str:
    return f"Documento da {secretaria} para apoio à decisão orçamentária. Não contém dado pessoal nem nome de escola."



RESSALVAS_NARRATIVA = [
    "Texto escrito pelo assistente de IA a partir da versão confirmada do plano; os números são calculados pelo sistema.",
    "Confirmar o plano não é aprovar orçamento, financiar nem executar as ações.",
    "Custos são estimativas da secretaria, ainda sem fonte de custo verificada.",
    "As fontes legais citadas ainda não foram validadas por especialista.",
]


def _alcance(acao: dict, restricoes: narrativa_ia.Restricoes) -> str:
    if not acao.get("escolas"):
        return "Ação da rede, sem escola específica"
    # Ação retida da IA (escola pequena ou retirada LGPD) também não diz o alcance no PDF (AgLGPD, B1).
    return "Ação localizada" if narrativa_ia.motivo_restricao(acao, restricoes) else "Nas escolas da rede"


def _poucas(valor: int) -> str:
    """Contagem pequena de escolas vira "menos de N", como na IA (AgLGPD, B1)."""
    return f"menos de {POUCAS_ESCOLAS}" if 0 < valor < POUCAS_ESCOLAS else str(valor)


def _linha_da_acao(acao: dict, barreiras: dict[str, str], restricoes: narrativa_ia.Restricoes) -> list[Campo]:
    """Só o que o sistema estruturou: o texto livre da ação pode citar escola (RN-PDF-09)."""
    return [
        Campo("Barreiras", "; ".join(f"{c} {barreiras.get(c, '')}".strip() for c in acao.get("codigos") or [])),
        Campo("Horizonte", HORIZONTES.get(acao.get("horizonte"), acao.get("horizonte"))),
        Campo("Prioridade", PRIORIDADES.get(acao.get("prioridade"), acao.get("prioridade"))),
        Campo("Alcance", _alcance(acao, restricoes)),
        Campo("Custo", "Estimativa registrada pela secretaria" if narrativa_ia._tem_custo(acao) else "A estimar"),
    ]


def documento_narrativa(sessao: Session, versao: VersaoPlanoMunicipal, registro: NarrativaPlanoMunicipal) -> Documento:
    """Levanta ErroPlano quando o texto gravado tem número ou nome da rede (RN-PDF-09): a narrativa
    editada antes de 2026-11-03 não passou por essa checagem ao salvar."""
    t = registro.conteudo
    textos = [t.get("resumo") or "", t.get("situacao") or "", t.get("fundamentacao") or "", t.get("proximos_passos") or "",
              *(b["texto"] for b in t.get("estrategia") or []), *(t.get("incertezas") or []), *(t.get("lacunas") or [])]
    if narrativa_ia.problema(textos, censo.locais_da_rede(versao.co_municipio, bairros_curtos=True)):
        raise ErroPlano("A narrativa tem número, nome da rede ou estudante descrito no texto. Edite o texto antes de baixar o PDF.", 409)

    municipio = censo.municipio(versao.co_municipio)
    sujeito = f"{municipio.nome}/{municipio.uf}" if municipio else f"Município {versao.co_municipio}"
    rotulos = censo.rotulos_da_rede(versao.co_municipio)
    n = narrativa_ia.numeros(versao, len(_escolas_municipais(versao.co_municipio)))
    barreiras = _barreiras()
    restricoes = narrativa_ia._restricoes(sessao, versao)
    fontes = citacoes(set(t.get("fontes") or []))
    referidas = list(dict.fromkeys(int(r[1:]) for b in t.get("estrategia") or [] for r in b.get("acoes") or []))

    return Documento(
        tipo="Narrativa executiva do Plano Estratégico Municipal",
        sujeito=f"{rotulos.rede} de {sujeito}",
        versao=versao.versao,
        identificacao=[
            Campo("Plano confirmado em", f"{data_hora(versao.confirmada_em)}, pela {rotulos.secretaria}"),
            Campo("Texto", "Revisado pela secretaria" if registro.editada else "Escrito pelo assistente de IA, sem revisão da secretaria"),
        ],
        secoes=[
            Secao("Números do plano (calculados pelo sistema)", campos=[
                Campo("Ações municipais", str(n.acoes)),
                Campo("Barreiras enfrentadas", str(n.barreiras)),
                Campo(f"{rotulos.escolas.capitalize()} atendidas", f"{_poucas(n.escolas_atendidas)} de {n.escolas_municipais}"),
                Campo("Ações na LOA · no PPA", f"{n.loa} · {n.ppa}"),
                Campo("Ações de prioridade alta", str(n.prioridade_alta)),
                Campo("Ações com custo estimado pela secretaria", f"{n.com_custo_estimado} de {n.acoes}"),
            ]),
            Secao("Resumo", campos=[Campo("", t.get("resumo"), livre=True)]),
            Secao("Situação da rede", campos=[Campo("", t.get("situacao"), livre=True)]),
            Secao("Estratégia", blocos=[
                Bloco(f"Frente {i}", [
                    Campo("", b["texto"], livre=True),
                    Campo("Ações", ", ".join(b.get("acoes") or [])),
                ]) for i, b in enumerate(t.get("estrategia") or [], start=1)
            ]),
            Secao("Fundamentação legal", campos=[
                Campo("", t.get("fundamentacao"), livre=True),
                Campo("Fontes citadas", "; ".join(fontes.get(f, f) for f in t.get("fontes") or [])),
                Campo("O que a base normativa entregue não sustenta", " ".join(t.get("lacunas") or []), livre=True),
            ]),
            Secao("Próximos passos", campos=[Campo("", t.get("proximos_passos"), livre=True)]),
            Secao("Incertezas", campos=[Campo("", f"• {i}", livre=True) for i in t.get("incertezas") or []],
                  vazio="Nenhuma incerteza registrada."),
            Secao("Ações citadas", blocos=[
                Bloco(f"A{k}", _linha_da_acao(versao.acoes[k - 1], barreiras, restricoes)) for k in sorted(referidas) if 1 <= k <= len(versao.acoes)
            ], vazio="Nenhuma ação citada."),
        ],
        ressalvas=RESSALVAS_NARRATIVA,
        congelado={
            "documento": "narrativa_plano_municipal",
            "co_municipio": versao.co_municipio,
            "versao": versao.versao,
            "confirmada_em": versao.confirmada_em,
            "editada": registro.editada,
            "conteudo": {k: v for k, v in t.items() if k != "trilha"},
        },
        nome_arquivo=f"narrativa-executiva_{versao.co_municipio}_v{versao.versao}.pdf",
        alvo=("narrativa_plano_municipal", registro.id),
        marca=marca_narrativa(rotulos.secretaria),
    )
