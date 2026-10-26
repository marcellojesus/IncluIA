"""Ponto de entrada da API do IncluIA — registra os routers de cada feature (ver estrutura em docs/)."""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Precisa rodar antes de importar qualquer módulo de feature — login/security.py e
# shared/ai_client.py leem variáveis de ambiente (chaves/segredos) na importação.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.features.diagnostico_ia.db import ensure_schema as ensure_schema_diagnostico_ia  # noqa: E402
from app.features.diagnostico_ia.router import router as diagnostico_ia_router  # noqa: E402
from app.features.escolas.router import router as escolas_router  # noqa: E402
from app.features.indicadores_municipio.router import router as indicadores_municipio_router  # noqa: E402
from app.features.login.db import ensure_schema_and_seed  # noqa: E402
from app.features.login.router import router as login_router  # noqa: E402
from app.features.mapa.router import router as mapa_router  # noqa: E402
from app.features.acesso.router import router as acesso_router  # noqa: E402
from app.features.acesso.router_dev import router as acesso_dev_router  # noqa: E402
from app.features.diretor.router import router as diretor_router  # noqa: E402
from app.features.declaracao.router import router as declaracao_router  # noqa: E402
from app.features.declaracao.router import router_admin as declaracao_admin_router  # noqa: E402
from app.features.declaracao.router_publico import router as declaracao_publica_router  # noqa: E402
from app.features.declaracao.router_secretario import router as declaracao_secretario_router  # noqa: E402
from app.features.plano.router import router as plano_router  # noqa: E402
from app.features.plano.router import router_admin as plano_admin_router  # noqa: E402
from app.features.plano_municipal.router import router as plano_municipal_router  # noqa: E402
from app.features.plano_municipal.router import router_diretor as acoes_municipais_router  # noqa: E402
from app.features.plano.router_secretario import router as plano_secretario_router  # noqa: E402
from app.features.acesso import servico as acesso_servico  # noqa: E402
from app.features.declaracao.conversa import limpar_conversas_paradas  # noqa: E402
from app.shared import banco_gestao  # noqa: E402
from app.shared.ambiente import problemas_da_gestao  # noqa: E402
from app.shared.guardiao_lgpd import GuardiaoIndisponivel  # noqa: E402
from app.shared.guardiao_lgpd import carregar as carregar_guardiao_lgpd  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema_and_seed()
    ensure_schema_diagnostico_ia()
    # Banco da Gestão Ativa (AD-01): aplica as migrações pendentes antes de aceitar requisições.
    banco_gestao.migrar()
    # Fora de AMBIENTE=dev, sem segredos ou provedor de e-mail a Gestão Ativa responde 503 (falha
    # fechado); o motivo fica só aqui no log, nunca na resposta. O site público segue no ar.
    for problema in problemas_da_gestao():
        logging.getLogger("gestao_ativa").error("Gestão Ativa indisponível: %s", problema)
    acesso_servico.limpar(next(banco_gestao.obter_sessao()))
    limpar_conversas_paradas(next(banco_gestao.obter_sessao()))
    # Carrega o modelo de nomes do Guardião LGPD na subida, para a primeira conversa não esperar.
    # Se falhar, o servidor sobe mesmo assim e as chamadas à IA falham fechadas (AD-05).
    try:
        carregar_guardiao_lgpd()
    except GuardiaoIndisponivel:
        logging.getLogger("guardiao_lgpd").error("Guardião LGPD indisponível: chamadas à IA serão recusadas")
    yield


app = FastAPI(title="IncluIA API", version="0.1.0", lifespan=lifespan)

# O frontend Next.js chama a API direto do navegador ao trocar de UF. Em produção, a URL real do
# frontend (Vercel) entra via variável de ambiente INCLUIA_CORS_ORIGINS (lista separada por vírgula)
# — nunca hardcoded, para não precisar de um novo deploy do backend só por causa de um domínio.
_origins = [
    origem.strip()
    for origem in os.environ.get("INCLUIA_CORS_ORIGINS", "http://localhost:3000").split(",")
    if origem.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(login_router)
app.include_router(mapa_router)
app.include_router(indicadores_municipio_router)
app.include_router(escolas_router)
app.include_router(diagnostico_ia_router)
app.include_router(acesso_router)
app.include_router(acesso_dev_router)
app.include_router(diretor_router)
app.include_router(declaracao_router)
app.include_router(declaracao_admin_router)
app.include_router(declaracao_publica_router)
app.include_router(declaracao_secretario_router)
app.include_router(plano_router)
app.include_router(plano_admin_router)
app.include_router(plano_municipal_router)
app.include_router(acoes_municipais_router)
app.include_router(plano_secretario_router)
