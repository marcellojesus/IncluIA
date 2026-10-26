"""Spec: docs/sdd/fase-2/requirements/diretor/plano-acao-escolar.md e business-rules (RN-PAE-00 a 05)."""

from app.shared import ai_client
from tests.test_declaracao import ambiente, _estado, _provedor  # noqa: F401 — fixture e auxiliares compartilhados

TEXTO = "A gestão escolar relata que pediu o recurso à secretaria em 2025 e não teve resposta."


def _emitir(cliente, auth, texto=TEXTO):
    """Primeira barreira com obstáculo relatado, as demais sem relato; emite a próxima versão."""
    barreiras = _estado(cliente, auth)["barreiras"]
    for i, b in enumerate(barreiras):
        corpo = {"posicao": "obstaculo", "texto": texto, "resumo": "Pedido sem resposta"} if i == 0 else {"posicao": "sem_relato"}
        cliente.put(f"/gestao/diretor/declaracao/barreiras/{b['codigo']}", json=corpo, headers=auth)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=auth)
    return barreiras[0]["codigo"], barreiras[1]["codigo"]


def _sugestao(acao="Solicitar formalmente à secretaria a contratação do profissional.", fontes=None, lacunas=None):
    return {
        "sugestoes": [{
            "acao": acao, "relacao": "Responde ao pedido sem resposta.", "responsavel": "direção da escola", "prazo": "até 3 meses",
            "horizonte": "LOA", "custo_estimado": "a estimar", "premissas": "Secretaria com orçamento.", "fontes": fontes or [],
            "incertezas": "Não se sabe o prazo da secretaria.",
        }],
        "lacunas": lacunas if lacunas is not None else ["A base normativa entregue não trata de prazos de resposta."],
    }


def _plano(cliente, auth):
    return cliente.get("/gestao/diretor/plano", headers=auth)


def test_sem_declaracao_emitida_o_plano_nao_comeca(ambiente):
    cliente, diretora, _ = ambiente
    resposta = _plano(cliente, diretora)
    assert resposta.status_code == 409 and "Emita a Declaração" in resposta.json()["detail"]
    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()
    assert painel["plano"]["estado"] == "sem_declaracao"


def test_sugestao_aceita_editada_e_submetida(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _sem = _emitir(cliente, diretora)
    plano = _plano(cliente, diretora).json()
    assert plano["declaracaoBase"] == 1 and not plano["desatualizado"] and not plano["podeSubmeter"]

    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao("Pedir à professora Ana Clara que acompanhe o caso.")], recebidos))])
    plano = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()
    [sugestao] = plano["sugestoes"]
    assert "Ana Clara" not in sugestao["acao"] and sugestao["horizonte"] == "LOA" and sugestao["lacunas"]
    assert "pediu o recurso" in str(recebidos[0][0])  # a posição da Declaração foi para o contexto

    plano = cliente.post(f"/gestao/diretor/plano/sugestoes/{sugestao['id']}/aceitar", json={}, headers=diretora).json()
    [acao] = plano["acoes"]
    assert acao["origem"] == "ia" and not acao["editada"] and plano["sugestoes"] == []

    corpo = {**{k: acao[k] for k in ("codigo", "acao", "relacao", "responsavel", "prazo", "horizonte", "custoEstimado", "premissas")}, "prazo": "até 6 meses"}
    plano = cliente.put(f"/gestao/diretor/plano/acoes/{acao['id']}", json=corpo, headers=diretora).json()
    assert plano["acoes"][0]["editada"] and plano["podeSubmeter"]

    assert cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": False}, headers=diretora).status_code == 422
    versao = cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora).json()
    assert versao["versao"] == 1 and versao["estado"] == "aguardando_analise" and versao["declaracaoVersao"] == 1
    assert versao["itens"][0]["origem"] == "ia" and versao["itens"][0]["editada"] and versao["itens"][0]["prazo"] == "até 6 meses"

    # Em análise: não sai outra versão; editar o rascunho não muda a versão enviada (RN-PAE-04).
    assert cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora).status_code == 409
    cliente.put(f"/gestao/diretor/plano/acoes/{acao['id']}", json={**corpo, "prazo": "até 12 meses"}, headers=diretora)
    assert cliente.get("/gestao/diretor/plano/versoes/1", headers=diretora).json()["itens"][0]["prazo"] == "até 6 meses"
    assert cliente.get("/gestao/diretor/escola", headers=diretora).json()["plano"]["estado"] == "aguardando_analise"


def test_sem_relato_e_lacuna_sem_sugestao(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _com, sem_relato = _emitir(cliente, diretora)

    async def nao_pode(*_args):
        raise AssertionError("a IA não pode ser chamada")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", nao_pode)])
    resposta = cliente.post(f"/gestao/diretor/plano/barreiras/{sem_relato}/sugestoes", json={}, headers=diretora)
    assert resposta.status_code == 409 and "lacuna" in resposta.json()["detail"]


def test_orientacao_com_dado_sensivel_bloqueia_antes_da_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)

    async def nao_pode(*_args):
        raise AssertionError("a IA não pode ser chamada")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", nao_pode)])
    resposta = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={"orientacao": "O aluno toma Ritalina."}, headers=diretora)
    assert resposta.status_code == 422


def test_fonte_inventada_passa_ao_proximo_provedor(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    inventada = _sugestao(fontes=["LDB-art59"], lacunas=[])
    valida = _sugestao()
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("inventa", _provedor([inventada], [])), ("certo", _provedor([valida], []))])
    plano = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()
    assert plano["sugestoes"][0]["fontes"] == []


def test_acao_propria_descartar_e_remover(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    nova = {"codigo": com_relato, "acao": "Organizar mutirão com a comunidade para adaptar o espaço.", "horizonte": "PPA"}
    plano = cliente.post("/gestao/diretor/plano/acoes", json=nova, headers=diretora).json()
    [acao] = plano["acoes"]
    assert acao["origem"] == "diretor"
    assert cliente.post("/gestao/diretor/plano/acoes", json={**nova, "codigo": "B-X-99"}, headers=diretora).status_code == 404

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao()], []))])
    plano = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()
    sugestao = plano["sugestoes"][0]["id"]
    assert cliente.post(f"/gestao/diretor/plano/sugestoes/{sugestao}/descartar", json={}, headers=diretora).json()["sugestoes"] == []

    # Outra escola não alcança a ação (RN-PAE-03).
    _emitir(cliente, outra)
    assert cliente.delete(f"/gestao/diretor/plano/acoes/{acao['id']}", headers=outra).status_code == 404
    assert cliente.delete(f"/gestao/diretor/plano/acoes/{acao['id']}", headers=diretora).json()["acoes"] == []


def test_nova_declaracao_sinaliza_plano_desatualizado(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    _plano(cliente, diretora)
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{com_relato}", json={"posicao": "divergencia", "texto": "O recurso existe e não foi declarado no Censo."}, headers=diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    plano = _plano(cliente, diretora).json()
    assert plano["desatualizado"] and plano["declaracaoBase"] == 1 and plano["ultimaDeclaracao"] == 2
    assert cliente.get("/gestao/diretor/escola", headers=diretora).json()["plano"]["desatualizado"]
    plano = cliente.post("/gestao/diretor/plano/atualizar-base", json={}, headers=diretora).json()
    assert plano["declaracaoBase"] == 2 and not plano["desatualizado"]


# --- Privacidade (revisão AgLGPD de 2026-10-25) ---------------------------------------------------

def test_acao_propria_com_dado_de_saude_de_estudante_bloqueia_e_nada_e_gravado(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    sensivel = {"codigo": com_relato, "acao": "Acompanhar o aluno Pedro, que tem autismo e toma Ritalina.", "horizonte": "LOA"}
    resposta = cliente.post("/gestao/diretor/plano/acoes", json=sensivel, headers=diretora)
    assert resposta.status_code == 422 and "A ação não foi salva" in resposta.json()["detail"]
    assert _plano(cliente, diretora).json()["acoes"] == []
    # Contraexemplo: a necessidade da escola, sem identificar estudante, é aceita.
    neutra = {**sensivel, "acao": "Garantir profissional de apoio para estudantes com deficiência na sala comum."}
    assert cliente.post("/gestao/diretor/plano/acoes", json=neutra, headers=diretora).status_code == 201


def test_responsavel_com_nome_de_pessoa_e_recusado(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    base = {"codigo": com_relato, "acao": "Solicitar à secretaria a contratação do profissional de AEE.", "horizonte": "LOA"}
    for nome in ("Professora Maria José", "coordenadora Ana Clara"):
        resposta = cliente.post("/gestao/diretor/plano/acoes", json={**base, "responsavel": nome}, headers=diretora)
        assert resposta.status_code == 422 and "cargo ou órgão" in resposta.json()["detail"], nome
    for cargo in ("direção da escola", "Secretaria Municipal de Educação", "coordenação pedagógica"):
        assert cliente.post("/gestao/diretor/plano/acoes", json={**base, "responsavel": cargo}, headers=diretora).status_code == 201, cargo


def test_nome_mascarado_na_acao_gera_aviso(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    corpo = {"codigo": com_relato, "acao": "Reunir com a professora Ana Clara para planejar o AEE.", "horizonte": "LOA"}
    plano = cliente.post("/gestao/diretor/plano/acoes", json=corpo, headers=diretora).json()
    assert "Ana Clara" not in plano["acoes"][0]["acao"] and plano["avisoGuardiao"]
    sem_nome = {**corpo, "acao": "Reunir a equipe pedagógica para planejar o AEE."}
    assert cliente.post("/gestao/diretor/plano/acoes", json=sem_nome, headers=diretora).json()["avisoGuardiao"] is None


def test_resposta_da_ia_com_dado_sensivel_descarta_o_campo(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    resposta = _sugestao()
    resposta["sugestoes"][0]["relacao"] = "O aluno Pedro tem autismo e toma Ritalina, por isso precisa de apoio."
    resposta["sugestoes"][0]["responsavel"] = "Professora Maria José"
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], []))])
    plano = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()
    [sugestao] = plano["sugestoes"]
    assert sugestao["relacao"] is None and sugestao["responsavel"] is None and plano["avisoGuardiao"]
    assert "Ritalina" not in str(plano)


def test_orientacao_com_nome_vai_mascarada_para_a_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao()], recebidos))])
    cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={"orientacao": "Converse com a professora Ana Clara antes."}, headers=diretora)
    enviado = str(recebidos[0])
    assert "Ana Clara" not in enviado and "[NOME]" in enviado


def test_outra_escola_nao_aceita_sugestao_nem_le_versao(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    _emitir(cliente, outra)
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao()], []))])
    sugestao = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()["sugestoes"][0]["id"]
    assert cliente.post(f"/gestao/diretor/plano/sugestoes/{sugestao}/aceitar", json={}, headers=outra).status_code == 404
    cliente.post(f"/gestao/diretor/plano/sugestoes/{sugestao}/aceitar", json={}, headers=diretora)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora)
    assert cliente.get("/gestao/diretor/plano/versoes/1", headers=outra).status_code == 404


# --- Ajustar com a IA e editar antes de incluir (PAE-RF-02) ---------------------------------------

def _uma_sugestao(cliente, auth, codigo, monkeypatch):
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao()], []))])
    return cliente.post(f"/gestao/diretor/plano/barreiras/{codigo}/sugestoes", json={}, headers=auth).json()["sugestoes"][0]


def test_ajustar_com_a_ia_substitui_a_sugestao(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    original = _uma_sugestao(cliente, diretora, com_relato, monkeypatch)

    recebidos = []
    ajustada = _sugestao("Solicitar à secretaria, em até 30 dias, a contratação do profissional.")
    ajustada["sugestoes"][0]["prazo"] = "até 1 mês"
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([ajustada], recebidos))])
    plano = cliente.post(f"/gestao/diretor/plano/sugestoes/{original['id']}/ajustar", json={"pedido": "Reduza o prazo para um mês."}, headers=diretora).json()
    [nova] = plano["sugestoes"]
    assert nova["id"] != original["id"] and nova["ajustada"] and nova["prazo"] == "até 1 mês"
    enviado = str(recebidos[0])
    assert "Proposta anterior" in enviado and original["acao"] in enviado and "Reduza o prazo" in enviado
    # A anterior não pode mais ser incluída nem ajustada.
    assert cliente.post(f"/gestao/diretor/plano/sugestoes/{original['id']}/aceitar", json={}, headers=diretora).status_code == 404


def test_pedido_de_ajuste_com_dado_sensivel_bloqueia_antes_da_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    original = _uma_sugestao(cliente, diretora, com_relato, monkeypatch)

    async def nao_pode(*_args):
        raise AssertionError("a IA não pode ser chamada")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", nao_pode)])
    resposta = cliente.post(f"/gestao/diretor/plano/sugestoes/{original['id']}/ajustar", json={"pedido": "O aluno toma Ritalina, considere isso."}, headers=diretora)
    assert resposta.status_code == 422
    assert _plano(cliente, diretora).json()["sugestoes"][0]["id"] == original["id"]  # a sugestão continua


def test_outra_escola_nao_ajusta_sugestao(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    _emitir(cliente, outra)
    original = _uma_sugestao(cliente, diretora, com_relato, monkeypatch)
    resposta = cliente.post(f"/gestao/diretor/plano/sugestoes/{original['id']}/ajustar", json={"pedido": "Reduza o prazo."}, headers=outra)
    assert resposta.status_code == 404


def test_editar_e_incluir_marca_como_editada(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    s = _uma_sugestao(cliente, diretora, com_relato, monkeypatch)
    edicao = {k: s[k] for k in ("codigo", "acao", "relacao", "responsavel", "prazo", "horizonte", "custoEstimado", "premissas")}
    plano = cliente.post(f"/gestao/diretor/plano/sugestoes/{s['id']}/aceitar", json={"edicao": {**edicao, "prazo": "até 2 meses"}}, headers=diretora).json()
    [acao] = plano["acoes"]
    assert acao["origem"] == "ia" and acao["editada"] and acao["prazo"] == "até 2 meses" and acao["fontes"] == s["fontes"]
    # A edição passa pelo Guardião como qualquer texto do diretor.
    outra = _uma_sugestao(cliente, diretora, com_relato, monkeypatch)
    resposta = cliente.post(f"/gestao/diretor/plano/sugestoes/{outra['id']}/aceitar", json={"edicao": {**edicao, "responsavel": "Professora Maria José"}}, headers=diretora)
    assert resposta.status_code == 422
