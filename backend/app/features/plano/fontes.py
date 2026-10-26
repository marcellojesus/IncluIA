"""Citação legível dos trechos da base normativa usados nas ações do plano."""

from app.shared.contexto_ia import BaseNormativaIndisponivel, base_normativa


def citacoes(identificadores: set[str]) -> dict[str, str]:
    """Identificador de trecho → citação legível ("Lei 13.146/2015 (LBI), Art. 28, XII")."""
    if not identificadores:
        return {}
    try:
        trechos = base_normativa.carregar().trechos
    except BaseNormativaIndisponivel:
        return {}
    return {i: trechos[i].citacao for i in identificadores if i in trechos}
