"""Configuração da Gestão Ativa por ambiente, falhando fechado (revisão do AgLGPD, 2026-10-23).

Só `AMBIENTE=dev` (explícito, no `.env` local) libera atalhos de desenvolvimento: código de acesso
no console e segredos derivados fixos. Sem a variável, vale o comportamento de produção: segredos
obrigatórios com pelo menos 32 bytes e e-mail por provedor real. Se algo faltar, a Gestão Ativa
responde 503 e o site público da Fase 1 continua no ar.
"""

import hashlib
import os

TAMANHO_MINIMO_SEGREDO = 32


class ConfiguracaoInvalida(RuntimeError):
    pass


def em_desenvolvimento() -> bool:
    return os.environ.get("AMBIENTE") == "dev"


def segredo(nome: str) -> bytes:
    """Segredo da variável `nome`. Em dev, sem a variável, usa um valor derivado do nome (nunca
    em produção). Fora de dev, ausente ou curto levanta ConfiguracaoInvalida."""
    valor = os.environ.get(nome)
    if valor:
        if len(valor.encode()) < TAMANHO_MINIMO_SEGREDO and not em_desenvolvimento():
            raise ConfiguracaoInvalida(f"{nome} precisa de pelo menos {TAMANHO_MINIMO_SEGREDO} bytes")
        return valor.encode()
    if em_desenvolvimento():
        return hashlib.sha256(f"escola-sem-barreiras-dev:{nome}".encode()).digest()
    raise ConfiguracaoInvalida(f"{nome} não configurado")


def problemas_da_gestao() -> list[str]:
    """O que impede a Gestão Ativa de funcionar com segurança neste ambiente."""
    problemas = []
    for nome in ("GESTAO_SEGREDO_TOKEN", "GESTAO_SEGREDO_CODIGO"):
        try:
            segredo(nome)
        except ConfiguracaoInvalida as erro:
            problemas.append(str(erro))
    modo = os.environ.get("EMAIL_MODO", "")
    if modo == "console" and not em_desenvolvimento():
        problemas.append("EMAIL_MODO=console só é aceito com AMBIENTE=dev")
    elif modo == "brevo":
        for nome in ("BREVO_API_KEY", "EMAIL_REMETENTE"):
            if not os.environ.get(nome):
                problemas.append(f"EMAIL_MODO=brevo sem {nome}")
    elif modo != "console":
        problemas.append("nenhum provedor de e-mail configurado (EMAIL_MODO=brevo)")
    return problemas
