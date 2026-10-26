"""Envio de e-mail da Gestão Ativa.

`EMAIL_MODO=console` só é aceito com `AMBIENTE=dev`: a mensagem vai para o console do backend e
para a caixa de teste local (`caixa_de_teste`, exibida em /gestao/dev/emails). Em produção o
console vira log persistente, e o código ali daria acesso a quem lê o log. O provedor
transacional gratuito (AD-02, decisão pendente 3) entra aqui no deploy; até lá, fora de dev, o
envio falha fechado.
"""

import os
import sys
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from app.shared.ambiente import em_desenvolvimento
from app.shared.banco_gestao import agora

_CAPACIDADE_CAIXA = 30


class EnvioIndisponivel(RuntimeError):
    pass


@dataclass(frozen=True)
class MensagemTeste:
    para: str
    assunto: str
    texto: str
    codigo: str
    enviada_em: datetime


_caixa: deque[MensagemTeste] = deque(maxlen=_CAPACIDADE_CAIXA)
_trava = threading.Lock()


def caixa_de_teste() -> list[MensagemTeste]:
    """Últimas mensagens simuladas, da mais recente para a mais antiga. Só em memória: some quando
    o backend reinicia. Vazia fora de dev."""
    if not em_desenvolvimento():
        return []
    with _trava:
        return list(reversed(_caixa))


def enviar_codigo(email: str, codigo: str, escola: str | None = None) -> None:
    if os.environ.get("EMAIL_MODO") != "console" or not em_desenvolvimento():
        raise EnvioIndisponivel("Envio de e-mail não configurado neste ambiente")
    if escola:
        assunto = "Confirme seu pedido de acesso à Gestão Ativa"
        texto = f"Você pediu acesso à Gestão Ativa como diretor(a) de {escola}. Se não foi você, ignore este e-mail."
    else:
        assunto = "Seu código de acesso à Gestão Ativa"
        texto = "Use este código para entrar na Gestão Ativa."
    with _trava:
        _caixa.append(MensagemTeste(email, assunto, texto, codigo, agora()))
    print(f"\n[Gestão Ativa — e-mail simulado, AMBIENTE=dev] Para {email}: {texto} Código: {codigo}\n", file=sys.stderr, flush=True)
