"""Narrativa executiva do Plano Estratégico Municipal (RF-30; SPM-RF-05; RN-SPM-04).

A IA escreve, a partir de uma versão confirmada, um texto para quem decide o orçamento (prefeitura,
câmara, conselho): resumo, situação da rede, estratégia, fundamentação legal, próximos passos e
incertezas. Ela recebe a situação da rede em faixas ("a maioria das escolas", calculadas a partir
das proporções do Analítico), as ações da versão com referência [A<n>] e os trechos da base
normativa. Nem município, nem escolas, nem valores de custo vão à IA: o custo vai só como
"estimativa registrada pela secretaria" ou "a estimar".

Revisão do AgLGPD (2026-10-27), aplicada:
- o Guardião não mascara nome de escola ("EMEF Santa Rita") nem município composto, que ele trata
  como nomes públicos; por isso os nomes do município, das escolas e dos bairros, e códigos INEP, saem
  do texto das ações na camada de locais do Guardião (`proteger_para_ia`, desde 2026-11-03), e a
  resposta que trouxer um deles é recusada (`contem_local`);
- ação ligada a escola pequena numa barreira sensível (classe exclusiva ou poucas escolas), ou a
  escola cujo plano da base ou cuja Declaração foi retirado por motivo LGPD, vai só com a linha
  estruturada, sem o texto livre (mesma regra do Analítico);
- premissas e justificativa não vão (minimização: foram escritas a partir de planos escolares);
- cada geração grava a trilha do que foi enviado, sem texto, e gera evento de auditoria.

O texto não traz números: o validador recusa valor em reais, percentual e contagem de escolas ou
alunos, e a cadeia passa ao próximo provedor. Os números ao lado do texto são calculados pelo sistema
a partir da versão congelada (`numeros`). Custos e projeções do RF-30 ficam como estimativas da
secretaria até haver fonte de custo definida (decisões pendentes 12 e 13 do PRD).
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.acesso.modelos import EventoAuditoria
from app.features.analitico import base as base_analitica
from app.features.analitico import sintese as sintese_analitica
from app.features.declaracao.modelos import Declaracao
from app.features.plano.modelos import VersaoPlano
from app.features.plano.publicacao import MOTIVOS_LGPD
from app.features.plano.servico import ErroPlano, _campo
from app.features.plano.sugestoes import _Mascara
from app.features.plano_municipal import base as base_rede
from app.features.plano_municipal.modelos import NarrativaPlanoMunicipal, VersaoPlanoMunicipal
from app.shared import ai_client
from app.shared.contexto_ia import INSTRUCOES_CITACAO, gerar_resposta_fundamentada, montar_contexto_plano
from app.shared.contexto_ia.barreiras import CLASSE_EXCLUSIVA, celula_pequena
from app.features.acesso import censo
from app.shared.guardiao_lgpd import (
    SEM_LOCAIS,
    Locais,
    TextoBloqueado,
    contem_local,
    juntar_protegidos,
    liberar_dados_publicos,
    proteger_para_ia,
)

INSTRUCOES_NARRATIVA = """Você apoia a secretaria municipal de educação a apresentar o Plano Estratégico Municipal de educação
inclusiva a quem decide o orçamento (prefeitura, câmara, conselho de educação). Recebe a situação da rede, calculada pelo
sistema, e as ações do plano já confirmado pela secretaria, cada uma com uma referência [A1].

Escreva uma narrativa executiva em português claro, para leitor não especialista:
- "resumo": de 3 a 5 frases com o problema, a resposta do plano e o que se pede de quem decide.
- "situacao": o que os dados mostram sobre as barreiras da rede, sem números.
- "estrategia": de 2 a 6 blocos; cada um agrupa ações que respondem a um mesmo problema, explica o porquê e lista em
  "acoes" as referências (como "A1") das ações que agrupa. Toda ação do plano deve aparecer em algum bloco.
- "fundamentacao": por que o plano cumpre o que a norma exige, citando os trechos da base normativa pelo identificador.
- "proximos_passos": o que precisa acontecer para o plano sair do papel (dotação na LOA ou no PPA, contratações,
  definição de custos), sem prazos ou valores que não estejam nas ações.
- "incertezas": o que o plano ainda não sabe (custos a estimar, dados que faltam).
Ação marcada como "ação localizada" teve o texto retido por proteção de dados: mencione-a só pela barreira que enfrenta.
Não escreva valores em reais, percentuais nem quantidades de escolas, alunos ou profissionais: o sistema mostra os números
ao lado do texto. Não cite escola nem município. Confirmar o plano não é aprovar orçamento nem executar: não diga que algo
foi financiado ou feito. Linguagem factual e neutra, sem culpar pessoas, escolas ou órgãos.

Responda APENAS com um JSON válido, sem markdown, neste formato:
{"resumo": "...", "situacao": "...", "estrategia": [{"texto": "...", "acoes": ["A1", "A2"]}], "fundamentacao": "... [identificador]",
 "proximos_passos": "...", "incertezas": ["..."], "fontes": ["identificador"], "lacunas": ["..."]}"""

PEDIDO_NARRATIVA = "Escreva a narrativa executiva do plano municipal a partir do contexto."

_REF_ACAO = re.compile(r"\[?\bA(\d{1,3})\b\]?")
_NUMERO_PROIBIDO = re.compile(
    r"R\$|\d[\d.,]*\s*(?:%|por\s*cento|mil\b|milh|bilh|escolas?\b|alunos?\b|alunas?\b|estudantes?\b|matr[íi]culas?\b|"
    r"profissionais?\b|professor(?:es|as?)?\b|crian[çc]as?\b|turmas?\b|salas?\b|unidades?\b)",
    re.IGNORECASE,
)
_SEM_CUSTO = {"", "a estimar"}


class Bloco(BaseModel):
    texto: str = Field(max_length=1200)
    acoes: list[str] = Field(default_factory=list, max_length=40)


class RespostaNarrativa(BaseModel):
    resumo: str = Field(max_length=1500)
    situacao: str = Field(default="", max_length=1500)
    estrategia: list[Bloco] = Field(min_length=1, max_length=8)
    fundamentacao: str = Field(default="", max_length=1500)
    proximos_passos: str = Field(default="", max_length=1200)
    incertezas: list[str] = Field(default_factory=list, max_length=6)
    fontes: list[str] = Field(default_factory=list, max_length=10)
    lacunas: list[str] = Field(default_factory=list, max_length=5)


class NarrativaReprovada(ai_client.RespostaReprovada):
    """Ação inexistente, número ou nome de local no texto; a cadeia segue para o próximo provedor."""


# --- Validação da resposta --------------------------------------------------------------------

def _textos(resposta: RespostaNarrativa) -> list[str]:
    return [resposta.resumo, resposta.situacao, resposta.fundamentacao, resposta.proximos_passos,
            *(b.texto for b in resposta.estrategia), *resposta.incertezas, *resposta.lacunas]


def conferir(resposta: RespostaNarrativa, total_acoes: int, nomes: Locais = SEM_LOCAIS) -> None:
    """Referências [A<n>] só das ações da versão; nenhum número de custo, proporção ou contagem
    (SPM-RF-05); nenhum nome do município ou das escolas. A mensagem diz só o tipo do problema."""
    citadas = [int(n) for t in _textos(resposta) for n in _REF_ACAO.findall(t)]
    citadas += [int(m) for b in resposta.estrategia for a in b.acoes for m in _REF_ACAO.findall(a)]
    if any(not 1 <= n <= total_acoes for n in citadas):
        raise NarrativaReprovada("referência a ação fora do plano")
    for texto in _textos(resposta):
        if _NUMERO_PROIBIDO.search(texto):
            raise NarrativaReprovada("número no texto")
        if contem_local(texto, nomes):
            raise NarrativaReprovada("nome de escola ou município no texto")


# --- O que vai à IA ---------------------------------------------------------------------------

def _faixa(percentual: int) -> str:
    if percentual >= 90:
        return "quase todas as escolas"
    if percentual >= 60:
        return "a maioria das escolas"
    if percentual >= 40:
        return "cerca de metade das escolas"
    return "uma parte das escolas"


def sem_percentuais(texto: str) -> str:
    """"cerca de 40% das escolas" → "cerca de metade das escolas": sem número no contexto, a IA não o copia."""
    return re.sub(r"cerca de (\d+)% das escolas", lambda m: _faixa(int(m.group(1))), texto)


def _tem_custo(acao: dict) -> bool:
    return (acao.get("custo_estimado") or "").strip().lower() not in _SEM_CUSTO


@dataclass(frozen=True)
class Restricoes:
    nomes: Locais
    """Nomes da rede, para a camada de locais do Guardião (pendência 16)."""
    pequenas: frozenset[int]
    """Escolas com 1 a 4 matrículas da educação especial."""
    retiradas: frozenset[int]
    """Escolas com plano da base ou última Declaração retirados por motivo LGPD."""


def _restricoes(sessao: Session, versao: VersaoPlanoMunicipal) -> Restricoes:
    linhas = base_rede._escolas_municipais(versao.co_municipio)
    retiradas = {
        co for co, d in base_analitica._ultimas(sessao, Declaracao, versao.co_municipio).items() if d.retirada_motivo in MOTIVOS_LGPD
    }
    for p in (versao.base or {}).get("planos", []):
        plano = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == p["co_entidade"], VersaoPlano.versao == p["versao"]))
        if plano is not None and plano.retirada_motivo in MOTIVOS_LGPD:
            retiradas.add(p["co_entidade"])
    return Restricoes(
        nomes=censo.locais_da_rede(versao.co_municipio),
        pequenas=frozenset(linha["co_entidade"] for linha in linhas if celula_pequena(linha)), retiradas=frozenset(retiradas),
    )


def motivo_restricao(acao: dict, restricoes: Restricoes) -> str | None:
    """Por que o texto livre da ação não vai à IA (None quando vai). Mesma regra de `analitico.sintese._vai_a_ia`."""
    escolas = {e["co_entidade"] for e in acao.get("escolas") or []}
    if escolas & restricoes.retiradas:
        return "retirada_lgpd"
    sensivel = CLASSE_EXCLUSIVA in (acao.get("codigos") or []) or len(escolas) < sintese_analitica.POUCAS_ESCOLAS
    if escolas & restricoes.pequenas and sensivel:
        return "escola_pequena"
    return None


def _linha(n: int, acao: dict, total_escolas: int, restricoes: Restricoes) -> str:
    escolas = acao.get("escolas") or []
    restrita = motivo_restricao(acao, restricoes) is not None
    if not escolas:
        alcance = "ação sistêmica, sem escola vinculada"
    elif restrita:
        alcance = "ação localizada"
    else:
        alcance = f"atende {sem_percentuais(sintese_analitica._proporcao(len(escolas), total_escolas))} da rede" + (
            "; cobertura parcial em parte delas" if any(e.get("cobertura") == "parcial" for e in escolas) else ""
        )
    partes = [
        f"[A{n}]",
        # Texto livre retido: só a linha estruturada (revisão do AgLGPD, B2 e R1).
        "Ação localizada da secretaria (texto retido por proteção de dados)." if restrita else acao["acao"],
        f"Barreiras: {', '.join(acao.get('codigos') or [])}. Horizonte {acao['horizonte']}; prioridade {acao.get('prioridade', 'media')}; {alcance}.",
        acao.get("responsavel") and not restrita and f"Responsável: {acao['responsavel']}.",
        acao.get("prazo") and f"Prazo: {acao['prazo']}.",
        # O valor não vai: só se a secretaria registrou uma estimativa.
        "Custo: estimativa registrada pela secretaria." if _tem_custo(acao) else "Custo: a estimar.",
    ]
    return " ".join(p for p in partes if p)


# --- Números, leitura e geração ---------------------------------------------------------------

@dataclass(frozen=True)
class Numeros:
    """Calculados pelo sistema a partir da versão congelada; a IA não os vê nem os escreve."""

    acoes: int
    barreiras: int
    escolas_atendidas: int
    escolas_municipais: int
    loa: int
    ppa: int
    prioridade_alta: int
    com_custo_estimado: int
    com_cobertura_parcial: int


def numeros(versao: VersaoPlanoMunicipal, escolas_municipais: int) -> Numeros:
    acoes = versao.acoes
    return Numeros(
        acoes=len(acoes), barreiras=len({c for a in acoes for c in a.get("codigos") or []}),
        escolas_atendidas=len({e["co_entidade"] for a in acoes for e in a.get("escolas") or []}), escolas_municipais=escolas_municipais,
        loa=sum(a["horizonte"] == "LOA" for a in acoes), ppa=sum(a["horizonte"] == "PPA" for a in acoes),
        prioridade_alta=sum(a.get("prioridade") == "alta" for a in acoes), com_custo_estimado=sum(_tem_custo(a) for a in acoes),
        com_cobertura_parcial=sum(any(e.get("cobertura") == "parcial" for e in a.get("escolas") or []) for a in acoes),
    )


def da_versao(sessao: Session, co_municipio: int, numero: int) -> NarrativaPlanoMunicipal | None:
    return sessao.scalar(
        select(NarrativaPlanoMunicipal).where(NarrativaPlanoMunicipal.co_municipio == co_municipio, NarrativaPlanoMunicipal.versao == numero)
    )


def _com_fuso(momento: datetime) -> datetime:
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


def _auditar(sessao: Session, autor_id: str, acao: str, versao: VersaoPlanoMunicipal, detalhe: str) -> None:
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao=acao, alvo_tipo="plano_municipal", alvo_id=str(versao.co_municipio), resultado="ok",
        detalhe=f"município {versao.co_municipio} v{versao.versao}; {detalhe}",
    ))


async def gerar(sessao: Session, *, versao: VersaoPlanoMunicipal, autor_id: str) -> tuple[NarrativaPlanoMunicipal, bool]:
    """Levanta ErroPlano (contexto bloqueado) e RuntimeError (nenhum provedor respondeu)."""
    rede = base_analitica.montar(sessao, versao.co_municipio)
    restricoes = _restricoes(sessao, versao)

    # Cada ação passa pelo Guardião; a que bloquear fica de fora e vira incerteza.
    protegidas, enviadas, fora, retidas, mascaradas = [], [], [], [], 0
    for n, acao in enumerate(versao.acoes, start=1):
        # Nomes da rede e códigos INEP saem na camada de locais do Guardião (pendência 16).
        resultado = proteger_para_ia(_linha(n, acao, len(rede.escolas), restricoes), restricoes.nomes)
        if resultado.texto_protegido is None:
            fora.append({"id": acao.get("id"), "motivo": "guardiao"})
            continue
        mascaradas += bool(resultado.trechos)
        protegidas.append(resultado.texto_protegido)
        enviadas.append(acao.get("id"))
        if motivo := motivo_restricao(acao, restricoes):
            retidas.append({"id": acao.get("id"), "motivo": motivo})
    if not protegidas:
        raise ErroPlano("As ações do plano têm dado sensível e não podem ir ao assistente.", 409)

    codigos = list(dict.fromkeys(c for a in versao.acoes for c in a.get("codigos") or []))
    fontes = list(dict.fromkeys(f for a in versao.acoes for f in a.get("fontes") or []))
    try:
        contexto = await montar_contexto_plano(
            liberar_dados_publicos(sem_percentuais(sintese_analitica.renderizar_rede(rede))), juntar_protegidos(protegidas, "\n"), codigos, fontes,
        )
        sistema = juntar_protegidos([liberar_dados_publicos(INSTRUCOES_NARRATIVA), liberar_dados_publicos(INSTRUCOES_CITACAO), contexto.texto])
    except TextoBloqueado:
        raise ErroPlano("O contexto do plano tem dado sensível; revise as ações municipais.", 409) from None
    mensagens = [{"role": "user", "content": liberar_dados_publicos(PEDIDO_NARRATIVA)}]

    resposta, modelo = await gerar_resposta_fundamentada(
        sistema, mensagens, RespostaNarrativa, contexto, validar_extra=lambda r: conferir(r, len(versao.acoes), restricoes.nomes),
    )

    mascarar = _Mascara()
    incertezas = [t for t in (mascarar(i) for i in resposta.incertezas) if t]
    if fora:
        incertezas.append(f"{len(fora)} ação(ões) com dado sensível ficaram fora do texto.")
    if retidas:
        incertezas.append(f"{len(retidas)} ação(ões) entraram só pela barreira, sem o texto, por proteção de dados das escolas.")
    agora = datetime.now(timezone.utc)
    anterior = da_versao(sessao, versao.co_municipio, versao.versao)
    conteudo = {
        "resumo": mascarar(resposta.resumo) or "", "situacao": mascarar(resposta.situacao) or "",
        "estrategia": [
            {"texto": texto, "acoes": [f"A{n}" for n in dict.fromkeys(int(m) for a in b.acoes for m in _REF_ACAO.findall(a))]}
            for b in resposta.estrategia if (texto := mascarar(b.texto))
        ],
        "fundamentacao": mascarar(resposta.fundamentacao) or "", "proximos_passos": mascarar(resposta.proximos_passos) or "",
        "incertezas": incertezas, "lacunas": [t for t in (mascarar(l) for l in resposta.lacunas) if t],
        "fontes": list(dict.fromkeys(f.strip("[]") for f in resposta.fontes)),
        # Trilha do que foi à IA, sem texto, preservada entre gerações (revisão do AgLGPD, R2).
        "trilha": [*(anterior.conteudo.get("trilha") or [] if anterior else []), {
            "em": agora.isoformat(), "modelo": modelo, "acoes_enviadas": enviadas, "so_estrutura": retidas, "fora": fora,
            "trechos": [t.id for t in contexto.trechos], "mascaradas": mascaradas,
        }],
    }

    narrativa = anterior or NarrativaPlanoMunicipal(co_municipio=versao.co_municipio, versao=versao.versao)
    if anterior is None:
        sessao.add(narrativa)
    narrativa.conteudo, narrativa.modelo, narrativa.gerada_por = conteudo, modelo, autor_id
    narrativa.gerada_em, narrativa.editada = agora, False
    _auditar(sessao, autor_id, "narrativa_plano_municipal_gerada", versao,
             f"{len(enviadas)} ação(ões) enviada(s), {len(retidas)} só pela barreira, {len(fora)} fora")
    sessao.commit()
    return narrativa, mascarar.alterou or mascaradas > 0


@dataclass(frozen=True)
class EdicaoNarrativa:
    resumo: str
    situacao: str | None
    estrategia: tuple[tuple[str, tuple[str, ...]], ...]
    fundamentacao: str | None
    proximos_passos: str | None
    incertezas: tuple[str, ...]


def editar(sessao: Session, *, versao: VersaoPlanoMunicipal, dados: EdicaoNarrativa, autor_id: str) -> bool:
    """SPM-RF-06: o secretário revisa o texto. Passa pelo Guardião; números e nomes não são conferidos
    aqui, porque o texto passa a ser do secretário (a tela diz que foi editado). A narrativa não é
    pública: antes de exportá-la ou publicá-la, a edição precisa da mesma checagem de nomes (AgLGPD, O2)."""
    narrativa = da_versao(sessao, versao.co_municipio, versao.versao)
    if narrativa is None:
        raise ErroPlano("Gere a narrativa antes de editá-la.", 404)
    resumo, m1 = _campo(dados.resumo, obrigatorio=True)
    situacao, m2 = _campo(dados.situacao)
    fundamentacao, m3 = _campo(dados.fundamentacao)
    proximos, m4 = _campo(dados.proximos_passos)
    mascarou = any((m1, m2, m3, m4))
    estrategia = []
    for texto, acoes in dados.estrategia:
        limpo, m = _campo(texto)
        mascarou = mascarou or m
        refs = [f"A{n}" for n in dict.fromkeys(int(x) for a in acoes for x in _REF_ACAO.findall(a))]
        if any(not 1 <= int(r[1:]) <= len(versao.acoes) for r in refs):
            raise ErroPlano("Ação fora desta versão do plano.", 404)
        if limpo:
            estrategia.append({"texto": limpo, "acoes": refs})
    incertezas = []
    for texto in dados.incertezas:
        limpo, m = _campo(texto)
        mascarou = mascarou or m
        if limpo:
            incertezas.append(limpo)
    narrativa.conteudo = {
        **narrativa.conteudo, "resumo": resumo, "situacao": situacao or "", "estrategia": estrategia,
        "fundamentacao": fundamentacao or "", "proximos_passos": proximos or "", "incertezas": incertezas,
    }
    narrativa.editada = True
    _auditar(sessao, autor_id, "narrativa_plano_municipal_editada", versao, "texto revisado pela secretaria")
    sessao.commit()
    return mascarou
