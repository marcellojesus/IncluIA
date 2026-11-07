"""Regras do acesso à Gestão Ativa (docs/sdd/fase-2/business-rules/acesso-gestao-ativa.md).

Respostas que dependem de existir ou não uma conta são uniformes, para não revelar quem está
cadastrado. Cada mudança de estado gera evento de auditoria (RN-13) com categoria fechada, nunca
texto livre. Correções da revisão do AgLGPD de 2026-10-23: confirmação por pedido, consumo atômico
do código, limites diários, pedidos não confirmados escondidos e apagados, textos mascarados.
"""

import re
from dataclasses import dataclass
from datetime import timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.features.acesso import censo, seguranca
from app.features.acesso.modelos import CodigoUsoUnico, Conta, EventoAuditoria, Vinculo
from app.shared import email as envio
from app.shared.banco_gestao import agora
from app.shared.guardiao_lgpd import proteger
from app.shared.guardiao_lgpd.contexto_escolar import tem_dado_sensivel

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Categorias fechadas por ação: é o que a auditoria guarda (revisão do AgLGPD, I4).
CATEGORIAS = {
    "aprovar": ("oficio", "sistema_rede", "telefone_institucional", "presencial", "outro"),
    "rejeitar": ("nao_consta", "escola_errada", "outro"),
    "suspender": ("afastamento", "apuracao", "outro"),
    "reativar": ("retorno", "outro"),
    "revogar": ("mudanca_escola", "desligamento", "uso_indevido", "outro"),
    "provisionar": ("oficio", "telefone_institucional", "diario_oficial", "outro"),
}
PRAZO_PEDIDO_NAO_CONFIRMADO = timedelta(hours=72)
PRAZO_CODIGO = timedelta(hours=24)


class ErroAcesso(Exception):
    """Erro de regra com mensagem para o usuário e código HTTP sugerido."""

    def __init__(self, mensagem: str, status: int = 422):
        self.mensagem = mensagem
        self.status = status
        super().__init__(mensagem)


def normalizar_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not _EMAIL.match(email) or len(email) > 254:
        raise ErroAcesso("Informe um e-mail válido.")
    return email


def _nome(nome: str) -> str:
    nome = " ".join((nome or "").split())
    if not 3 <= len(nome) <= 200:
        raise ErroAcesso("Informe o nome completo.")
    return nome


def _texto_da_decisao(texto: str, obrigatorio: str) -> str:
    """Texto livre do secretário ou do administrador, mascarado pelo Guardião LGPD antes de gravar."""
    texto = " ".join((texto or "").split())
    if len(texto) < 5:
        raise ErroAcesso(obrigatorio)
    resultado = proteger(texto)
    # O texto é sempre sobre uma pessoa identificada (o candidato), então saúde e situação sensível
    # bloqueiam mesmo sem menção a estudante.
    if resultado.bloqueado or tem_dado_sensivel(texto):
        raise ErroAcesso("O texto tem dado sensível (saúde, documento ou situação pessoal). Descreva só como o vínculo foi verificado.")
    return resultado.texto_mascarado


def _categoria(acao: str, categoria: str) -> str:
    if categoria not in CATEGORIAS[acao]:
        raise ErroAcesso("Escolha uma das opções de motivo.")
    return categoria


def auditar(sessao: Session, *, ator_id: str | None, acao: str, alvo: Conta | Vinculo, resultado: str = "ok", detalhe: str | None = None) -> None:
    sessao.add(EventoAuditoria(
        ator_id=ator_id, acao=acao, alvo_tipo="conta" if isinstance(alvo, Conta) else "vinculo",
        alvo_id=alvo.id, resultado=resultado, detalhe=detalhe,
    ))


def _conta_por_email(sessao: Session, email: str) -> Conta | None:
    return sessao.scalar(select(Conta).where(Conta.email == email))


def _utc(momento):
    """SQLite devolve datas sem fuso; o banco grava sempre em UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)


# --- Código de uso único -----------------------------------------------------------------------

def _codigos_desde(sessao: Session, email: str, janela: timedelta) -> list[CodigoUsoUnico]:
    return list(sessao.scalars(select(CodigoUsoUnico).where(CodigoUsoUnico.email == email, CodigoUsoUnico.criado_em >= agora() - janela)))


def _bloqueado_por_erros(sessao: Session, email: str) -> bool:
    erros = sessao.scalar(
        select(func.coalesce(func.sum(CodigoUsoUnico.tentativas), 0))
        .where(CodigoUsoUnico.email == email, CodigoUsoUnico.criado_em >= agora() - timedelta(days=1))
    )
    return erros >= seguranca.MAX_ERROS_POR_DIA


def enviar_codigo(sessao: Session, email: str, vinculo: Vinculo | None = None, escola: str | None = None) -> None:
    """Gera e envia um código, respeitando intervalo de reenvio e limites por hora e por dia (RF-04)."""
    do_dia = _codigos_desde(sessao, email, timedelta(days=1))
    da_hora = [c for c in do_dia if _utc(c.criado_em) >= agora() - timedelta(hours=1)]
    if len(do_dia) >= seguranca.MAX_CODIGOS_POR_DIA or len(da_hora) >= seguranca.MAX_CODIGOS_POR_HORA:
        return
    if _bloqueado_por_erros(sessao, email):
        return
    if any(c.usado_em is None and _utc(c.criado_em) >= agora() - seguranca.INTERVALO_REENVIO for c in do_dia):
        return
    sessao.execute(update(CodigoUsoUnico).where(CodigoUsoUnico.email == email, CodigoUsoUnico.usado_em.is_(None)).values(usado_em=agora()))
    codigo = seguranca.novo_codigo()
    sessao.add(CodigoUsoUnico(
        email=email, vinculo_id=vinculo.id if vinculo else None,
        codigo_hash=seguranca.hash_codigo(email, codigo), expira_em=agora() + seguranca.VALIDADE_CODIGO,
    ))
    sessao.flush()
    envio.enviar_codigo(email, codigo, escola)


def _consumir_codigo(sessao: Session, email: str, codigo: str) -> CodigoUsoUnico | None:
    """Devolve o registro do código se ele confere e ainda não foi usado. O uso e o erro são gravados
    com UPDATE condicional, para requisições simultâneas não passarem do limite (revisão, I1)."""
    if _bloqueado_por_erros(sessao, email):
        return None
    registro = sessao.scalar(
        select(CodigoUsoUnico)
        .where(CodigoUsoUnico.email == email, CodigoUsoUnico.usado_em.is_(None))
        .order_by(CodigoUsoUnico.criado_em.desc())
    )
    if registro is None or _utc(registro.expira_em) < agora():
        return None
    condicao = (CodigoUsoUnico.id == registro.id, CodigoUsoUnico.usado_em.is_(None), CodigoUsoUnico.tentativas < seguranca.MAX_TENTATIVAS)
    if not seguranca.codigo_confere(email, codigo, registro.codigo_hash):
        sessao.execute(update(CodigoUsoUnico).where(*condicao).values(tentativas=CodigoUsoUnico.tentativas + 1))
        sessao.execute(
            update(CodigoUsoUnico)
            .where(CodigoUsoUnico.id == registro.id, CodigoUsoUnico.tentativas >= seguranca.MAX_TENTATIVAS)
            .values(usado_em=agora())
        )
        return None
    usado = sessao.execute(update(CodigoUsoUnico).where(*condicao).values(usado_em=agora()))
    return registro if usado.rowcount == 1 else None


# --- Diretor: solicitação ----------------------------------------------------------------------

MENSAGEM_CODIGO_ENVIADO = "Se os dados estiverem corretos, enviamos um código de 6 dígitos para o e-mail informado."


def solicitar_acesso_diretor(sessao: Session, *, nome: str, email: str, co_entidade: int) -> None:
    """Fluxo 2 (RF-02, RF-03): pedido pendente e código enviado. O pedido só aparece para a
    secretaria depois que o dono do e-mail usar o código deste pedido."""
    nome, email = _nome(nome), normalizar_email(email)
    escola = censo.escola(co_entidade)
    if escola is None:
        raise ErroAcesso("Código INEP não encontrado no Censo Escolar 2025.", 404)
    if escola.rede != censo.REDE_DO_PILOTO:
        raise ErroAcesso("Neste piloto, a Gestão Ativa atende só escolas da rede municipal.")

    conta = _conta_por_email(sessao, email)
    if conta is None:
        conta = Conta(nome=nome, email=email, papel="diretor")
        sessao.add(conta)
        sessao.flush()
        auditar(sessao, ator_id=None, acao="conta_criada", alvo=conta, resultado="nao_autenticado")
    vinculo = None
    if conta.papel == "diretor" and conta.vinculo_vigente() is None:
        vinculo = Vinculo(conta_id=conta.id, co_entidade=escola.co_entidade, co_municipio=escola.co_municipio)
        sessao.add(vinculo)
        sessao.flush()
        sessao.refresh(conta)
        auditar(sessao, ator_id=None, acao="vinculo_solicitado", alvo=vinculo, resultado="nao_autenticado", detalhe=f"escola {escola.co_entidade}")
    # Conta com vínculo vigente ou de outro papel: mesma resposta, sem pedido novo.
    enviar_codigo(sessao, email, vinculo, escola.nome if vinculo else None)
    sessao.commit()


# --- Entrada ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultadoEntrada:
    situacao: str
    """"ativo", "aguardando_aprovacao", "rejeitado", "suspenso" ou "revogado"."""
    token: str | None = None
    mensagem: str = ""


_MENSAGENS_SITUACAO = {
    "aguardando_aprovacao": "E-mail confirmado. Seu vínculo está em validação pela secretaria municipal; a Gestão Ativa fica bloqueada até a aprovação.",
    "rejeitado": "A secretaria não confirmou o vínculo com a escola. Se os dados estiverem errados, solicite de novo com o código INEP correto ou procure a secretaria municipal.",
    "suspenso": "Seu acesso está suspenso pela secretaria municipal. Procure a secretaria para regularizar.",
    "revogado": "Seu acesso foi revogado. Para voltar, é preciso uma nova solicitação e uma nova aprovação.",
}


def pedir_codigo_de_entrada(sessao: Session, email: str) -> None:
    email = normalizar_email(email)
    if _conta_por_email(sessao, email) is not None:
        enviar_codigo(sessao, email)
        sessao.commit()


def situacao(conta: Conta) -> str:
    if conta.papel == "admin":
        return "ativo"
    vigente = conta.vinculo_vigente()
    if vigente is None:
        ultimo = conta.vinculos[-1] if conta.vinculos else None
        return ultimo.estado if ultimo and ultimo.estado in ("rejeitado", "revogado") else "revogado"
    return {"aprovado": "ativo", "pendente": "aguardando_aprovacao", "suspenso": "suspenso"}[vigente.estado]


def entrar(sessao: Session, *, email: str, codigo: str) -> ResultadoEntrada:
    email = normalizar_email(email)
    conta = _conta_por_email(sessao, email)
    registro = _consumir_codigo(sessao, email, codigo)
    if registro is None or conta is None:
        sessao.commit()  # grava a tentativa errada
        raise ErroAcesso("Código inválido ou expirado. Peça um novo código.", 400)
    if conta.email_confirmado_em is None:
        conta.email_confirmado_em = agora()
        auditar(sessao, ator_id=conta.id, acao="canal_confirmado", alvo=conta)
    # Só o código enviado para o pedido confirma o pedido (revisão, I3). O secretário provisionado
    # confirma o próprio vínculo na primeira entrada.
    vigente = conta.vinculo_vigente()
    confirma = registro.vinculo_id is not None or (conta.papel == "secretario" and vigente is not None)
    if confirma and vigente is not None and vigente.confirmado_em is None and (registro.vinculo_id in (None, vigente.id)):
        vigente.confirmado_em = agora()
        auditar(sessao, ator_id=conta.id, acao="pedido_confirmado", alvo=vigente)
    estado = situacao(conta)
    auditar(sessao, ator_id=conta.id, acao="entrada", alvo=conta, resultado=estado)
    sessao.commit()
    if estado == "ativo":
        return ResultadoEntrada("ativo", seguranca.criar_token(conta.id))
    return ResultadoEntrada(estado, mensagem=_MENSAGENS_SITUACAO[estado])


# --- Secretário: decisão sobre vínculos de diretor ---------------------------------------------

def solicitacoes_da_rede(sessao: Session, co_municipio: int, estados: tuple[str, ...]) -> list[Vinculo]:
    """Pedido sem confirmação do e-mail não aparece: pode ser alguém usando nome e e-mail de outra
    pessoa (revisão, I2). Ele é apagado em 72 h por `limpar`."""
    return list(sessao.scalars(
        select(Vinculo).join(Conta, Vinculo.conta_id == Conta.id)
        .where(
            Vinculo.co_municipio == co_municipio, Conta.papel == "diretor", Vinculo.estado.in_(estados),
            (Vinculo.estado != "pendente") | Vinculo.confirmado_em.is_not(None),
        )
        .order_by(Vinculo.criado_em)
    ))


def _vinculo_da_rede(sessao: Session, vinculo_id: str, co_municipio: int) -> Vinculo:
    vinculo = sessao.get(Vinculo, vinculo_id)
    # Vínculo de outra rede responde como inexistente (RN-07: o escopo não vaza).
    if vinculo is None or vinculo.co_municipio != co_municipio or vinculo.conta.papel != "diretor":
        raise ErroAcesso("Solicitação não encontrada.", 404)
    return vinculo


_TRANSICOES = {
    "aprovar": (("pendente",), "aprovado"),
    "rejeitar": (("pendente",), "rejeitado"),
    "suspender": (("aprovado",), "suspenso"),
    "reativar": (("suspenso",), "aprovado"),
    "revogar": (("aprovado", "suspenso"), "revogado"),
}


def decidir_vinculo(
    sessao: Session, *, secretario: Conta, co_municipio: int, vinculo_id: str, acao: str, categoria: str, texto: str
) -> Vinculo:
    """RF-05 e RF-09. `texto` é o método de verificação (aprovar) ou a justificativa (demais)."""
    categoria = _categoria(acao, categoria)
    texto = _texto_da_decisao(texto, "Descreva o método de verificação." if acao == "aprovar" else "Informe a justificativa.")
    vinculo = _vinculo_da_rede(sessao, vinculo_id, co_municipio)
    origens, destino = _TRANSICOES[acao]
    if vinculo.estado not in origens:
        raise ErroAcesso(f"Não é possível {acao} um vínculo {vinculo.estado}.", 409)
    if acao == "aprovar" and vinculo.confirmado_em is None:
        raise ErroAcesso("O candidato ainda não confirmou o e-mail deste pedido.", 409)
    if vinculo.conta_id == secretario.id:
        raise ErroAcesso("Ninguém decide sobre o próprio vínculo.", 403)

    vinculo.estado = destino
    vinculo.decidido_por = secretario.id
    vinculo.decidido_em = agora()
    vinculo.categoria = categoria
    if acao == "aprovar":
        vinculo.metodo_verificacao = texto
    else:
        vinculo.justificativa = texto
    auditar(sessao, ator_id=secretario.id, acao=f"vinculo_{destino}", alvo=vinculo, detalhe=categoria)
    sessao.commit()
    return vinculo


# --- Administrador: secretários ----------------------------------------------------------------

def provisionar_secretario(
    sessao: Session, *, admin: Conta, nome: str, email: str, co_municipio: int, categoria: str, metodo: str
) -> Conta:
    """Fluxo 1 (RF-06): conta e vínculo criados pelo administrador; o acesso começa quando o
    secretário confirma o e-mail com o código."""
    nome, email = _nome(nome), normalizar_email(email)
    categoria = _categoria("provisionar", categoria)
    metodo = _texto_da_decisao(metodo, "Descreva como a função foi confirmada no canal institucional.")
    municipio = censo.municipio(co_municipio)
    if municipio is None:
        raise ErroAcesso("Município não encontrado no Censo Escolar 2025.", 404)
    if _conta_por_email(sessao, email) is not None:
        raise ErroAcesso("Já existe uma conta com este e-mail.", 409)

    conta = Conta(nome=nome, email=email, papel="secretario")
    sessao.add(conta)
    sessao.flush()
    vinculo = Vinculo(
        conta_id=conta.id, co_municipio=co_municipio, estado="aprovado", categoria=categoria,
        decidido_por=admin.id, decidido_em=agora(), metodo_verificacao=metodo,
    )
    sessao.add(vinculo)
    sessao.flush()
    auditar(sessao, ator_id=admin.id, acao="secretario_provisionado", alvo=vinculo, detalhe=categoria)
    enviar_codigo(sessao, email)
    sessao.commit()
    return conta


def criar_admin(sessao: Session, *, nome: str, email: str) -> Conta:
    """Só pela linha de comando (python -m app.features.acesso.cli)."""
    email = normalizar_email(email)
    if _conta_por_email(sessao, email) is not None:
        raise ErroAcesso("Já existe uma conta com este e-mail.", 409)
    conta = Conta(nome=_nome(nome), email=email, papel="admin")
    sessao.add(conta)
    sessao.flush()
    auditar(sessao, ator_id=None, acao="admin_criado", alvo=conta, detalhe="linha de comando")
    sessao.commit()
    return conta


# --- Retenção ----------------------------------------------------------------------------------

def limpar(sessao: Session) -> dict[str, int]:
    """Apaga o que não precisa ficar (revisão, M4): códigos com mais de 24 h, pedidos nunca
    confirmados com mais de 72 h e contas de diretor que nunca confirmaram o e-mail e ficaram sem
    pedido. Os demais prazos de retenção são a decisão pendente 4 de AD-03."""
    corte_pedido = agora() - PRAZO_PEDIDO_NAO_CONFIRMADO
    sem_sincronizar = {"synchronize_session": False}
    codigos = sessao.execute(
        delete(CodigoUsoUnico).where(CodigoUsoUnico.criado_em < agora() - PRAZO_CODIGO).execution_options(**sem_sincronizar)
    ).rowcount
    pedidos = sessao.execute(
        delete(Vinculo)
        .where(Vinculo.estado == "pendente", Vinculo.confirmado_em.is_(None), Vinculo.criado_em < corte_pedido)
        .execution_options(**sem_sincronizar)
    ).rowcount
    tem_vinculo = select(Vinculo.id).where(Vinculo.conta_id == Conta.id).exists()
    contas = sessao.execute(
        delete(Conta).where(
            Conta.papel == "diretor", Conta.email_confirmado_em.is_(None), Conta.criado_em < corte_pedido, ~tem_vinculo,
            # A conta pseudonimizada tem histórico (auditoria, versões): fica (retenção, RN-RET-04).
            Conta.anonimizada_em.is_(None),
        ).execution_options(synchronize_session=False)
    ).rowcount
    sessao.commit()
    return {"codigos": codigos, "pedidos_nao_confirmados": pedidos, "contas_nao_confirmadas": contas}
