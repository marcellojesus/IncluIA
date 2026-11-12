"""Consultas ao artefato do Censo usadas pelo acesso: a escola e o município existem e estão no piloto."""

from dataclasses import dataclass

from app.database import get_connection
from app.shared.guardiao_lgpd import SEM_LOCAIS, Locais, nomes_da_rede

REDE_DO_PILOTO = "Municipal"  # decisão de 2026-10-23: piloto só com a rede municipal
# O Distrito Federal não tem municípios nem rede municipal: Brasília (5300108) é o único código IBGE
# do DF, e as escolas da Secretaria de Educação do DF aparecem no Censo com a dependência "Estadual".
# Decisão de 2026-11-09: no DF, a rede da Gestão Ativa é a rede distrital (federais e privadas fora).
REDE_DISTRITAL = "Estadual"
CO_UF_DF = 53


def eh_distrito_federal(co_municipio: int) -> bool:
    return co_municipio // 100_000 == CO_UF_DF


def rede_da_gestao(co_municipio: int) -> str:
    """Rede pública local atendida pela Gestão Ativa no município: a municipal ou, no DF, a distrital."""
    return REDE_DISTRITAL if eh_distrito_federal(co_municipio) else REDE_DO_PILOTO


@dataclass(frozen=True)
class RotulosRede:
    rede: str  # "Rede municipal"
    escolas: str  # "escolas municipais"
    secretaria: str  # "Secretaria Municipal de Educação"


_ROTULOS_MUNICIPAIS = RotulosRede("Rede municipal", "escolas municipais", "Secretaria Municipal de Educação")
_ROTULOS_DF = RotulosRede("Rede distrital", "escolas distritais", "Secretaria de Estado de Educação do Distrito Federal")


def rotulos_da_rede(co_municipio: int) -> RotulosRede:
    """Como os documentos nomeiam a rede e a secretaria (PDFs)."""
    return _ROTULOS_DF if eh_distrito_federal(co_municipio) else _ROTULOS_MUNICIPAIS


@dataclass(frozen=True)
class EscolaCenso:
    co_entidade: int
    nome: str
    co_municipio: int
    municipio: str
    uf: str
    rede: str


_REDE_NO_TEXTO = {"Privada": "rede privada", "Federal": "rede federal", "Estadual": "rede estadual", "Municipal": "rede municipal"}


def motivo_fora_do_piloto(escola: EscolaCenso) -> str:
    """Recusa do pedido de acesso dizendo a rede da própria escola (dado público do Censo), para não
    parecer que o sistema confundiu o município com o DF."""
    rede = _REDE_NO_TEXTO.get(escola.rede, f"rede {escola.rede.lower()}")
    atendida = rotulos_da_rede(escola.co_municipio).rede.lower()
    return (
        f"O Censo Escolar 2025 registra esta escola ({escola.municipio}/{escola.uf}) na {rede}. "
        f"Neste piloto, a Gestão Ativa atende só escolas da {atendida}."
    )


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


def edicao_do_municipio(co_municipio: int) -> str | None:
    """Edição do Censo mais nova do município no artefato (retenção das sínteses, RN-RET-07)."""
    conn = get_connection()
    try:
        return conn.execute("SELECT MAX(censo_versao) FROM escolas WHERE co_municipio = ?", (co_municipio,)).fetchone()[0]
    finally:
        conn.close()


_LOCAIS: dict[tuple[int, str, bool], Locais] = {}


def locais_da_rede(co_municipio: int | None, bairros_curtos: bool = False) -> Locais:
    """Nomes do município, das escolas de todas as redes e dos bairros, para a camada de locais do
    Guardião em todo texto que vai à IA (pendência 16; revisão do AgLGPD de 2026-11-03, M2). A escola
    estadual vizinha e o bairro também localizam a escola. Cache por município e edição do Censo; resultado
    vazio não fica guardado (B2). `bairros_curtos`: ver `nomes_da_rede`."""
    if co_municipio is None:
        return SEM_LOCAIS
    conn = get_connection()
    try:
        versao = conn.execute("SELECT MAX(censo_versao) FROM escolas WHERE co_municipio = ?", (co_municipio,)).fetchone()[0]
        if versao is None:
            return SEM_LOCAIS
        if (co_municipio, versao, bairros_curtos) in _LOCAIS:
            return _LOCAIS[(co_municipio, versao, bairros_curtos)]
        linha = conn.execute("SELECT no_municipio FROM municipios WHERE co_municipio = ?", (co_municipio,)).fetchone()
        escolas = conn.execute("SELECT no_entidade, bairro FROM escolas WHERE co_municipio = ?", (co_municipio,)).fetchall()
    finally:
        conn.close()
    locais = nomes_da_rede(linha[0] if linha else "", [e[0] for e in escolas], {e[1] for e in escolas if e[1]}, bairros_curtos)
    _LOCAIS[(co_municipio, versao, bairros_curtos)] = locais
    return locais


def limpar_cache_locais() -> None:
    """Para a recarga do artefato do Censo e para os testes."""
    _LOCAIS.clear()


def locais_da_escola(co_entidade: int) -> Locais:
    """Locais da rede da escola, para o texto do diretor que vai à IA."""
    dados = escola(co_entidade)
    return locais_da_rede(dados.co_municipio) if dados else SEM_LOCAIS
