"""Consultas ao artefato do Censo usadas pelo acesso: a escola e o município existem e estão no piloto."""

from dataclasses import dataclass

from app.database import get_connection
from app.shared.guardiao_lgpd import SEM_LOCAIS, Locais, nomes_da_rede

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


_LOCAIS: dict[tuple[int, str], Locais] = {}


def locais_da_rede(co_municipio: int | None) -> Locais:
    """Nomes do município, das escolas de todas as redes e dos bairros, para a camada de locais do
    Guardião em todo texto que vai à IA (pendência 16; revisão do AgLGPD de 2026-11-03, M2). A escola
    estadual vizinha e o bairro também localizam a escola. Cache por município e edição do Censo; resultado
    vazio não fica guardado (B2)."""
    if co_municipio is None:
        return SEM_LOCAIS
    conn = get_connection()
    try:
        versao = conn.execute("SELECT MAX(censo_versao) FROM escolas WHERE co_municipio = ?", (co_municipio,)).fetchone()[0]
        if versao is None:
            return SEM_LOCAIS
        if (co_municipio, versao) in _LOCAIS:
            return _LOCAIS[(co_municipio, versao)]
        linha = conn.execute("SELECT no_municipio FROM municipios WHERE co_municipio = ?", (co_municipio,)).fetchone()
        escolas = conn.execute("SELECT no_entidade, bairro FROM escolas WHERE co_municipio = ?", (co_municipio,)).fetchall()
    finally:
        conn.close()
    locais = nomes_da_rede(linha[0] if linha else "", [e[0] for e in escolas], {e[1] for e in escolas if e[1]})
    _LOCAIS[(co_municipio, versao)] = locais
    return locais


def limpar_cache_locais() -> None:
    """Para a recarga do artefato do Censo e para os testes."""
    _LOCAIS.clear()


def locais_da_escola(co_entidade: int) -> Locais:
    """Locais da rede da escola, para o texto do diretor que vai à IA."""
    dados = escola(co_entidade)
    return locais_da_rede(dados.co_municipio) if dados else SEM_LOCAIS
