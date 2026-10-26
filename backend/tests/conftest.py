"""Os testes rodam como ambiente de desenvolvimento (segredos derivados, e-mail no console), salvo os
que mudam o ambiente de propósito para verificar o comportamento de produção."""

import os

os.environ["AMBIENTE"] = "dev"
os.environ["EMAIL_MODO"] = "console"

import pytest  # noqa: E402

from app.features.acesso.protecao import zerar_limites  # noqa: E402
from app.features.declaracao.router_publico import limpar_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _limites_e_cache_zerados():
    limpar_cache()
    zerar_limites()
    yield
    zerar_limites()
