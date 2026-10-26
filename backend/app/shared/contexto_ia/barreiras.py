"""Identificação das barreiras de uma escola (metodologia_barreiras.md, §3 a §5).

Regra determinística sobre os indicadores do Censo já gravados em `escolas` pelo ETL do score. Os
nomes, textos e pontos vêm da metodologia gravada na base normativa (camada C2), para a IA e a tela
usarem a mesma versão. Quando o ETL passar a gravar a tabela de barreiras (AD-04), esta função é a
que ele deve chamar.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from app.shared.contexto_ia.base_normativa import RegraBarreira

# Código da barreira → indicador binário em `escolas` (1 = recurso registrado no Censo).
_INDICADOR = {
    "B-I-01": "v_aee",
    "B-II-01": "v_rampa",
    "B-II-02": "v_banheiro_pne",
    "B-II-03": "v_corrimao",
    "B-II-04": "v_piso_tatil",
    "B-II-05": "v_sinal_visual",
    "B-II-06": "v_sinal_sonoro",
    "B-II-07": "v_elevador",
    "B-III-01": "v_libras",
    "B-III-02": "v_braille",
}
CLASSE_EXCLUSIVA = "B-IV-01"
CODIGOS_COM_REGRA = frozenset(_INDICADOR) | {CLASSE_EXCLUSIVA}

_ORDEM_EIXO = {"I": 0, "II": 1, "III": 2, "IV": 3}
_NAO_INFORMADO = "informação não registrada no Censo"
_ELEVADOR = "pode não se aplicar a prédios térreos"


@dataclass(frozen=True)
class BarreiraIdentificada:
    codigo: str
    eixo: str
    nome: str
    texto: str
    pontos: float
    """Pontos do score em jogo (metodologia, §5)."""
    nota: str | None = None


def identificar(escola: Mapping, metodologia: Mapping[str, RegraBarreira]) -> list[BarreiraIdentificada]:
    """Barreiras da escola, ordenadas por pontos em jogo, depois eixo e código (§5)."""
    faltando = CODIGOS_COM_REGRA ^ set(metodologia)
    if faltando:
        raise ValueError(f"Metodologia e regras de identificação divergem: {sorted(faltando)}")

    barreiras = []
    for codigo, coluna in _INDICADOR.items():
        valor = escola[coluna]
        if valor is None or valor == 0:
            regra = metodologia[codigo]
            nota = _NAO_INFORMADO if valor is None else (_ELEVADOR if codigo == "B-II-07" else None)
            barreiras.append(BarreiraIdentificada(codigo, regra.eixo, regra.barreira, regra.texto_exibido, regra.pontos_max, nota))

    # Eixo IV (§3 e §4.1): só com matrícula da educação especial e alguma fora da classe comum
    # (QT_MAT_ESP = classe comum + classe exclusiva).
    matriculas, classe_comum = escola["qt_mat_esp"] or 0, escola["qt_mat_esp_cc"] or 0
    if matriculas > 0 and classe_comum < matriculas:
        regra = metodologia[CLASSE_EXCLUSIVA]
        taxa = classe_comum / matriculas
        texto = regra.texto_exibido.replace("X de Y", f"{matriculas - classe_comum:g} de {matriculas:g}")
        barreiras.append(BarreiraIdentificada(CLASSE_EXCLUSIVA, regra.eixo, regra.barreira, texto, round(regra.pontos_max * (1 - taxa), 2)))

    return sorted(barreiras, key=lambda b: (-b.pontos, _ORDEM_EIXO[b.eixo], b.codigo))


# --- Supressão de célula pequena (AD-08, decisão pendente 13; revisão do AgLGPD) ---------------

LIMIAR_CELULA_PEQUENA = 5
"""Abaixo disto, a contagem de matrículas da educação especial não sai da tela da própria escola:
somada a um relato, apontaria uma criança. Vale para o texto da IA e para a Declaração emitida."""


def celula_pequena(escola: Mapping) -> bool:
    return 0 < (escola["qt_mat_esp"] or 0) < LIMIAR_CELULA_PEQUENA


def texto_sem_celula_pequena(barreira: BarreiraIdentificada, escola: Mapping) -> str:
    """Texto do dado do Censo sem a contagem exata quando a célula é pequena."""
    if barreira.codigo == CLASSE_EXCLUSIVA and celula_pequena(escola):
        return "O Censo registra matrículas da educação especial em classes exclusivas (contagem omitida para não identificar estudantes)."
    return barreira.texto


def pontos_revelam_contagem(barreira: BarreiraIdentificada, escola: Mapping) -> bool:
    """Os pontos de B-IV-01 são 1,5 × (1 − taxa em classe comum): com poucas matrículas, revelam a contagem."""
    return barreira.codigo == CLASSE_EXCLUSIVA and celula_pequena(escola)
