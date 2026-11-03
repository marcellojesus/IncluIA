"""PDF de uma versão emitida da Declaração de Obstáculos (PDF-RF-01; RN-PDF-01 a 07).

O conteúdo vem só da versão congelada (`declaracoes` + `declaracao_itens`); a situação da publicação
aparece como está no momento da geração. O motivo de retirada não entra.
"""

from app.features.acesso import censo
from app.features.declaracao.modelos import Declaracao
from app.shared.contexto_ia import BaseNormativaIndisponivel, base_normativa
from app.shared.pdf import USO_INTERNO, Bloco, Campo, Documento, Secao, data_hora

POSICOES = {
    "obstaculo": "Obstáculo relatado",
    "divergencia": "Divergência com o dado do Censo",
    "sem_relato": "Sem relato nesta versão",
}
_ROTULO_TEXTO = {"obstaculo": "Obstáculo confirmado pelo diretor", "divergencia": "Divergência descrita pelo diretor"}

RESSALVAS = [
    "Os dados do Censo Escolar são da edição indicada. As posições e os textos foram registrados e confirmados pelo diretor da escola.",
]


def eixos() -> dict[str, str]:
    """Código da barreira → nome do eixo, pela metodologia; sem a base, o PDF mostra o código do eixo."""
    try:
        return {codigo: regra.eixo_nome for codigo, regra in base_normativa.carregar().metodologia.items()}
    except BaseNormativaIndisponivel:
        return {}


def numero(valor: float) -> str:
    return f"{valor:g}".replace(".", ",")


def _publicacao(declaracao: Declaracao) -> str:
    if declaracao.retirada_em:
        return f"Publicação retirada em {data_hora(declaracao.retirada_em)}"
    if declaracao.publicada_em:
        return f"Publicada na página da escola em {data_hora(declaracao.publicada_em)}"
    return "Não publicada"


def _marca(declaracao: Declaracao) -> str:
    if declaracao.publicada_em and not declaracao.retirada_em:
        return f"Versão publicada em {data_hora(declaracao.publicada_em)}. A versão oficial para o público é a da página da escola."
    return USO_INTERNO


def documento(declaracao: Declaracao) -> Documento:
    escola = censo.escola(declaracao.co_entidade)
    nome = escola.nome if escola else f"INEP {declaracao.co_entidade}"
    local = f" — {escola.municipio}/{escola.uf}" if escola else ""
    nomes_eixo = eixos()
    posicoes = [i.posicao for i in declaracao.itens]
    return Documento(
        tipo="Declaração de Obstáculos",
        sujeito=f"{nome}{local} · INEP {declaracao.co_entidade}",
        versao=declaracao.versao,
        identificacao=[
            Campo("Emitida em", data_hora(declaracao.emitida_em)),
            Campo("Edição do Censo Escolar", declaracao.censo_versao),
            Campo("Versão da metodologia de barreiras", declaracao.metodologia_versao),
            Campo("Publicação", _publicacao(declaracao)),
        ],
        secoes=[
            Secao("Resumo", campos=[
                Campo("Barreiras encontradas nos dados do Censo", str(len(posicoes))),
                Campo("Posições registradas", (
                    f"{posicoes.count('obstaculo')} obstáculo(s) relatado(s); {posicoes.count('divergencia')} divergência(s) "
                    f"com o dado do Censo; {posicoes.count('sem_relato')} sem relato nesta versão"
                )),
            ]),
            Secao("Barreiras e posições", vazio="Nenhuma barreira nesta versão.", blocos=[
                Bloco(f"{i.codigo} · {i.barreira}", [
                    Campo("Eixo", nomes_eixo.get(i.codigo, i.eixo)),
                    Campo("Dado do Censo", i.dado_censo),
                    Campo("Pontos na metodologia", numero(i.pontos)),
                    Campo("Posição", POSICOES.get(i.posicao, i.posicao)),
                    Campo(_ROTULO_TEXTO.get(i.posicao, "Texto"), i.texto, livre=True),
                ])
                for i in declaracao.itens
            ]),
        ],
        ressalvas=RESSALVAS,
        congelado={
            "documento": "declaracao",
            "co_entidade": declaracao.co_entidade,
            "versao": declaracao.versao,
            "emitida_em": declaracao.emitida_em,
            "censo_versao": declaracao.censo_versao,
            "metodologia_versao": declaracao.metodologia_versao,
            "itens": [
                {"codigo": i.codigo, "eixo": i.eixo, "barreira": i.barreira, "dado_censo": i.dado_censo, "pontos": i.pontos,
                 "posicao": i.posicao, "texto": i.texto}
                for i in declaracao.itens
            ],
        },
        nome_arquivo=f"declaracao-obstaculos_{declaracao.co_entidade}_v{declaracao.versao}.pdf",
        alvo=("declaracao", declaracao.id),
        marca=_marca(declaracao),
    )
