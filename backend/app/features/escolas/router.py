"""Spec: docs/requirements/escolas.md, docs/business-rules/escolas.md"""

from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.features.escolas import service
from app.features.escolas.schemas import BarreiraPublica, BarreirasDaEscola, Escola
from app.shared.contexto_ia import BaseNormativaIndisponivel, base_normativa
from app.shared.contexto_ia.barreiras import (
    CLASSE_EXCLUSIVA,
    celula_pequena,
    identificar,
    pontos_revelam_contagem,
    texto_sem_celula_pequena,
)

router = APIRouter(tags=["escolas"])


@router.get("/municipios/{codigo_ibge}/escolas", response_model=list[Escola])
def get_escolas_por_municipio(codigo_ibge: int) -> list[Escola]:
    return service.obter_escolas_por_municipio(codigo_ibge)


@router.get("/escolas/{co_entidade}", response_model=Escola)
def get_escola_detalhe(co_entidade: int) -> Escola:
    resultado = service.obter_escola_detalhe(co_entidade)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Escola {co_entidade} não encontrada")
    return resultado


@router.get("/escolas/{co_entidade}/barreiras", response_model=BarreirasDaEscola)
def get_barreiras_da_escola(co_entidade: int) -> BarreirasDaEscola:
    """PUB-01: a mesma regra da Declaração de Obstáculos, sem a contagem de célula pequena (AD-08)."""
    conn = get_connection()
    try:
        escola = conn.execute("SELECT * FROM escolas WHERE co_entidade = ?", (co_entidade,)).fetchone()
    finally:
        conn.close()
    if escola is None:
        raise HTTPException(status_code=404, detail=f"Escola {co_entidade} não encontrada")
    try:
        base = base_normativa.carregar()
    except BaseNormativaIndisponivel:
        raise HTTPException(503, "Metodologia de barreiras indisponível no servidor.") from None
    barreiras = [
        BarreiraPublica(
            codigo=b.codigo, eixo=b.eixo, nome=b.nome, dado_censo=texto_sem_celula_pequena(b, escola),
            pontos=None if pontos_revelam_contagem(b, escola) else b.pontos, nota=b.nota,
        )
        for b in identificar(escola, base.metodologia)
    ]
    if celula_pequena(escola):
        # Com 1 a 4 alunos, ter ou não a barreira do eixo IV já diz onde eles estudam (revisão do
        # AgLGPD de 2026-10-27): o eixo IV vira um item fixo, igual com ou sem classe exclusiva.
        barreiras = [b for b in barreiras if b.codigo != CLASSE_EXCLUSIVA] + [_EIXO_IV_OMITIDO]
    return BarreirasDaEscola(
        co_entidade=co_entidade, censo_versao=escola["censo_versao"], metodologia_versao=base.meta.get("metodologia_barreiras_versao", ""),
        barreiras=barreiras,
    )


_EIXO_IV_OMITIDO = BarreiraPublica(
    codigo="B-IV-omitido", eixo="IV", nome="Inclusão em classe comum",
    dado_censo="Dado omitido: a escola tem menos de 5 matrículas da educação especial, e mostrá-lo poderia identificar estudantes.",
    pontos=None,
)
