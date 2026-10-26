"""Consultas ao artefato do Censo usadas pelo acesso: a escola e o município existem e estão no piloto."""

from dataclasses import dataclass

from app.database import get_connection

REDE_DO_PILOTO = "Municipal"  # decisão de 2026-10-23: piloto só com a rede municipal


@dataclass(frozen=True)
class EscolaCenso:
    co_entidade: int
    nome: str
    co_municipio: int
    municipio: str
    uf: str
    rede: str


@dataclass(frozen=True)
class MunicipioCenso:
    co_municipio: int
    nome: str
    uf: str


def escola(co_entidade: int) -> EscolaCenso | None:
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT co_entidade, no_entidade, co_municipio, no_municipio, sg_uf, rede FROM escolas WHERE co_entidade = ?",
            (co_entidade,),
        ).fetchone()
    finally:
        conn.close()
    return EscolaCenso(*linha) if linha else None


def escolas(codigos: set[int]) -> dict[int, EscolaCenso]:
    if not codigos:
        return {}
    conn = get_connection()
    try:
        marcadores = ",".join("?" * len(codigos))
        linhas = conn.execute(
            f"SELECT co_entidade, no_entidade, co_municipio, no_municipio, sg_uf, rede FROM escolas WHERE co_entidade IN ({marcadores})",
            tuple(codigos),
        ).fetchall()
    finally:
        conn.close()
    return {linha[0]: EscolaCenso(*linha) for linha in linhas}


def municipio(co_municipio: int) -> MunicipioCenso | None:
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT co_municipio, no_municipio, sg_uf FROM municipios WHERE co_municipio = ?", (co_municipio,)
        ).fetchone()
    finally:
        conn.close()
    return MunicipioCenso(*linha) if linha else None
