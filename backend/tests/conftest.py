"""Os testes rodam como ambiente de desenvolvimento (segredos derivados, e-mail no console), salvo os
que mudam o ambiente de propósito para verificar o comportamento de produção."""

import os

os.environ["AMBIENTE"] = "dev"
os.environ["EMAIL_MODO"] = "console"
# PostgreSQL de teste só quando passado no terminal (tests/banco.py). O app carrega o backend/.env ao
# ser importado, e o load_dotenv não sobrescreve variável já definida: com o valor fixado aqui, uma
# GESTAO_TESTE_DATABASE_URL guardada no .env não vale, e a suíte padrão roda em SQLite.
os.environ["GESTAO_TESTE_DATABASE_URL"] = os.environ.get("GESTAO_TESTE_DATABASE_URL", "")
# Os testes nunca usam o banco configurado para o app (produção ou desenvolvimento).
os.environ["GESTAO_DATABASE_URL"] = ""

import pytest  # noqa: E402

from app.features.acesso.protecao import zerar_limites  # noqa: E402
from app.features.declaracao.router_publico import limpar_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _limites_e_cache_zerados():
    limpar_cache()
    zerar_limites()
    yield
    zerar_limites()
