"""Caixa de e-mails de teste (desenvolvimento local).

Mostra os códigos que seriam enviados por e-mail enquanto não há provedor (AD-02, pendência 3).
Responde 404 — como se a rota não existisse — fora de `AMBIENTE=dev` ou para quem não acessa da
própria máquina: com o backend aberto na rede, os códigos não ficam expostos.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.shared.ambiente import em_desenvolvimento
from app.shared.email import caixa_de_teste

router = APIRouter(prefix="/gestao/dev", tags=["gestao-dev"], include_in_schema=False)

_LOCAIS = {"127.0.0.1", "::1", "localhost"}


class EmailTeste(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    para: str
    assunto: str
    texto: str
    codigo: str
    enviada_em: datetime


@router.get("/emails", response_model=list[EmailTeste])
def emails_de_teste(request: Request) -> list[EmailTeste]:
    if not em_desenvolvimento() or (request.client and request.client.host not in _LOCAIS):
        raise HTTPException(404, "Not Found")
    return [
        EmailTeste(para=m.para, assunto=m.assunto, texto=m.texto, codigo=m.codigo, enviada_em=m.enviada_em)
        for m in caixa_de_teste()
    ]
