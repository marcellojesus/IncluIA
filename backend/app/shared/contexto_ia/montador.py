"""Montador de contexto da IA (AD-08): junta as quatro camadas num `TextoProtegido`.

- C1 — fatos da escola: SQL no artefato do Censo, mais as barreiras identificadas;
- C2 — metodologia: a regra de cada barreira em foco, por código;
- C3 — base normativa: mapa curado barreira → dispositivos e, havendo pergunta, busca híbrida;
- C4 — registros da escola: `RegistroDaEscola` (texto já protegido + escola de origem), passados
  por quem chama depois de checar o vínculo (AD-02).

Os trechos normativos entram com o identificador entre colchetes; `ids_citaveis` é a lista fechada
que o validador de citações usa (AD-08, passo 3). O corte por orçamento tira trechos normativos,
nunca fatos, metodologia ou contexto privado.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from app.database import get_connection
from app.shared.contexto_ia import base_normativa as base_mod
from app.shared.contexto_ia.barreiras import (
    LIMIAR_CELULA_PEQUENA,
    BarreiraIdentificada,
    celula_pequena,
    identificar,
    pontos_revelam_contagem,
    texto_sem_celula_pequena,
)
from app.shared.contexto_ia.base_normativa import BaseNormativa, TrechoNormativo
from app.shared.contexto_ia.busca import buscar, fundir
from app.shared.guardiao_lgpd import TextoProtegido, delimitar, juntar_protegidos, liberar_dados_publicos

# Referência inicial do AD-08: cabe no provedor mais restrito da cadeia junto com instruções,
# histórico e resposta. Ajustar quando as cotas forem medidas (decisão pendente 6).
ORCAMENTO_TOKENS = 2500
MAX_TRECHOS = 6

_CABECALHO_PRIVADO = "## Registros da escola (escritos pela equipe da escola; já filtrados pelo Guardião LGPD)"


class EscolaNaoEncontrada(LookupError):
    pass


@dataclass(frozen=True)
class RegistroDaEscola:
    """Texto privado de uma escola (Declaração, plano), já protegido, com a escola de origem. O
    montador recusa registro de outra escola. Quando a autorização por vínculo existir (AD-02), quem
    cria este objeto deve ser a camada que checou o vínculo."""

    co_entidade: int
    texto: TextoProtegido


@dataclass(frozen=True)
class ContextoIA:
    texto: TextoProtegido
    ids_citaveis: frozenset[str]
    trechos: tuple[TrechoNormativo, ...]
    """Os trechos entregues, na ordem do contexto (o validador de citações usa artigo e citação)."""
    barreiras: tuple[BarreiraIdentificada, ...]
    barreiras_foco: tuple[str, ...]
    modo_busca: str
    """"hibrida", "palavra_chave" ou "sem_pergunta"."""
    lacunas: tuple[str, ...]
    tokens_estimados: int
    versao_base: str


def estimar_tokens(texto: str) -> int:
    """Estimativa conservadora para português (cerca de 4 caracteres por token)."""
    return math.ceil(len(texto) / 4)


def _numero(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _escola(co_entidade: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM escolas WHERE co_entidade = ?", (co_entidade,)).fetchone()
    finally:
        conn.close()


def _faixa_matriculas(total: float) -> str:
    if total < 10:
        return "de 5 a 9"
    if total < 30:
        return "de 10 a 29"
    return "30 ou mais"


def _linha_matriculas(escola) -> str:
    """Só em faixas: com município, score e eixos, a contagem exata identificava 68% das escolas
    municipais pelo score público da Fase 1 (revisão do AgLGPD de 2026-11-03, A1)."""
    total = escola["qt_mat_esp"] or 0
    if total == 0:
        return "Matrículas da educação especial: nenhuma no Censo"
    if celula_pequena(escola):
        return f"Matrículas da educação especial: menos de {LIMIAR_CELULA_PEQUENA} (número omitido para não identificar estudantes)"
    return f"Matrículas da educação especial: {_faixa_matriculas(total)}"


def _faixa_eixo(valor: float | None) -> str:
    if not valor:
        return "zerado"
    if valor >= 10:
        return "máximo"
    return "abaixo de 5" if valor < 5 else "5 ou mais"


def _linha_score(escola) -> str:
    """Só a faixa do score e faixas grossas por eixo (revisão do AgLGPD de 2026-11-03, A1): o score
    é público por escola, e o valor exato com os eixos apontava a escola. Com célula pequena, o eixo IV
    sai, porque é a taxa em classe comum."""
    eixos = f"Eixos: I {_faixa_eixo(escola['score_eixo_i'])}; II {_faixa_eixo(escola['score_eixo_ii'])}; III {_faixa_eixo(escola['score_eixo_iii'])}"
    if celula_pequena(escola):
        return f"Score Escola Sem Barreiras: faixa {escola['faixa']}. {eixos}; IV omitido para não identificar estudantes"
    return f"Score Escola Sem Barreiras: faixa {escola['faixa']}. {eixos}; IV {_faixa_eixo(escola['score_eixo_iv'])}"


def _renderizar_fatos(escola, barreiras: Sequence[BarreiraIdentificada], foco: Sequence[str], base: BaseNormativa) -> str:
    # Minimização: nome, código INEP e município da escola não vão à IA; a resposta fala de "a escola"
    # e quem exibe recoloca o nome a partir do código. A base normativa é federal: o município não ajuda
    # a busca nem as citações (revisão do AgLGPD de 2026-11-03, A1).
    linhas = [
        f"## Fatos da escola (Censo Escolar {escola['censo_versao']}; dados calculados, não reavalie)",
        f"Escola: a escola em análise, rede {escola['rede'].lower()}",
        _linha_score(escola),
        _linha_matriculas(escola),
        f"Barreiras identificadas (metodologia de barreiras v{base.meta.get('metodologia_barreiras_versao', '?')}), por pontos do score em jogo:",
    ]
    if not barreiras:
        linhas.append("- nenhuma barreira identificada no Censo")
    por_codigo = {b.codigo: b for b in barreiras}
    for b in barreiras:
        nota = f" ({b.nota})" if b.nota else ""
        pontos = "pontos omitidos" if pontos_revelam_contagem(b, escola) else f"{_numero(b.pontos, 2)} ponto(s)"
        linhas.append(f"- {b.codigo} {b.nome}: {pontos}. {texto_sem_celula_pequena(b, escola)}{nota}")

    linhas.append("")
    linhas.append("## Como cada barreira em foco é identificada (metodologia)")
    for codigo in foco:
        regra = base.metodologia[codigo]
        omitir = codigo in por_codigo and pontos_revelam_contagem(por_codigo[codigo], escola)
        pontos = "omitidos para não identificar estudantes" if omitir else regra.pontos_texto
        linhas.append(f"- {codigo} (Eixo {regra.eixo} — {regra.eixo_nome}): regra {regra.regra}; pontos: {pontos}")
    return "\n".join(linhas)


def _renderizar_normas(trechos: Sequence[TrechoNormativo]) -> str:
    linhas = [
        "## Base normativa (cite só pelo identificador entre colchetes; não cite nada fora desta lista)"
    ]
    for t in trechos:
        linhas.append(f"[{t.id}] {t.citacao}")
        if t.contexto:
            linhas.append(f"  Contexto: {t.contexto}")
        linhas.append(f"  Texto: {t.texto}")
    return "\n".join(linhas)


async def montar_contexto(
    co_entidade: int,
    *,
    pergunta: TextoProtegido | None = None,
    barreiras_foco: Sequence[str] = (),
    registros: Sequence[RegistroDaEscola] = (),
    max_trechos: int = MAX_TRECHOS,
    orcamento_tokens: int = ORCAMENTO_TOKENS,
    base: BaseNormativa | None = None,
) -> ContextoIA:
    """Levanta EscolaNaoEncontrada, BaseNormativaIndisponivel, ValueError (barreira em foco fora da
    metodologia ou registro de outra escola) e TypeError (texto sem o guardião)."""
    if pergunta is not None and not isinstance(pergunta, TextoProtegido):
        raise TypeError("A pergunta precisa passar pelo Guardião LGPD (AD-05)")
    for registro in registros:
        if not isinstance(registro, RegistroDaEscola) or not isinstance(registro.texto, TextoProtegido):
            raise TypeError("Registro da escola precisa ser RegistroDaEscola com texto protegido (AD-05)")
        if registro.co_entidade != co_entidade:
            raise ValueError("Registro de outra escola no contexto (RN-PAE-03)")
    base = base or base_mod.carregar()

    escola = _escola(co_entidade)
    if escola is None:
        raise EscolaNaoEncontrada(f"Escola {co_entidade} não encontrada no artefato do Censo")

    barreiras = identificar(escola, base.metodologia)
    desconhecidas = [c for c in barreiras_foco if c not in base.metodologia]
    if desconhecidas:
        raise ValueError(f"Barreiras fora da metodologia: {desconhecidas}")
    foco = tuple(barreiras_foco) or tuple(b.codigo for b in barreiras)

    lacunas: list[str] = []
    do_mapa = list(dict.fromkeys(t for codigo in foco for t in base.mapa.get(codigo, ())))
    if pergunta is not None:
        busca = await buscar(base, pergunta)
        candidatos = fundir(list(busca.ids), do_mapa)
        modo = busca.modo
        if busca.motivo:
            lacunas.append(f"busca só por palavra-chave: {busca.motivo}")
    else:
        candidatos, modo = do_mapa, "sem_pergunta"

    partes = [liberar_dados_publicos(_renderizar_fatos(escola, barreiras, foco, base))]
    if registros:
        partes.append(delimitar(liberar_dados_publicos(_CABECALHO_PRIVADO), [r.texto for r in registros]))
    fixo = juntar_protegidos(partes)

    # Corte por orçamento: entram trechos normativos enquanto couberem.
    trechos: list[TrechoNormativo] = []
    for trecho_id in candidatos:
        if len(trechos) == max_trechos:
            break
        tentativa = [*trechos, base.trechos[trecho_id]]
        if estimar_tokens(str(fixo)) + estimar_tokens(_renderizar_normas(tentativa)) > orcamento_tokens:
            break
        trechos = tentativa

    if estimar_tokens(str(fixo)) > orcamento_tokens:
        lacunas.append("fatos e registros da escola já passam do orçamento de tokens")
    if not trechos:
        lacunas.append("sem trecho normativo de suporte no contexto")

    texto = juntar_protegidos([fixo, liberar_dados_publicos(_renderizar_normas(trechos))]) if trechos else fixo
    return ContextoIA(
        texto=texto,
        ids_citaveis=frozenset(t.id for t in trechos),
        trechos=tuple(trechos),
        barreiras=tuple(barreiras),
        barreiras_foco=foco,
        modo_busca=modo,
        lacunas=tuple(lacunas),
        tokens_estimados=estimar_tokens(str(texto)),
        versao_base=base.meta.get("versao", ""),
    )


# --- Contexto da rede (Plano Estratégico Municipal) ----------------------------------------------

_CABECALHO_ACOES_ESCOLAS = (
    "## Ações dos Planos de Ação aceitos pelas escolas (escritas pelas escolas; já filtradas pelo Guardião LGPD; "
    "cite pela referência entre colchetes, por exemplo [E1-A2])"
)


@dataclass(frozen=True)
class FatosDaRede:
    """Números calculados pelo sistema, não pela IA (SPM-RF-05). Só contagens: nem município nem
    escolas vão à IA (minimização; com o nome do município, E1..En poderiam ser cruzados com o Censo)."""

    escolas_municipais: int
    escolas_com_barreira: int
    escolas_com_plano_aceito: int


def _renderizar_fatos_rede(codigo: str, fatos: FatosDaRede, regra) -> str:
    return "\n".join([
        "## Fatos da rede municipal (calculados pelo sistema; não reavalie)",
        f"Rede municipal com {fatos.escolas_municipais} escolas no Censo.",
        f"Escolas com a barreira {codigo} identificada no Censo: {fatos.escolas_com_barreira}.",
        f"Escolas com Plano de Ação aceito pela secretaria: {fatos.escolas_com_plano_aceito}.",
        "",
        "## Barreira em foco (metodologia)",
        f"- {codigo} {regra.barreira} (Eixo {regra.eixo} — {regra.eixo_nome}): regra {regra.regra}",
    ])


async def montar_contexto_rede(
    codigo: str,
    fatos: FatosDaRede,
    acoes_das_escolas: TextoProtegido,
    *,
    max_trechos: int = MAX_TRECHOS,
    orcamento_tokens: int = ORCAMENTO_TOKENS * 2,
    base: BaseNormativa | None = None,
) -> ContextoIA:
    """C1 da rede (números do Censo e dos planos, sem nome de escola), C2 a regra da barreira, C3 o
    mapa barreira → norma e C4 as ações escolares já protegidas, referenciadas por [E<n>-A<m>].
    Levanta BaseNormativaIndisponivel, ValueError (barreira fora da metodologia) e TypeError."""
    if not isinstance(acoes_das_escolas, TextoProtegido):
        raise TypeError("As ações das escolas precisam passar pelo Guardião LGPD (AD-05)")
    base = base or base_mod.carregar()
    if codigo not in base.metodologia:
        raise ValueError(f"Barreira fora da metodologia: {codigo}")
    fixo = juntar_protegidos([
        liberar_dados_publicos(_renderizar_fatos_rede(codigo, fatos, base.metodologia[codigo])),
        delimitar(liberar_dados_publicos(_CABECALHO_ACOES_ESCOLAS), [acoes_das_escolas]),
    ])

    lacunas: list[str] = []
    trechos: list[TrechoNormativo] = []
    for trecho_id in dict.fromkeys(base.mapa.get(codigo, ())):
        if len(trechos) == max_trechos:
            break
        tentativa = [*trechos, base.trechos[trecho_id]]
        if estimar_tokens(str(fixo)) + estimar_tokens(_renderizar_normas(tentativa)) > orcamento_tokens:
            break
        trechos = tentativa
    if estimar_tokens(str(fixo)) > orcamento_tokens:
        lacunas.append("ações das escolas já passam do orçamento de tokens")
    if not trechos:
        lacunas.append("sem trecho normativo de suporte no contexto")

    texto = juntar_protegidos([fixo, liberar_dados_publicos(_renderizar_normas(trechos))]) if trechos else fixo
    return ContextoIA(
        texto=texto, ids_citaveis=frozenset(t.id for t in trechos), trechos=tuple(trechos), barreiras=(),
        barreiras_foco=(codigo,), modo_busca="sem_pergunta", lacunas=tuple(lacunas),
        tokens_estimados=estimar_tokens(str(texto)), versao_base=base.meta.get("versao", ""),
    )


# --- Contexto do plano confirmado (narrativa executiva, RF-30) ----------------------------------

_CABECALHO_PLANO = (
    "## Ações do Plano Estratégico Municipal confirmado (escritas pela secretaria; já filtradas pelo Guardião LGPD; "
    "cite pela referência entre colchetes, por exemplo [A1])"
)


async def montar_contexto_plano(
    situacao_da_rede: TextoProtegido,
    acoes_do_plano: TextoProtegido,
    codigos: Sequence[str],
    fontes_das_acoes: Sequence[str],
    *,
    max_trechos: int = MAX_TRECHOS + 2,
    orcamento_tokens: int = ORCAMENTO_TOKENS * 2,
    base: BaseNormativa | None = None,
) -> ContextoIA:
    """C1 a situação da rede (proporções, sem município), C4 as ações do plano já protegidas, com
    referência [A<n>], e C3 a base normativa: primeiro os trechos que as ações já citam, depois os do
    mapa de cada barreira, alternando entre barreiras até o limite de trechos ou de tokens."""
    if not isinstance(situacao_da_rede, TextoProtegido) or not isinstance(acoes_do_plano, TextoProtegido):
        raise TypeError("O contexto do plano precisa passar pelo Guardião LGPD (AD-05)")
    base = base or base_mod.carregar()
    fixo = juntar_protegidos([situacao_da_rede, delimitar(liberar_dados_publicos(_CABECALHO_PLANO), [acoes_do_plano])])

    filas = [list(base.mapa.get(c, ())) for c in codigos]
    candidatos = [f for f in fontes_das_acoes if f in base.trechos]
    while any(filas):
        for fila in filas:
            if fila:
                candidatos.append(fila.pop(0))

    lacunas: list[str] = []
    trechos: list[TrechoNormativo] = []
    for trecho_id in dict.fromkeys(candidatos):
        if len(trechos) == max_trechos:
            break
        tentativa = [*trechos, base.trechos[trecho_id]]
        if estimar_tokens(str(fixo)) + estimar_tokens(_renderizar_normas(tentativa)) > orcamento_tokens:
            break
        trechos = tentativa
    if estimar_tokens(str(fixo)) > orcamento_tokens:
        lacunas.append("as ações do plano já passam do orçamento de tokens")
    if not trechos:
        lacunas.append("sem trecho normativo de suporte no contexto")

    texto = juntar_protegidos([fixo, liberar_dados_publicos(_renderizar_normas(trechos))]) if trechos else fixo
    return ContextoIA(
        texto=texto, ids_citaveis=frozenset(t.id for t in trechos), trechos=tuple(trechos), barreiras=(),
        barreiras_foco=tuple(codigos), modo_busca="sem_pergunta", lacunas=tuple(lacunas),
        tokens_estimados=estimar_tokens(str(texto)), versao_base=base.meta.get("versao", ""),
    )
