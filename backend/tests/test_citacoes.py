"""Spec: docs/sdd/fase-2/arquitetura.md AD-08 — a IA só fundamenta no que o montador entregou."""

import asyncio

import pytest
from pydantic import BaseModel

from app.shared import ai_client
from app.shared.contexto_ia import base_normativa
from app.shared.contexto_ia.citacoes import CitacaoInvalida, Fundamento, gerar_resposta_fundamentada, validar_citacoes
from app.shared.contexto_ia.montador import montar_contexto
from app.shared.guardiao_lgpd import proteger
from etl.base_normativa import construir as etl

pytestmark = pytest.mark.skipif(not etl.TEXTOS.exists(), reason="textos legais ausentes em base/legislacao/")


class RespostaTeste(BaseModel):
    resposta: str
    fundamentos: list[Fundamento]
    lacunas: list[str]


class SemLacunas(BaseModel):
    resposta: str


@pytest.fixture(scope="module")
def contexto(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("base") / "base_normativa.db"
    etl.construir(com_embeddings=False, saida=caminho)
    base = base_normativa.carregar(caminho)
    # Escola de Cabixi/RO, foco em Braille e em recursos (Art. 19, VII e 19-A entram pela pergunta).
    pergunta = proteger("Material em Braille e recursos do Fundeb").texto_protegido
    return asyncio.run(montar_contexto(11050098, pergunta=pergunta, barreiras_foco=["B-III-02"], base=base))


def _resposta(texto="", fontes=(), lacunas=()):
    fundamentos = [Fundamento(afirmacao="afirmação", fontes=list(fontes))] if fontes else []
    return RespostaTeste(resposta=texto, fundamentos=fundamentos, lacunas=list(lacunas))


def test_contexto_de_teste_tem_os_trechos_esperados(contexto):
    assert {"LBI-art28-XII", "D12686-art19A"} <= contexto.ids_citaveis


def test_citacao_valida_passa(contexto):
    relatorio = validar_citacoes(
        _resposta("Conforme a LBI, Art. 28, XII [LBI-art28-XII], cabe ao poder público ofertar Braille.", ["LBI-art28-XII"]),
        contexto,
    )
    assert relatorio.ids_usados == {"LBI-art28-XII"}


def test_identificador_fora_do_contexto_reprova(contexto):
    with pytest.raises(CitacaoInvalida) as erro:
        validar_citacoes(_resposta("Ver [LBI-art27].", ["LBI-art27"]), contexto)
    assert ("trecho_fora", "LBI-art27") in erro.value.problemas


def test_identificador_inventado_reprova(contexto):
    with pytest.raises(CitacaoInvalida):
        validar_citacoes(_resposta("texto", ["LDB-art59"]), contexto)


@pytest.mark.parametrize(
    "texto",
    [
        "Segundo o Art. 59 da LDB, a escola deve adaptar o currículo.",
        "A Lei nº 9.394/1996 garante o atendimento.",
        "O Decreto 12.773/2025 elevou a carga horária.",
        "Conforme a Resolução 4/2009 e o artigo 3º.",
    ],
)
def test_mencao_livre_a_norma_fora_do_contexto_reprova(contexto, texto):
    with pytest.raises(CitacaoInvalida):
        validar_citacoes(_resposta(texto, ["LBI-art28-XII"]), contexto)


@pytest.mark.parametrize(
    "texto",
    [
        "A LBI (Lei 13.146/2015), no Art. 28, trata do Braille.",
        "O Art. 19-A do Decreto 12.686/2025 assegura recursos do Fundeb.",
        "Os recursos do Fundeb seguem a Lei nº 14.113, citada no próprio decreto.",
    ],
)
def test_mencao_livre_ao_que_foi_entregue_passa(contexto, texto):
    validar_citacoes(_resposta(texto, ["LBI-art28-XII"]), contexto)


def test_sem_fonte_exige_lacuna_declarada(contexto):
    with pytest.raises(CitacaoInvalida, match="1 problema"):
        validar_citacoes(_resposta("A escola pode buscar parcerias."), contexto)
    validar_citacoes(_resposta("A escola pode buscar parcerias.", lacunas=["Sem base normativa sobre parcerias."]), contexto)


def test_schema_sem_campo_de_lacunas_nao_exige_lacuna(contexto):
    validar_citacoes(SemLacunas(resposta="Resposta sem norma."), contexto)


def test_fundamento_exige_ao_menos_uma_fonte():
    with pytest.raises(Exception):
        Fundamento(afirmacao="sem fonte", fontes=[])


# --- Integração com a cadeia de provedores ----------------------------------------------------

def _provedor(retorno):
    async def chamar(_system, _mensagens):
        return retorno

    return chamar


def _chamar(contexto, provedores, monkeypatch):
    monkeypatch.setattr(ai_client, "_PROVEDORES", provedores)
    sistema = proteger("Responda em JSON.").texto_protegido
    mensagens = [{"role": "user", "content": proteger("Pergunta").texto_protegido}]
    return asyncio.run(gerar_resposta_fundamentada(sistema, mensagens, RespostaTeste, contexto))


def test_citacao_invalida_passa_para_o_proximo_provedor(contexto, monkeypatch, caplog):
    inventada = {"resposta": "Art. 59 da LDB.", "fundamentos": [{"afirmacao": "x", "fontes": ["LDB-art59"]}], "lacunas": []}
    valida = {"resposta": "Ver [LBI-art28-XII].", "fundamentos": [{"afirmacao": "x", "fontes": ["LBI-art28-XII"]}], "lacunas": []}
    resposta, modelo = _chamar(contexto, [("inventa", _provedor(inventada)), ("cita", _provedor(valida))], monkeypatch)
    assert modelo == "cita"
    assert resposta.fundamentos[0].fontes == ["LBI-art28-XII"]
    # O log leva só a contagem por tipo, nunca o que a IA escreveu.
    assert "CitacaoInvalida: artigo_fora=1, trecho_fora=1" in caplog.text
    assert "LDB" not in caplog.text and "59" not in caplog.text


def test_log_nao_carrega_dado_ecoado_pela_ia(contexto, monkeypatch, caplog):
    # Caso montado pelo AgLGPD: a IA põe frase em "fontes", nome no identificador e CPF como artigo.
    eco = {
        "resposta": "Ver [LBI-art28-JoaoPedroSilva], a Lei 1234567 e o art. 52998224725.",
        "fundamentos": [{"afirmacao": "x", "fontes": ["aluno João Pedro, 5º ano, laudo F84", "LBI-art28-JoaoPedroSilva"]}],
        "lacunas": [],
    }
    with pytest.raises(RuntimeError):
        _chamar(contexto, [("eco", _provedor(eco))], monkeypatch)
    for fragmento in ("João", "Joao", "laudo", "F84", "52998224725", "1234567"):
        assert fragmento not in caplog.text
    # A conferência da saída (ai_client.conferir_saida) recusa o CPF e o laudo antes do validador.
    assert "SaidaInsegura(CPF, SAUDE)" in caplog.text

    # Sem CPF nem laudo, a resposta chega ao validador de citações, que também só registra contagens.
    caplog.clear()
    sem_documento = {
        "resposta": "Ver [LBI-art28-JoaoPedroSilva] e a Lei 1234567.",
        "fundamentos": [{"afirmacao": "x", "fontes": ["aluno João Pedro", "LBI-art28-JoaoPedroSilva"]}],
        "lacunas": [],
    }
    with pytest.raises(RuntimeError):
        _chamar(contexto, [("eco", _provedor(sem_documento))], monkeypatch)
    for fragmento in ("João", "Joao", "1234567"):
        assert fragmento not in caplog.text
    assert "fonte_mal_formada=2" in caplog.text and "referencia_invalida=1" in caplog.text


def test_identificador_com_sufixo_livre_nao_e_aceito(contexto):
    with pytest.raises(CitacaoInvalida) as erro:
        validar_citacoes(_resposta("texto", ["LBI-art28-XII-JoaoPedro"]), contexto)
    assert erro.value.tipos() == {"fonte_mal_formada": 1}


def test_nenhuma_resposta_valida_vira_falha_da_cadeia(contexto, monkeypatch):
    inventada = {"resposta": "Lei 9.394.", "fundamentos": [], "lacunas": []}
    with pytest.raises(RuntimeError):
        _chamar(contexto, [("a", _provedor(inventada)), ("b", _provedor(inventada))], monkeypatch)
