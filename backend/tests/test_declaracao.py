"""Spec: docs/sdd/fase-2/requirements/diretor/declaracao-obstaculos.md e business-rules (RN-DO-01 a 09)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from tests import banco as banco_teste
from app.features.acesso import servico as acesso
from app.features.declaracao.modelos import DeclaracaoItem, MensagemObstaculo, Posicao
from app.main import app
from app.shared import ai_client, banco_gestao
from app.shared import email as envio

NITEROI = 3303302
ESCOLA, OUTRA_ESCOLA = 33055238, 33056323


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    banco_teste.preparar(tmp_path)
    codigos: dict[str, str] = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))
    cliente = TestClient(app)

    sessao = next(banco_gestao.obter_sessao())
    admin = acesso.criar_admin(sessao, nome="Admin Teste", email="admin@teste.gov.br")
    acesso.provisionar_secretario(sessao, admin=admin, nome="Sec Niterói", email="sec@niteroi.gov.br", co_municipio=NITEROI, categoria="oficio", metodo="Ofício de teste")
    sessao.close()
    secretaria = _entrar(cliente, codigos, "sec@niteroi.gov.br")

    diretores = {}
    for email, escola in (("diretora@escola.gov.br", ESCOLA), ("outra@escola.gov.br", OUTRA_ESCOLA)):
        cliente.post("/gestao/acesso/diretor", json={"nome": "Diretora Teste", "email": email, "coEntidade": escola})
        cliente.post("/gestao/acesso/entrar", json={"email": email, "codigo": codigos[email]})
    for pedido in cliente.get("/gestao/secretario/vinculos", headers=secretaria).json():
        cliente.post(f"/gestao/secretario/vinculos/{pedido['id']}/aprovar", json={"categoria": "oficio", "texto": "Portaria conferida"}, headers=secretaria)
    for email in ("diretora@escola.gov.br", "outra@escola.gov.br"):
        _envelhecer(email)
        diretores[email] = _entrar(cliente, codigos, email, pedir=True)

    cliente.headers_secretaria = secretaria  # para os testes da visão do secretário
    yield cliente, diretores["diretora@escola.gov.br"], diretores["outra@escola.gov.br"]
    banco_gestao.configurar()


def _envelhecer(email):
    from datetime import timedelta

    from app.features.acesso.modelos import CodigoUsoUnico

    sessao = next(banco_gestao.obter_sessao())
    for registro in sessao.scalars(select(CodigoUsoUnico).where(CodigoUsoUnico.email == email)):
        registro.criado_em = registro.criado_em - timedelta(minutes=2)
    sessao.commit()
    sessao.close()


def _entrar(cliente, codigos, email, pedir=False):
    if pedir:
        cliente.post("/gestao/acesso/codigo", json={"email": email})
    resposta = cliente.post("/gestao/acesso/entrar", json={"email": email, "codigo": codigos[email]}).json()
    assert resposta["situacao"] == "ativo", resposta
    return {"Authorization": f"Bearer {resposta['token']}"}


def _estado(cliente, auth):
    return cliente.get("/gestao/diretor/declaracao", headers=auth).json()


def _posicionar_todas(cliente, auth, posicao="sem_relato"):
    for barreira in _estado(cliente, auth)["barreiras"]:
        corpo = {"posicao": posicao, "texto": "A sala existe desde 2024, mas não foi declarada no Censo." if posicao != "sem_relato" else None}
        assert cliente.put(f"/gestao/diretor/declaracao/barreiras/{barreira['codigo']}", json=corpo, headers=auth).status_code == 200


# --- Posições ------------------------------------------------------------------------------------

def test_comeca_com_todas_as_barreiras_sem_posicao(ambiente):
    cliente, diretora, _ = ambiente
    estado = _estado(cliente, diretora)
    assert estado["coEntidade"] == ESCOLA and estado["barreiras"]
    assert {b["posicao"] for b in estado["barreiras"]} == {"sem_posicao"}
    assert estado["faltam"] == len(estado["barreiras"]) and not estado["podeEmitir"] and estado["versoes"] == []


def test_tres_posicoes_e_textos_mascarados(ambiente):
    cliente, diretora, _ = ambiente
    b1, b2, b3 = [b["codigo"] for b in _estado(cliente, diretora)["barreiras"][:3]]
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{b1}", json={"posicao": "sem_relato"}, headers=diretora)
    cliente.put(
        f"/gestao/diretor/declaracao/barreiras/{b2}",
        json={"posicao": "divergencia", "texto": "A rampa foi construída em 2024 pela professora Maria José e não entrou no Censo."},
        headers=diretora,
    )
    estado = cliente.put(
        f"/gestao/diretor/declaracao/barreiras/{b3}",
        json={"posicao": "obstaculo", "texto": "A gestão escolar relata que pediu o recurso à secretaria sem resposta.", "resumo": "Pedido sem resposta"},
        headers=diretora,
    ).json()
    por_codigo = {b["codigo"]: b for b in estado["barreiras"]}
    assert por_codigo[b1]["posicao"] == "sem_relato" and por_codigo[b1]["texto"] is None
    assert por_codigo[b2]["posicao"] == "divergencia" and "Maria" not in por_codigo[b2]["texto"] and "[NOME]" in por_codigo[b2]["texto"]
    assert por_codigo[b3]["posicao"] == "obstaculo" and por_codigo[b3]["resumo"] == "Pedido sem resposta"


def test_dado_de_risco_alto_bloqueia_a_posicao(ambiente):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    resposta = cliente.put(
        f"/gestao/diretor/declaracao/barreiras/{codigo}",
        json={"posicao": "obstaculo", "texto": "O aluno do 3º ano toma Ritalina e não temos apoio."},
        headers=diretora,
    )
    assert resposta.status_code == 422 and "Reescreva" in resposta.json()["detail"]
    assert _estado(cliente, diretora)["barreiras"][0]["posicao"] == "sem_posicao"


def test_divergencia_e_obstaculo_exigem_texto(ambiente):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    for posicao in ("divergencia", "obstaculo"):
        assert cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": posicao, "texto": ""}, headers=diretora).status_code == 422


def test_barreira_que_a_escola_nao_tem(ambiente):
    cliente, diretora, _ = ambiente
    codigos = {b["codigo"] for b in _estado(cliente, diretora)["barreiras"]}
    inexistente = next(c for c in ("B-I-01", "B-II-01", "B-II-02", "B-III-01", "B-IV-01", "B-II-07") if c not in codigos)
    assert cliente.put(f"/gestao/diretor/declaracao/barreiras/{inexistente}", json={"posicao": "sem_relato"}, headers=diretora).status_code == 404


# --- Emissão e versões ---------------------------------------------------------------------------

def test_emissao_exige_todas_as_posicoes(ambiente):
    cliente, diretora, _ = ambiente
    primeira = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{primeira}", json={"posicao": "sem_relato"}, headers=diretora)
    resposta = cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    assert resposta.status_code == 409 and "Faltam" in resposta.json()["detail"]


def test_emitir_congela_e_retificar_gera_nova_versao(ambiente):
    cliente, diretora, _ = ambiente
    _posicionar_todas(cliente, diretora)
    v1 = cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    assert v1.status_code == 201 and v1.json()["versao"] == 1
    assert all(i["posicao"] == "sem_relato" for i in v1.json()["itens"])

    # Sem alteração não há nova versão.
    assert cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora).status_code == 409
    estado = _estado(cliente, diretora)
    assert not estado["haAlteracoes"] and not estado["podeEmitir"]

    # Retificar uma posição muda o rascunho, não a versão emitida.
    codigo = estado["barreiras"][0]["codigo"]
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": "divergencia", "texto": "O recurso existe e não foi declarado no Censo."}, headers=diretora)
    assert _estado(cliente, diretora)["haAlteracoes"]
    assert cliente.get("/gestao/diretor/declaracao/versoes/1", headers=diretora).json()["itens"][0]["posicao"] == "sem_relato"

    v2 = cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora).json()
    assert v2["versao"] == 2 and v2["itens"][0]["posicao"] == "divergencia"
    assert [v["versao"] for v in _estado(cliente, diretora)["versoes"]] == [1, 2]

    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()
    assert painel["declaracao"]["estado"] == "emitida" and painel["declaracao"]["versao"] == 2
    assert painel["declaracao"]["comPosicao"] == painel["declaracao"]["total"]


def test_versao_emitida_nao_muda_quando_o_rascunho_volta_a_sem_posicao(ambiente):
    cliente, diretora, _ = ambiente
    _posicionar_todas(cliente, diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    estado = cliente.delete(f"/gestao/diretor/declaracao/barreiras/{codigo}", headers=diretora).json()
    assert estado["faltam"] == 1
    sessao = next(banco_gestao.obter_sessao())
    itens = sessao.scalars(select(DeclaracaoItem)).all()
    sessao.close()
    assert all(i.posicao == "sem_relato" for i in itens)


def test_diretor_so_ve_a_propria_escola(ambiente):
    cliente, diretora, outra = ambiente
    _posicionar_todas(cliente, diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    assert _estado(cliente, outra)["coEntidade"] == OUTRA_ESCOLA
    assert _estado(cliente, outra)["versoes"] == []
    assert cliente.get("/gestao/diretor/declaracao/versoes/1", headers=outra).status_code == 404


# --- Conversa com a IA ---------------------------------------------------------------------------

def _provedor(retornos, recebidos):
    async def chamar(sistema, mensagens):
        recebidos.append((sistema, mensagens))
        return retornos.pop(0)

    return chamar


def test_conversa_mascara_guarda_e_vira_relato_original(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    recebidos = []
    retornos = [
        {"resposta": "A escola formalizou o pedido à secretaria?", "texto_formal": None, "resumo": None},
        {"resposta": "Proponho o texto abaixo.", "texto_formal": "A gestão escolar relata que solicitou o recurso em 2025 e aguarda resposta.", "resumo": "Pedido de 2025 sem resposta"},
    ]
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor(retornos, recebidos))])

    r1 = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "A professora Ana Clara pediu o recurso e nada aconteceu."}, headers=diretora)
    assert r1.status_code == 200 and r1.json()["textoFormal"] is None
    assert "Ana Clara" not in str(recebidos[0][1])  # o provedor só viu o texto mascarado
    assert _estado(cliente, diretora)["barreiras"][0]["posicao"] == "rascunho"

    r2 = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"formalizar": True}, headers=diretora)
    proposta = r2.json()
    assert proposta["textoFormal"].startswith("A gestão escolar relata")

    historico = cliente.get(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", headers=diretora).json()
    assert [m["papel"] for m in historico] == ["diretor", "ia", "ia"]
    assert "Ana Clara" not in historico[0]["texto"]

    # Só a confirmação do diretor registra (RN-DO-02); o relato original fica, a conversa sai.
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": "obstaculo", "texto": proposta["textoFormal"], "resumo": proposta["resumo"]}, headers=diretora)
    sessao = next(banco_gestao.obter_sessao())
    posicao = sessao.scalar(select(Posicao).where(Posicao.codigo == codigo))
    restantes = sessao.scalars(select(MensagemObstaculo)).all()
    sessao.close()
    assert "[NOME] pediu o recurso" in posicao.relato_original and restantes == []


def test_conversa_bloqueia_dado_de_saude_antes_da_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]

    async def nao_pode(*_args):
        raise AssertionError("a IA não pode ser chamada")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", nao_pode)])
    resposta = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "O aluno tem laudo de autismo."}, headers=diretora)
    assert resposta.status_code == 422
    assert cliente.get(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", headers=diretora).json() == []


def test_ia_indisponivel_nao_grava_e_orienta_escrever_direto(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]

    async def fora(*_args):
        raise RuntimeError("fora do ar")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", fora)])
    resposta = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "Pedimos o recurso e nada aconteceu."}, headers=diretora)
    assert resposta.status_code == 503 and "diretamente" in resposta.json()["detail"]
    assert cliente.get(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", headers=diretora).json() == []


def test_proposta_com_lei_inventada_e_recusada(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    recebidos = []
    retornos = [
        {"resposta": "Ok.", "texto_formal": "A gestão escolar relata que, conforme a Lei 9.394, o recurso falta.", "resumo": None},
        {"resposta": "Ok.", "texto_formal": "A gestão escolar relata que o recurso falta desde 2024.", "resumo": None},
    ]
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("inventa", _provedor(retornos, recebidos)), ("certo", _provedor(retornos, recebidos))])
    resposta = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "O recurso falta desde 2024."}, headers=diretora).json()
    assert "9.394" not in (resposta["textoFormal"] or "")


# --- Revisão do AgLGPD (2026-10-23) --------------------------------------------------------------

def test_emissao_confere_de_novo_os_textos(ambiente):
    cliente, diretora, _ = ambiente
    _posicionar_todas(cliente, diretora)
    # Simula um texto gravado antes de uma regra nova do guardião.
    sessao = next(banco_gestao.obter_sessao())
    posicao = sessao.scalars(select(Posicao)).first()
    posicao.posicao, posicao.texto = "divergencia", "A família informou o CPF 529.982.247-25 na secretaria."
    codigo = posicao.codigo
    sessao.commit()
    sessao.close()
    resposta = cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    assert resposta.status_code == 409 and codigo in resposta.json()["detail"]
    assert _estado(cliente, diretora)["versoes"] == []


def test_versao_emitida_sem_contagem_de_celula_pequena():
    from app.shared.contexto_ia import base_normativa
    from app.shared.contexto_ia.barreiras import identificar, texto_sem_celula_pequena

    escola = {"v_aee": 1, "v_rampa": 1, "v_banheiro_pne": 1, "v_corrimao": 1, "v_piso_tatil": 1, "v_sinal_visual": 1,
              "v_sinal_sonoro": 1, "v_elevador": 1, "v_libras": 1, "v_braille": 1, "qt_mat_esp": 1.0, "qt_mat_esp_cc": 0.0}
    [barreira] = identificar(escola, base_normativa.carregar().metodologia)
    assert "1 de 1" in barreira.texto  # a tela da própria escola mostra o número
    assert "1 de 1" not in texto_sem_celula_pequena(barreira, escola)  # a versão emitida, não


def test_fala_da_ia_e_mascarada(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    retornos = [{"resposta": "Entendi. A professora Ana Clara formalizou o pedido?", "texto_formal": None, "resumo": None}]
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor(retornos, []))])
    resposta = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "Pedimos o recurso em 2025."}, headers=diretora).json()
    assert "Ana Clara" not in resposta["resposta"]
    historico = cliente.get(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", headers=diretora).json()
    assert all("Ana Clara" not in m["texto"] for m in historico)


def test_mensagem_longa_e_recusada_com_aviso(ambiente):
    cliente, diretora, _ = ambiente
    codigo = _estado(cliente, diretora)["barreiras"][0]["codigo"]
    resposta = cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": "a" * 1999 + " bb"}, headers=diretora)
    assert resposta.status_code in (422,)


def test_conversa_parada_e_apagada(ambiente):
    from datetime import timedelta

    from app.features.declaracao.conversa import limpar_conversas_paradas

    sessao = next(banco_gestao.obter_sessao())
    sessao.add(MensagemObstaculo(co_entidade=ESCOLA, codigo="B-I-01", papel="diretor", texto="Relato antigo."))
    sessao.add(MensagemObstaculo(co_entidade=ESCOLA, codigo="B-II-01", papel="diretor", texto="Relato recente."))
    sessao.commit()
    antiga = sessao.scalar(select(MensagemObstaculo).where(MensagemObstaculo.codigo == "B-I-01"))
    antiga.criado_em = antiga.criado_em - timedelta(days=31)
    sessao.commit()
    assert limpar_conversas_paradas(sessao) == 1
    assert [m.codigo for m in sessao.scalars(select(MensagemObstaculo))] == ["B-II-01"]
    sessao.close()


# --- Pergunta inicial por barreira ---------------------------------------------------------------

def test_toda_barreira_tem_pergunta_inicial_propria():
    from app.features.declaracao.conversa import PERGUNTAS_INICIAIS
    from app.shared.contexto_ia.barreiras import CODIGOS_COM_REGRA

    assert set(PERGUNTAS_INICIAIS) == CODIGOS_COM_REGRA
    assert all(p.endswith("?") or p.endswith(".") for p in PERGUNTAS_INICIAIS.values())


def test_pergunta_inicial_vai_na_tela_e_para_a_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    barreira = _estado(cliente, diretora)["barreiras"][0]
    assert barreira["perguntaInicial"].startswith("O que tem")
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([{"resposta": "Ok?"}], recebidos))])
    cliente.post(f"/gestao/diretor/declaracao/barreiras/{barreira['codigo']}/conversa", json={"mensagem": "Falta verba."}, headers=diretora)
    primeira = recebidos[0][1][0]
    assert primeira["role"] == "assistant" and primeira["content"] == barreira["perguntaInicial"]


# --- Publicação ----------------------------------------------------------------------------------

def _emitir_com_textos(cliente, auth, texto):
    barreiras = _estado(cliente, auth)["barreiras"]
    for i, b in enumerate(barreiras):
        corpo = {"posicao": "obstaculo", "texto": texto, "resumo": "Resumo"} if i == 0 else {"posicao": "sem_relato"}
        cliente.put(f"/gestao/diretor/declaracao/barreiras/{b['codigo']}", json=corpo, headers=auth)
    return cliente.post("/gestao/diretor/declaracao/emitir", headers=auth).json()


def test_publicar_exige_aprovacao_e_aparece_na_pagina_publica(ambiente):
    cliente, diretora, _ = ambiente
    _emitir_com_textos(cliente, diretora, "A gestão escolar relata que a professora Maria José pediu o recurso em 2025, sem resposta.")
    assert cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json() is None

    previa = cliente.get("/gestao/diretor/declaracao/versoes/1/publica", headers=diretora).json()
    assert previa["podePublicar"]
    assert any("dado pessoal removido" in p["mensagem"] for p in previa["pontos"])
    assert previa["itens"][0]["textoPublico"].startswith("A escola relata:")
    assert "Maria" not in previa["itens"][0]["textoPublico"] and "[dado pessoal removido]" in previa["itens"][0]["textoPublico"]
    assert previa["itens"][1]["textoPublico"] == "A escola não apresentou relato nesta versão."

    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": False}, headers=diretora).status_code == 422
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 200
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 409

    publica = cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json()  # sem autenticação
    assert publica["versao"] == 1 and publica["publicadaEm"]
    assert "Maria" not in str(publica)
    assert not ({"relatoOriginal", "emitidaPor", "publicadaPor", "resumo", "texto"} & (set(publica) | set(publica["itens"][0])))
    assert cliente.get("/gestao/diretor/escola", headers=diretora).json()["declaracao"]["estado"] == "publicada"


def test_texto_publicado_fica_congelado(ambiente):
    from app.features.declaracao import publicacao

    cliente, diretora, _ = ambiente
    _emitir_com_textos(cliente, diretora, "A gestão escolar relata que o pedido de 2025 segue sem resposta.")
    cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    antes = cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json()["itens"][0]["textoPublico"]
    # Mesmo que a montagem da frase mude depois, o que foi aprovado não muda.
    original = publicacao._frase
    publicacao._frase = lambda posicao, texto: "TEXTO NOVO"
    try:
        depois = cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json()["itens"][0]["textoPublico"]
    finally:
        publicacao._frase = original
    assert antes == depois


def test_so_a_versao_mais_recente_e_publicada(ambiente):
    cliente, diretora, _ = ambiente
    _emitir_com_textos(cliente, diretora, "A gestão escolar relata que o pedido de 2025 segue sem resposta.")
    codigo = _estado(cliente, diretora)["barreiras"][1]["codigo"]
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": "divergencia", "texto": "O recurso existe e não foi declarado no Censo."}, headers=diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 409
    assert not cliente.get("/gestao/diretor/declaracao/versoes/1/publica", headers=diretora).json()["podePublicar"]


def test_dado_sensivel_impede_publicar(ambiente):
    cliente, diretora, _ = ambiente
    _emitir_com_textos(cliente, diretora, "A gestão escolar relata que o pedido de 2025 segue sem resposta.")
    sessao = next(banco_gestao.obter_sessao())
    item = sessao.scalars(select(DeclaracaoItem).where(DeclaracaoItem.posicao == "obstaculo")).first()
    item.texto = "O aluno do 2º ano toma Ritalina e não tem apoio."  # simula regra nova do guardião
    sessao.commit()
    sessao.close()
    previa = cliente.get("/gestao/diretor/declaracao/versoes/1/publica", headers=diretora).json()
    assert not previa["podePublicar"] and any(p["bloqueia"] for p in previa["pontos"])
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 409


# --- Secretário ----------------------------------------------------------------------------------

def test_secretario_ve_versoes_emitidas_da_rede_e_nunca_rascunho(ambiente):
    cliente, diretora, outra = ambiente
    _emitir_com_textos(cliente, diretora, "A gestão escolar relata que o pedido de 2025 segue sem resposta.")
    codigo = _estado(cliente, outra)["barreiras"][0]["codigo"]
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": "sem_relato"}, headers=outra)  # só rascunho

    secretaria = cliente.headers_secretaria
    rede = cliente.get("/gestao/secretario/declaracoes", headers=secretaria).json()
    assert rede["comDeclaracao"] == 1 and rede["escolasMunicipais"] > 1
    [linha] = rede["escolas"]
    assert linha["coEntidade"] == ESCOLA and linha["obstaculos"] == 1 and linha["semRelato"] == linha["total"] - 1
    versao = cliente.get(f"/gestao/secretario/declaracoes/{ESCOLA}/versoes/1", headers=secretaria).json()
    assert versao["itens"][0]["texto"].startswith("A gestão escolar relata")
    assert cliente.get(f"/gestao/secretario/declaracoes/{OUTRA_ESCOLA}/versoes/1", headers=secretaria).status_code == 404


def test_diretor_nao_acessa_visao_do_secretario(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.get("/gestao/secretario/declaracoes", headers=diretora).status_code == 403


# --- Revisão do AgLGPD da publicação (2026-10-24) --------------------------------------------------

def _publicar_v1(cliente, auth, texto="A gestão escolar relata que o pedido de 2025 segue sem resposta."):
    _emitir_com_textos(cliente, auth, texto)
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/publicar", json={"aprovado": True}, headers=auth).status_code == 200


def test_diretor_retira_a_publicacao(ambiente):
    cliente, diretora, _ = ambiente
    _publicar_v1(cliente, diretora)
    assert cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json()["versao"] == 1
    assert cliente.post("/gestao/diretor/declaracao/versoes/1/retirar", json={"motivo": "inventado"}, headers=diretora).status_code == 422
    previa = cliente.post("/gestao/diretor/declaracao/versoes/1/retirar", json={"motivo": "decisao_da_escola"}, headers=diretora).json()
    assert previa["retiradaEm"] and not previa["podePublicar"]
    assert cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json() is None  # vale na hora, sem esperar o cache
    assert cliente.get("/gestao/diretor/escola", headers=diretora).json()["declaracao"]["estado"] == "emitida"
    # A versão continua guardada e visível à secretaria.
    assert cliente.get(f"/gestao/secretario/declaracoes/{ESCOLA}/versoes/1", headers=cliente.headers_secretaria).status_code == 200


def test_administracao_retira_a_pedido_de_titular(ambiente):
    cliente, diretora, _ = ambiente
    from app.features.acesso.modelos import Conta
    from app.features.declaracao import publicacao

    _publicar_v1(cliente, diretora)
    sessao = next(banco_gestao.obter_sessao())
    admin = sessao.scalar(select(Conta).where(Conta.papel == "admin"))
    publicacao.retirar(sessao, co_entidade=ESCOLA, numero=1, autor_id=admin.id, motivo="pedido_de_titular")
    sessao.close()
    from app.features.declaracao.router_publico import limpar_cache
    limpar_cache(ESCOLA)
    assert cliente.get(f"/escolas/{ESCOLA}/declaracao-publica").json() is None
    assert cliente.post(f"/gestao/admin/declaracoes/{ESCOLA}/versoes/1/retirar", json={"motivo": "outro"}, headers=diretora).status_code == 403


def test_rota_publica_nao_guarda_copia_e_ignora_inep_inexistente(ambiente):
    cliente, _, _ = ambiente
    resposta = cliente.get(f"/escolas/{ESCOLA}/declaracao-publica")
    assert resposta.headers["cache-control"] == "no-store" and resposta.headers["x-robots-tag"] == "noindex"
    assert cliente.get("/escolas/99999999/declaracao-publica").json() is None


def _item(texto):
    return DeclaracaoItem(codigo="B-II-02", eixo="II", barreira="Sem banheiro acessível", dado_censo="—", pontos=0.7, posicao="obstaculo", texto=texto)


def test_celula_pequena_e_estudante_no_singular_impede_publicar():
    from app.features.declaracao.publicacao import _preparar

    texto = "A gestão escolar relata que o estudante cadeirante não consegue usar o banheiro do andar de cima."
    _, pontos = _preparar(_item(texto), celula_pequena=True)
    assert any(p.bloqueia and "redação coletiva" in p.mensagem for p in pontos)
    _, pontos = _preparar(_item(texto), celula_pequena=False)
    assert not any(p.bloqueia for p in pontos)
    _, pontos = _preparar(_item("A gestão escolar relata que os estudantes cadeirantes não usam o banheiro."), celula_pequena=True)
    assert not any(p.bloqueia for p in pontos)


def test_cargo_unico_culpa_e_varias_remocoes_viram_atencao():
    from app.features.declaracao.publicacao import _preparar

    _, pontos = _preparar(_item("A gestão escolar relata que o secretário municipal recusou o pedido por descaso."), celula_pequena=False)
    mensagens = " ".join(p.mensagem for p in pontos)
    assert "cargo" in mensagens and "culpa" in mensagens and not any(p.bloqueia for p in pontos)
    _, pontos = _preparar(_item("A gestão escolar relata que [NOME] e [NOME] pediram o recurso."), celula_pequena=False)
    assert any("vários trechos removidos" in p.mensagem for p in pontos)
