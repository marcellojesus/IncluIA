"""Spec: docs/sdd/fase-2/requirements/diretor/declaracao-obstaculos.md e business-rules (RN-DO-01 a 09).

A lista de barreiras vem da metodologia sobre o Censo e não é editável (metodologia, §7). O diretor
registra uma posição por barreira; emitir congela uma cópia; retificar é mudar o rascunho e emitir
de novo. Nada aqui altera dado do Censo, score ou faixa (RN-DO-04).
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database import get_connection
from app.features.acesso.modelos import EventoAuditoria
from app.features.declaracao.modelos import POSICOES_FINAIS, Declaracao, DeclaracaoItem, MensagemObstaculo, Posicao
from app.shared.contexto_ia import base_normativa
from app.shared.contexto_ia.barreiras import BarreiraIdentificada, identificar, texto_sem_celula_pequena
from app.shared.guardiao_lgpd import TextoBloqueado, proteger, verificar_regras

TAMANHO_MINIMO_TEXTO = 10
TAMANHO_MAXIMO_TEXTO = 3000
TAMANHO_MAXIMO_RESUMO = 300


class ErroDeclaracao(Exception):
    def __init__(self, mensagem: str, status: int = 422):
        self.mensagem = mensagem
        self.status = status
        super().__init__(mensagem)


@dataclass(frozen=True)
class EscolaComBarreiras:
    escola: object
    """Linha de `escolas` no artefato do Censo."""
    barreiras: list[BarreiraIdentificada]
    metodologia_versao: str


def escola_com_barreiras(co_entidade: int) -> EscolaComBarreiras:
    conn = get_connection()
    try:
        escola = conn.execute("SELECT * FROM escolas WHERE co_entidade = ?", (co_entidade,)).fetchone()
    finally:
        conn.close()
    if escola is None:
        raise ErroDeclaracao("Escola do vínculo não encontrada no Censo.", 404)
    base = base_normativa.carregar()
    return EscolaComBarreiras(escola, identificar(escola, base.metodologia), base.meta.get("metodologia_barreiras_versao", ""))


def protegido(texto: str, *, obrigatorio: bool = True, maximo: int = TAMANHO_MAXIMO_TEXTO) -> str | None:
    """Texto do diretor mascarado pelo Guardião LGPD; dado de risco alto bloqueia (AD-05)."""
    texto = (texto or "").strip()
    if not texto:
        if obrigatorio:
            raise ErroDeclaracao("Escreva o texto antes de confirmar.")
        return None
    if obrigatorio and len(texto) < TAMANHO_MINIMO_TEXTO:
        raise ErroDeclaracao("O texto está curto demais para explicar a situação.")
    if len(texto) > maximo:
        raise ErroDeclaracao(f"O texto passa de {maximo} caracteres.")
    resultado = proteger(texto)
    if resultado.bloqueado:
        raise ErroDeclaracao(str(TextoBloqueado(resultado.motivos_bloqueio)))
    return resultado.texto_mascarado


# --- Estado do rascunho e das versões ----------------------------------------------------------

@dataclass
class BarreiraComPosicao:
    barreira: BarreiraIdentificada
    posicao: str
    """"sem_posicao", "rascunho", "obstaculo", "divergencia" ou "sem_relato"."""
    texto: str | None = None
    resumo: str | None = None
    relato_original: str | None = None
    atualizado_em: datetime | None = None


@dataclass
class EstadoDeclaracao:
    escola: EscolaComBarreiras
    barreiras: list[BarreiraComPosicao]
    versoes: list[Declaracao]
    ha_alteracoes: bool
    faltam: int
    rascunhos: list[str] = field(default_factory=list)

    @property
    def ultima(self) -> Declaracao | None:
        return self.versoes[-1] if self.versoes else None

    @property
    def pode_emitir(self) -> bool:
        return self.faltam == 0 and self.ha_alteracoes


def _assinatura(codigo: str, posicao: str, texto: str | None, resumo: str | None) -> tuple:
    return (codigo, posicao, texto or "", resumo or "")


def estado(sessao: Session, co_entidade: int) -> EstadoDeclaracao:
    escola = escola_com_barreiras(co_entidade)
    posicoes = {p.codigo: p for p in sessao.scalars(select(Posicao).where(Posicao.co_entidade == co_entidade))}
    em_conversa = set(sessao.scalars(select(MensagemObstaculo.codigo).where(MensagemObstaculo.co_entidade == co_entidade).distinct()))
    versoes = list(sessao.scalars(select(Declaracao).where(Declaracao.co_entidade == co_entidade).order_by(Declaracao.versao)))

    lista = []
    for b in escola.barreiras:
        p = posicoes.get(b.codigo)
        if p is not None:
            lista.append(BarreiraComPosicao(b, p.posicao, p.texto, p.resumo, p.relato_original, p.atualizado_em))
        else:
            lista.append(BarreiraComPosicao(b, "rascunho" if b.codigo in em_conversa else "sem_posicao"))

    faltam = sum(1 for item in lista if item.posicao not in POSICOES_FINAIS)
    atual = {_assinatura(i.barreira.codigo, i.posicao, i.texto, i.resumo) for i in lista}
    if versoes:
        emitida = {_assinatura(i.codigo, i.posicao, i.texto, i.resumo) for i in versoes[-1].itens}
        ha_alteracoes = atual != emitida
    else:
        ha_alteracoes = True
    return EstadoDeclaracao(escola, lista, versoes, ha_alteracoes, faltam, [i.barreira.codigo for i in lista if i.posicao == "rascunho"])


# --- Posições ------------------------------------------------------------------------------------

def _barreira(estado_atual: EstadoDeclaracao, codigo: str) -> BarreiraComPosicao:
    for item in estado_atual.barreiras:
        if item.barreira.codigo == codigo:
            return item
    raise ErroDeclaracao("Esta barreira não foi identificada para a escola.", 404)


def _relato_da_conversa(sessao: Session, co_entidade: int, codigo: str) -> str | None:
    falas = sessao.scalars(
        select(MensagemObstaculo.texto)
        .where(MensagemObstaculo.co_entidade == co_entidade, MensagemObstaculo.codigo == codigo, MensagemObstaculo.papel == "diretor")
        .order_by(MensagemObstaculo.criado_em)
    ).all()
    return "\n\n".join(falas) or None


def registrar_posicao(
    sessao: Session, *, co_entidade: int, autor_id: str, codigo: str, posicao: str, texto: str | None, resumo: str | None
) -> Posicao:
    """RN-DO-02: só a ação explícita do diretor registra a posição, inclusive a proposta pela IA."""
    if posicao not in POSICOES_FINAIS:
        raise ErroDeclaracao("Posição inválida.")
    _barreira(estado(sessao, co_entidade), codigo)

    relato = None
    if posicao == "sem_relato":
        texto_final, resumo_final = None, None
    elif posicao == "divergencia":
        texto_final, resumo_final = protegido(texto), None
    else:
        texto_final = protegido(texto)
        resumo_final = protegido(resumo, obrigatorio=False, maximo=TAMANHO_MAXIMO_RESUMO)
        relato = _relato_da_conversa(sessao, co_entidade, codigo)

    registro = sessao.scalar(select(Posicao).where(Posicao.co_entidade == co_entidade, Posicao.codigo == codigo))
    if registro is None:
        registro = Posicao(co_entidade=co_entidade, codigo=codigo)
        sessao.add(registro)
    registro.posicao = posicao
    registro.texto = texto_final
    registro.resumo = resumo_final
    registro.relato_original = relato
    registro.autor_id = autor_id
    # A conversa já virou relato original; não precisa ficar guardada (minimização, AD-03).
    sessao.execute(delete(MensagemObstaculo).where(MensagemObstaculo.co_entidade == co_entidade, MensagemObstaculo.codigo == codigo))
    sessao.commit()
    return registro


def retificar_posicao(sessao: Session, *, co_entidade: int, codigo: str) -> None:
    """Volta a barreira para "sem posição" no rascunho; as versões emitidas ficam como estão."""
    _barreira(estado(sessao, co_entidade), codigo)
    sessao.execute(delete(Posicao).where(Posicao.co_entidade == co_entidade, Posicao.codigo == codigo))
    sessao.commit()


# --- Emissão -------------------------------------------------------------------------------------

def _conferir_textos(atual: EstadoDeclaracao) -> None:
    """Antes de congelar, confere de novo cada texto e o documento inteiro com as regras atuais do
    guardião (revisão do AgLGPD): uma regra nova pode pegar o que passou no registro, e um dado
    pode estar partido entre itens. Achado novo recusa a emissão em vez de mascarar em silêncio."""
    revisar = []
    for item in atual.barreiras:
        for texto in (item.texto, item.resumo):
            if texto and verificar_regras(texto).trechos:
                revisar.append(f"{item.barreira.codigo} ({item.barreira.nome})")
                break
    documento = "\n".join(t for item in atual.barreiras for t in (item.texto, item.resumo) if t)
    if not revisar and documento and verificar_regras(documento).trechos:
        revisar.append("o conjunto dos textos")
    if revisar:
        raise ErroDeclaracao(
            "O filtro de dados pessoais encontrou trechos a revisar antes de emitir: " + "; ".join(revisar)
            + ". Retifique a posição e escreva sem dados pessoais.",
            409,
        )


def emitir(sessao: Session, *, co_entidade: int, autor_id: str) -> Declaracao:
    """RN-DO-03 e RN-DO-06: todas as barreiras com posição; a versão emitida é uma cópia congelada."""
    atual = estado(sessao, co_entidade)
    if atual.faltam:
        raise ErroDeclaracao(f"Faltam {atual.faltam} barreiras sem posição.", 409)
    if not atual.ha_alteracoes:
        raise ErroDeclaracao("Não há alterações desde a última versão emitida.", 409)
    _conferir_textos(atual)

    numero = (sessao.scalar(select(func.max(Declaracao.versao)).where(Declaracao.co_entidade == co_entidade)) or 0) + 1
    escola = atual.escola.escola
    declaracao = Declaracao(
        co_entidade=co_entidade, co_municipio=escola["co_municipio"], versao=numero, censo_versao=escola["censo_versao"],
        metodologia_versao=atual.escola.metodologia_versao, emitida_por=autor_id,
    )
    sessao.add(declaracao)
    sessao.flush()
    for ordem, item in enumerate(atual.barreiras):
        b = item.barreira
        # A versão emitida vai à secretaria e, publicada, ao público: sem contagem de célula pequena.
        sessao.add(DeclaracaoItem(
            declaracao_id=declaracao.id, ordem=ordem, codigo=b.codigo, eixo=b.eixo, barreira=b.nome,
            dado_censo=texto_sem_celula_pequena(b, escola), pontos=b.pontos, posicao=item.posicao, texto=item.texto, resumo=item.resumo,
        ))
    sessao.add(EventoAuditoria(
        ator_id=autor_id, acao="declaracao_emitida", alvo_tipo="declaracao", alvo_id=declaracao.id, resultado="ok",
        detalhe=f"escola {co_entidade} v{numero}",
    ))
    sessao.commit()
    sessao.refresh(declaracao)
    return declaracao


def versao(sessao: Session, co_entidade: int, numero: int) -> Declaracao:
    declaracao = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co_entidade, Declaracao.versao == numero))
    if declaracao is None:
        raise ErroDeclaracao("Versão não encontrada.", 404)
    return declaracao
