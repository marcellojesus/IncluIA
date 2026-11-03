"""PDF de uma versão enviada do Plano de Ação Escolar (PDF-RF-02; RN-PDF-01 a 07).

O conteúdo vem só da versão congelada; a decisão e os apontamentos da secretaria aparecem como estão
no momento da geração, fora do código de conferência. Não aparece nome de pessoa: quem enviou também
não aparece na tela do secretário, e quem decidiu vira o papel (RN-PDF-06).
"""

from sqlalchemy.orm import object_session

from app.features.acesso import censo
from app.features.plano.fontes import citacoes
from app.features.plano.modelos import VersaoPlano
from app.features.plano.revisao import ultima_declaracao
from app.shared.pdf import Bloco, Campo, Documento, Secao, data_hora

ESTADOS = {
    "aguardando_analise": "Aguardando análise da secretaria",
    "aceito": "Aceito pela secretaria",
    "ajustes_solicitados": "Ajustes solicitados pela secretaria",
    "reprovado": "Reprovado pela secretaria",
}
HORIZONTES = {"LOA": "LOA — exercício corrente", "PPA": "PPA — horizonte de quatro anos"}

RESSALVAS = [
    "As ações marcadas como propostas pela IA foram revisadas e aceitas pelo diretor da escola.",
    "Custos são estimativas da escola.",
    "As fontes legais citadas ainda não foram validadas por especialista.",
]


def origem(item) -> str:
    if item.origem == "ia":
        return "Proposta pela IA e editada pelo diretor" if item.editada else "Proposta pela IA e aceita pelo diretor"
    return "Escrita pelo diretor"


def _identificacao(versao: VersaoPlano, ultima: int) -> list[Campo]:
    base = f"Versão {versao.declaracao_versao}"
    if ultima > versao.declaracao_versao:
        base += f". Atenção: a escola emitiu a versão {ultima} depois deste envio, e este plano se baseia na anterior."
    campos = [
        Campo("Enviada à secretaria em", data_hora(versao.submetida_em)),
        Campo("Declaração de Obstáculos usada como base", base),
        Campo("Situação", ESTADOS.get(versao.estado, versao.estado)),
    ]
    if versao.decidida_em:
        # Só o papel, não o nome: o PDF circula fora da plataforma e ainda não tem valor formal (decisão de 2026-11-03).
        campos.append(Campo("Decidida em", f"{data_hora(versao.decidida_em)}, pela Secretaria Municipal de Educação"))
    campos.append(Campo("Comentário da secretaria", versao.comentario, livre=True))
    if versao.publicada_em:
        situacao = (f"Publicação retirada em {data_hora(versao.retirada_em)}" if versao.retirada_em
                    else f"Publicado na página da escola em {data_hora(versao.publicada_em)}")
        campos.append(Campo("Publicação", situacao))
    return campos


def documento(versao: VersaoPlano) -> Documento:
    sessao = object_session(versao)
    escola = censo.escola(versao.co_entidade)
    nome = escola.nome if escola else f"INEP {versao.co_entidade}"
    local = f" — {escola.municipio}/{escola.uf}" if escola else ""
    fontes = citacoes({f for i in versao.itens for f in i.fontes or []})
    apontado = {a.item_id: a for a in versao.apontamentos if a.item_id}
    sobre_barreira = [a for a in versao.apontamentos if not a.item_id]
    nomes_barreira = {i.codigo: i.barreira for i in versao.itens}
    horizontes = [i.horizonte for i in versao.itens]

    blocos = []
    for n, item in enumerate(versao.itens, start=1):
        campos = [
            Campo("Ação", item.acao, livre=True),
            Campo("Como responde à Declaração", item.relacao, livre=True),
            Campo("Responsável", item.responsavel, livre=True),
            Campo("Prazo", item.prazo, livre=True),
            Campo("Horizonte", HORIZONTES.get(item.horizonte, item.horizonte)),
            Campo("Custo estimado", item.custo_estimado, livre=True),
            Campo("Premissas", item.premissas, livre=True),
            Campo("Fontes", "; ".join(fontes.get(f, f) for f in item.fontes or [])),
            Campo("Origem", origem(item)),
        ]
        if item.id in apontado:
            campos.append(Campo("Apontamento da secretaria", apontado[item.id].texto or "Ação marcada para ajuste.", livre=True))
        blocos.append(Bloco(f"Ação {n} · {item.codigo} {item.barreira}", campos))

    secoes = [
        Secao("Resumo", campos=[
            Campo("Ações", f"{len(horizontes)} ({horizontes.count('LOA')} LOA; {horizontes.count('PPA')} PPA)"),
            Campo("Barreiras com ação", str(len({i.codigo for i in versao.itens}))),
        ]),
        Secao("Ações por barreira", blocos=blocos, vazio="Nenhuma ação nesta versão."),
    ]
    if sobre_barreira:
        secoes.append(Secao("Apontamentos da secretaria sobre barreiras", blocos=[
            Bloco(f"{a.codigo} {nomes_barreira.get(a.codigo, '')}".strip(),
                  [Campo("Apontamento", a.texto or "Barreira marcada para ajuste.", livre=True)])
            for a in sobre_barreira
        ]))

    return Documento(
        tipo="Plano de Ação Escolar",
        sujeito=f"{nome}{local} · INEP {versao.co_entidade}",
        versao=versao.versao,
        identificacao=_identificacao(versao, ultima_declaracao(sessao, versao.co_entidade) if sessao else 0),
        secoes=secoes,
        ressalvas=RESSALVAS,
        congelado={
            "documento": "plano_escolar",
            "co_entidade": versao.co_entidade,
            "versao": versao.versao,
            "declaracao_versao": versao.declaracao_versao,
            "submetida_em": versao.submetida_em,
            "itens": [
                {"codigo": i.codigo, "barreira": i.barreira, "acao": i.acao, "relacao": i.relacao, "responsavel": i.responsavel,
                 "prazo": i.prazo, "horizonte": i.horizonte, "custo_estimado": i.custo_estimado, "premissas": i.premissas,
                 "fontes": i.fontes or [], "origem": i.origem, "editada": i.editada}
                for i in versao.itens
            ],
        },
        nome_arquivo=f"plano-acao-escolar_{versao.co_entidade}_v{versao.versao}.pdf",
        alvo=("plano", versao.id),
    )
