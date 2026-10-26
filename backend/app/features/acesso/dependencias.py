"""Autorização da Gestão Ativa no servidor (RF-01, RF-07, RN-07).

O token só identifica a conta. A cada requisição, conta e vínculo são lidos do banco: vínculo
pendente, rejeitado, suspenso ou revogado não passa, mesmo com token válido. O escopo (escola do
diretor, rede do secretário) vem do vínculo, nunca de parâmetro enviado pelo navegador.
"""

from collections.abc import Callable
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.features.acesso import seguranca
from app.features.acesso.modelos import Conta
from app.shared.banco_gestao import obter_sessao


@dataclass(frozen=True)
class SessaoGestao:
    conta: Conta
    co_entidade: int | None
    """Escola do diretor (None para secretário e administrador)."""
    co_municipio: int | None
    """Rede do secretário ou município da escola do diretor."""


def _conta_autenticada(authorization: str | None, sessao: Session) -> Conta:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Entre na Gestão Ativa para continuar.")
    try:
        conta_id = seguranca.conta_do_token(authorization.removeprefix("Bearer ").strip())
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Sessão expirada ou inválida. Entre de novo.") from None
    conta = sessao.get(Conta, conta_id)
    if conta is None:
        raise HTTPException(401, "Sessão inválida. Entre de novo.")
    return conta


def exigir(*papeis: str) -> Callable[..., SessaoGestao]:
    """Dependência: conta com um dos papéis e acesso ativo agora."""

    def dependencia(authorization: str | None = Header(default=None), sessao: Session = Depends(obter_sessao)) -> SessaoGestao:
        conta = _conta_autenticada(authorization, sessao)
        if conta.papel not in papeis:
            raise HTTPException(403, "Seu perfil não tem acesso a esta área.")
        if conta.papel == "admin":
            return SessaoGestao(conta, None, None)
        vinculo = conta.vinculo_vigente()
        if conta.email_confirmado_em is None or vinculo is None or vinculo.estado != "aprovado":
            raise HTTPException(403, "Seu acesso à Gestão Ativa não está ativo.")
        return SessaoGestao(conta, vinculo.co_entidade, vinculo.co_municipio)

    return dependencia


exigir_diretor = exigir("diretor")
exigir_secretario = exigir("secretario")
exigir_admin = exigir("admin")
exigir_qualquer_perfil = exigir("diretor", "secretario", "admin")
