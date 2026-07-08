"""Spec: docs/requirements/login.md, docs/business-rules/login.md"""

from fastapi import APIRouter, HTTPException

from app.features.login import service
from app.features.login.schemas import LoginRequest, LoginResponse, RegistroRequest
from app.features.login.service import EmailJaCadastradoError

router = APIRouter(prefix="/auth", tags=["login"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    resultado = service.autenticar(request.email, request.senha)
    if resultado is None:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    return resultado


@router.post("/registrar", response_model=LoginResponse, status_code=201)
def registrar(request: RegistroRequest) -> LoginResponse:
    try:
        return service.registrar(request.nome, request.email, request.senha, request.perfil)
    except EmailJaCadastradoError:
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado")


@router.post("/logout", status_code=204)
def logout() -> None:
    # Sessão é um JWT stateless (ver security.py) — não há estado de sessão a limpar no
    # servidor; o cliente só descarta o token guardado.
    return None
