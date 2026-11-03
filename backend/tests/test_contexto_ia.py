"""Spec: docs/sdd/fase-2/arquitetura.md AD-08 — montador de contexto em camadas.

Roda sem rede: base normativa gerada sem embeddings num diretório temporário; a busca vetorial é
simulada com vetores sintéticos. Usa o artefato do Censo (data/incluia.db) para os fatos da escola.
"""

import asyncio
import re
import dataclasses

import numpy as np
import pytest

from app.shared import ai_client
from app.shared.contexto_ia import base_normativa, montador
from app.shared.contexto_ia.barreiras import CODIGOS_COM_REGRA, identificar
from app.shared.contexto_ia.busca import buscar, consulta_fts, fundir
from app.shared.guardiao_lgpd import TextoProtegido, proteger
from etl.base_normativa import construir as etl

pytestmark = pytest.mark.skipif(not etl.TEXTOS.exists(), reason="textos legais ausentes em base/legislacao/")

ESCOLA_APAE = 11050098  # Cabixi/RO: 5 matrículas, todas em classe exclusiva; sem Libras nem Braille
ESCOLA_UMA_MATRICULA = 13071653  # 1 matrícula da educação especial, em classe exclusiva
ESCOLA_NOME_G12 = 28033922  # nome termina em "VISAO G12"


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("base") / "base_normativa.db"
    etl.construir(com_embeddings=False, saida=caminho)
    return base_normativa.carregar(caminho)


@pytest.fixture
def base_com_vetores(base):
    """Vetores sintéticos ortogonais: a consulta igual ao vetor de um trecho o põe em 1º lugar."""
    ids = tuple(base.trechos)
    matriz = np.eye(len(ids), dtype=np.float32)
    meta = {**base.meta, "embeddings_modelo": ai_client.MODELO_EMBEDDING}
    return dataclasses.replace(base, ids_vetores=ids, matriz=matriz, meta=meta)


def _protegido(texto: str) -> TextoProtegido:
    return proteger(texto).texto_protegido


def _escola(**valores):
    padrao = {coluna: 1.0 for coluna in ("v_aee", "v_rampa", "v_banheiro_pne", "v_corrimao", "v_piso_tatil",
                                          "v_sinal_visual", "v_sinal_sonoro", "v_elevador", "v_libras", "v_braille")}
    return {**padrao, "qt_mat_esp": 10.0, "qt_mat_esp_cc": 10.0, **valores}


# --- Barreiras (metodologia, §3 a §5) ----------------------------------------------------------

def test_toda_barreira_da_metodologia_tem_regra(base):
    assert set(base.metodologia) == CODIGOS_COM_REGRA


def test_escola_completa_nao_tem_barreira(base):
    assert identificar(_escola(), base.metodologia) == []


def test_barreiras_ordenadas_por_pontos_em_jogo(base):
    codigos = [b.codigo for b in identificar(_escola(v_aee=0, v_elevador=0, v_braille=0, v_rampa=0), base.metodologia)]
    assert codigos == ["B-I-01", "B-III-02", "B-II-01", "B-II-07"]


def test_eixo_iv_proporcional_a_classe_exclusiva(base):
    [barreira] = identificar(_escola(qt_mat_esp=10.0, qt_mat_esp_cc=6.0), base.metodologia)
    assert barreira.codigo == "B-IV-01"
    assert barreira.pontos == pytest.approx(0.6)
    assert "4 de 10 matrículas" in barreira.texto


def test_sem_matricula_especial_nao_tem_barreira_no_eixo_iv(base):
    assert identificar(_escola(qt_mat_esp=0.0, qt_mat_esp_cc=0.0), base.metodologia) == []


def test_notas_de_elevador_e_dado_nao_informado(base):
    barreiras = {b.codigo: b for b in identificar(_escola(v_elevador=0, v_rampa=None), base.metodologia)}
    assert "térreos" in barreiras["B-II-07"].nota
    assert "não registrada" in barreiras["B-II-01"].nota


# --- Busca --------------------------------------------------------------------------------------

def test_consulta_fts_tira_marcadores_e_palavras_vazias():
    assert consulta_fts("O [NOME], do [TURMA], é cego e não temos material em Braille") == "cego* OR material* OR braille*"
    assert consulta_fts("o que é isso?") is None


def test_rrf_premia_quem_aparece_nas_duas_listas():
    assert fundir(["a", "b", "c"], ["c", "d"])[0] == "c"


def test_busca_sem_embeddings_usa_palavra_chave(base):
    resultado = asyncio.run(buscar(base, _protegido("Não temos material em Braille para o aluno cego")))
    assert resultado.modo == "palavra_chave"
    assert resultado.motivo
    assert resultado.ids[0] == "LBI-art28-XII"


def test_busca_hibrida_quando_ha_vetores(base_com_vetores, monkeypatch):
    ids = base_com_vetores.ids_vetores
    alvo = ids.index("D12686-art14-p2")

    async def vetor_falso(_pergunta):
        return np.eye(len(ids), dtype=np.float32)[alvo]

    monkeypatch.setattr(ai_client, "gerar_embedding_consulta", vetor_falso)
    resultado = asyncio.run(buscar(base_com_vetores, _protegido("Pode exigir laudo para o profissional de apoio?")))
    assert resultado.modo == "hibrida"
    assert resultado.ids[0] == "D12686-art14-p2"


def test_busca_cai_para_palavra_chave_se_a_api_falha(base_com_vetores, monkeypatch):
    async def falha(_pergunta):
        raise RuntimeError("fora")

    monkeypatch.setattr(ai_client, "gerar_embedding_consulta", falha)
    resultado = asyncio.run(buscar(base_com_vetores, _protegido("material em Braille")))
    assert resultado.modo == "palavra_chave"
    assert resultado.motivo == "API de embeddings indisponível"
    assert "LBI-art28-XII" in resultado.ids


def test_busca_exige_texto_protegido(base):
    with pytest.raises(TypeError):
        asyncio.run(buscar(base, "material em Braille"))


# --- Montador -----------------------------------------------------------------------------------

def _montar(base, **kwargs):
    return asyncio.run(montador.montar_contexto(ESCOLA_APAE, base=base, **kwargs))


def _registro(texto: str, co_entidade: int = ESCOLA_APAE) -> montador.RegistroDaEscola:
    return montador.RegistroDaEscola(co_entidade, _protegido(texto))


def test_contexto_tem_as_camadas_e_so_cita_o_que_entregou(base):
    privado = [_registro("B-III-02: obstáculo relatado. A rede nunca contratou revisor de Braille.")]
    ctx = _montar(base, pergunta=_protegido("Não temos material em Braille"), barreiras_foco=["B-III-02"], registros=privado)
    texto = str(ctx.texto)

    assert isinstance(ctx.texto, TextoProtegido)
    assert "## Fatos da escola" in texto and "B-IV-01" in texto  # C1 traz todas as barreiras
    assert "regra QT_PROF_REVISOR_BRAILLE = 0" in texto  # C2 só da barreira em foco
    assert "QT_PROF_TRAD_LIBRAS" not in texto
    assert "nunca contratou revisor" in texto  # C4
    assert "LBI-art28-XII" in ctx.ids_citaveis  # C3
    for trecho_id in ctx.ids_citaveis:
        assert f"[{trecho_id}]" in texto
    assert texto.count("\n[") == len(ctx.ids_citaveis)


def test_sem_pergunta_usa_so_o_mapa_da_barreira(base):
    ctx = _montar(base, barreiras_foco=["B-IV-01"])
    assert ctx.modo_busca == "sem_pergunta"
    assert ctx.ids_citaveis == {"D12686-art1-p3", "D12686-art8"}


def test_orcamento_corta_trechos_mas_nao_fatos(base):
    completo = _montar(base, pergunta=_protegido("intérprete de Libras e Braille"))
    apertado = _montar(base, pergunta=_protegido("intérprete de Libras e Braille"), orcamento_tokens=completo.tokens_estimados - 150)
    assert len(apertado.ids_citaveis) < len(completo.ids_citaveis)
    assert apertado.tokens_estimados <= completo.tokens_estimados - 150
    assert "## Fatos da escola" in str(apertado.texto)


def test_orcamento_sem_espaco_registra_lacuna(base):
    ctx = _montar(base, orcamento_tokens=50)
    assert ctx.ids_citaveis == frozenset()
    assert "sem trecho normativo de suporte no contexto" in ctx.lacunas
    assert "## Base normativa" not in str(ctx.texto)


def test_entradas_invalidas(base):
    with pytest.raises(montador.EscolaNaoEncontrada):
        asyncio.run(montador.montar_contexto(1, base=base))
    with pytest.raises(ValueError):
        _montar(base, barreiras_foco=["B-IX-99"])
    with pytest.raises(TypeError):
        _montar(base, pergunta="texto cru")
    with pytest.raises(TypeError):
        _montar(base, registros=["texto cru"])
    with pytest.raises(TypeError):
        _montar(base, registros=[_protegido("registro sem a escola de origem")])


def test_registro_de_outra_escola_e_recusado(base):
    with pytest.raises(ValueError, match="outra escola"):
        _montar(base, registros=[_registro("Relato da escola B.", co_entidade=ESCOLA_APAE + 1)])


def test_nome_e_codigo_da_escola_nao_vao_a_ia(base):
    texto = str(_montar(base).texto)
    assert "LUCELAINE" not in texto and str(ESCOLA_APAE) not in texto
    # Sem município desde 2026-11-03: com o score público, ele apontava a escola (revisão do AgLGPD, A1).
    assert "a escola em análise, rede" in texto and "Cabixi" not in texto and "CABIXI" not in texto


def test_celula_pequena_e_omitida(base):
    texto = str(asyncio.run(montador.montar_contexto(ESCOLA_UMA_MATRICULA, base=base)).texto)
    assert "menos de 5 (número omitido" in texto
    assert "1 de 1" not in texto and "Matrículas da educação especial: 1" not in texto
    assert "contagem omitida para não identificar estudantes" in texto


def test_escola_com_nome_parecido_com_cid_tem_contexto(base):
    # "…VISÃO G12" casava com o padrão de CID e bloqueava a escola inteira (revisão do AgLGPD).
    ctx = asyncio.run(montador.montar_contexto(ESCOLA_NOME_G12, base=base))
    assert "G12" not in str(ctx.texto)


def test_base_ausente(tmp_path):
    with pytest.raises(base_normativa.BaseNormativaIndisponivel):
        base_normativa.carregar(tmp_path / "nao_existe.db")


# --- Revisão do AgLGPD: supressão de célula pequena não pode ser revertida ----------------------

@pytest.mark.parametrize("co_entidade", [13265253, 14006693, 14008394, ESCOLA_UMA_MATRICULA])
def test_celula_pequena_nao_deixa_deduzir_a_taxa(base, co_entidade):
    texto = str(asyncio.run(montador.montar_contexto(co_entidade, barreiras_foco=["B-IV-01"], base=base)).texto)
    assert "IV omitido" in texto
    assert not re.search(r"Score Escola Sem Barreiras: \d", texto)  # o total permitiria recalcular o eixo IV
    assert "B-IV-01 Matrículas da educação especial em classes exclusivas: pontos omitidos" in texto
    assert "1,5 × (1 − Taxa_CC)" not in texto and "Taxa_CC" not in texto
    assert not re.search(r"\b\d+ de \d+ matrículas", texto)


def test_escola_grande_vai_so_com_faixas(base):
    texto = str(_montar(base).texto)  # 5 matrículas: no limiar, não é célula pequena
    assert "Score Escola Sem Barreiras: faixa" in texto and "IV omitido" not in texto
    assert not re.search(r"Score Escola Sem Barreiras: \d", texto) and not re.search(r"Eixos: I \d", texto)
    assert "Matrículas da educação especial: de 5 a 9" in texto
