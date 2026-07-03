"""Ponto de entrada da API do IncluIA — registra os routers de cada feature (ver estrutura em docs/)."""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Precisa rodar antes de importar qualquer módulo de feature — login/security.py e
# diagnostico_ia/ai_client.py leem variáveis de ambiente (chaves/segredos) na importação.
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema_and_seed()
    ensure_schema_diagnostico_ia()
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
