"""Spec: docs/sdd/fase-2/requirements/secretario/fila-revisao-planos.md e business-rules (RN-SFR-01 a 06)."""

from tests.test_declaracao import ambiente  # noqa: F401 — fixture compartilhada
from tests.test_plano import _emitir, _plano

ACAO = "Solicitar formalmente à secretaria a contratação do profissional de AEE."


def _enviar(cliente, auth, acao=ACAO, horizonte="LOA"):
    codigo = _plano(cliente, auth).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": codigo, "acao": acao, "horizonte": horizonte}, headers=auth)
    return cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=auth).json()


def _fila(cliente):
    return cliente.get("/gestao/secretario/planos", headers=cliente.headers_secretaria).json()


def _decidir(cliente, co_entidade, versao, decisao, comentario=None):
    corpo = {"decisao": decisao, **({"comentario": comentario} if comentario else {})}
    return cliente.post(f"/gestao/secretario/planos/{co_entidade}/versoes/{versao}/decisao", json=corpo, headers=cliente.headers_secretaria)


def _co_entidade(cliente, auth):
    return cliente.get("/gestao/diretor/escola", headers=auth).json()["coEntidade"]


def test_fila_lista_so_escolas_com_versao_enviada(ambiente):
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _emitir(cliente, outra)
    _plano(cliente, outra)  # rascunho sem envio não entra na fila (RN-SFR-02)
    assert _fila(cliente)["planos"] == []
    _enviar(cliente, diretora)
    [linha] = _fila(cliente)["planos"]
    assert linha["coEntidade"] == _co_entidade(cliente, diretora) and linha["estado"] == "aguardando_analise"
    assert linha["acoes"] == 1 and linha["loa"] == 1 and linha["ppa"] == 0 and linha["declaracaoVersao"] == 1


def test_diretor_nao_acessa_a_fila(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.get("/gestao/secretario/planos", headers=diretora).status_code == 403


def test_secretario_le_a_versao_sem_rascunho_nem_autor(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    revisao = cliente.get(f"/gestao/secretario/planos/{co}/versoes/1", headers=cliente.headers_secretaria).json()
    assert revisao["versao"]["itens"][0]["acao"] == ACAO and revisao["versaoAtual"] == 1
    assert "submetidaPor" not in str(revisao) and "sugestoes" not in revisao
    assert cliente.get(f"/gestao/secretario/planos/{co}/versoes/9", headers=cliente.headers_secretaria).status_code == 404
    assert cliente.get("/gestao/secretario/planos/99999999/versoes/1", headers=cliente.headers_secretaria).status_code == 404


def test_pedir_ajustes_exige_comentario_e_o_diretor_ve_a_decisao(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    assert _decidir(cliente, co, 1, "ajustes").status_code == 422
    assert _decidir(cliente, co, 1, "reprovar", "curto").status_code == 422
    resposta = _decidir(cliente, co, 1, "ajustes", "Detalhe o prazo e o responsável pela solicitação.")
    assert resposta.status_code == 200 and resposta.json()["versao"]["estado"] == "ajustes_solicitados"
    assert resposta.json()["versao"]["decididaPor"] == "Sec Niterói"

    plano = _plano(cliente, diretora).json()
    [versao] = plano["versoes"]
    assert versao["estado"] == "ajustes_solicitados" and "Detalhe o prazo" in versao["comentario"] and plano["podeSubmeter"]
    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()["plano"]
    assert painel["estado"] == "ajustes_solicitados" and "Detalhe o prazo" in painel["comentario"] and painel["decididaEm"]

    # RN-SFR-03 e 06: a nova versão volta à análise; a anterior fica com sua decisão e não pode ser decidida de novo.
    _enviar(cliente, diretora, acao="Solicitar à secretaria, em até 3 meses, a contratação do profissional de AEE.")
    assert _decidir(cliente, co, 1, "aceitar").status_code == 409
    revisao = _decidir(cliente, co, 2, "aceitar").json()
    assert [v["estado"] for v in revisao["historico"]] == ["ajustes_solicitados", "aceito"]
    assert _decidir(cliente, co, 2, "reprovar", "Motivo qualquer para reprovar.").status_code == 409


def test_aceitar_sem_comentario_e_auditoria_sem_texto(ambiente):
    from app.features.acesso.modelos import EventoAuditoria
    from app.shared import banco_gestao

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "reprovar", "A ação não responde à barreira declarada pela escola.")
    sessao = next(banco_gestao.obter_sessao())
    [evento] = [e for e in sessao.query(EventoAuditoria).all() if e.acao == "plano_reprovado"]
    assert "responde" not in (evento.detalhe or "")
    sessao.close()


def test_comentario_com_dado_sensivel_bloqueia_e_nome_e_mascarado(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    assert _decidir(cliente, co, 1, "ajustes", "O aluno Pedro tem autismo e toma Ritalina, inclua isso.").status_code == 422
    revisao = _decidir(cliente, co, 1, "ajustes", "Converse com a professora Ana Clara e detalhe o prazo.").json()
    assert "Ana Clara" not in revisao["versao"]["comentario"]


def test_aviso_quando_a_escola_emitiu_declaracao_mais_nova(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, _ = _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{com_relato}", json={"posicao": "divergencia", "texto": "O recurso existe e não foi declarado no Censo."}, headers=diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)
    [linha] = _fila(cliente)["planos"]
    assert linha["declaracaoVersao"] == 1 and linha["ultimaDeclaracao"] == 2


def test_comentario_mascarado_avisa_o_secretario(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    revisao = _decidir(cliente, _co_entidade(cliente, diretora), 1, "ajustes", "Converse com a professora Ana Clara e detalhe o prazo.").json()
    assert "Ana Clara" not in revisao["versao"]["comentario"] and revisao["avisoGuardiao"]


def test_secretario_de_outro_municipio_nao_ve_nem_decide(ambiente, monkeypatch):
    from sqlalchemy import select

    from app.features.acesso import servico as acesso
    from app.features.acesso.modelos import Conta, EventoAuditoria
    from app.shared import banco_gestao
    from app.shared import email as envio
    from tests.test_declaracao import _entrar

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)

    codigos = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))
    sessao = next(banco_gestao.obter_sessao())
    admin = sessao.scalar(select(Conta).where(Conta.papel == "admin"))
    acesso.provisionar_secretario(sessao, admin=admin, nome="Sec Rio", email="sec@rio.gov.br", co_municipio=3304557, categoria="oficio", metodo="Ofício de teste")
    sessao.close()
    rio = _entrar(cliente, codigos, "sec@rio.gov.br")

    assert cliente.get("/gestao/secretario/planos", headers=rio).json()["planos"] == []
    assert cliente.get(f"/gestao/secretario/planos/{co}/versoes/1", headers=rio).status_code == 404
    assert cliente.post(f"/gestao/secretario/planos/{co}/versoes/1/decisao", json={"decisao": "aceitar"}, headers=rio).status_code == 404
    assert _plano(cliente, diretora).json()["versoes"][0]["estado"] == "aguardando_analise"
    sessao = next(banco_gestao.obter_sessao())
    assert not [e for e in sessao.scalars(select(EventoAuditoria)) if e.acao.startswith("plano_") and e.acao != "plano_submetido"]
    sessao.close()


# --- Apontamentos: o que a secretaria marcou para ajuste ------------------------------------------

def test_apontamentos_marcam_acao_e_barreira_para_o_diretor(ambiente):
    cliente, diretora, _ = ambiente
    com_relato, sem_acao = _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    revisao = cliente.get(f"/gestao/secretario/planos/{co}/versoes/1", headers=cliente.headers_secretaria).json()
    assert {b["codigo"] for b in revisao["barreiras"]} >= {com_relato, sem_acao}
    [item] = revisao["versao"]["itens"]

    corpo = {
        "decisao": "ajustes", "comentario": "Revise os pontos marcados no plano.",
        "apontamentos": [
            {"codigo": item["codigo"], "itemId": item["id"], "texto": "Indique o prazo em meses."},
            {"codigo": sem_acao, "texto": "Falta ação para esta barreira."},
        ],
    }
    decidido = cliente.post(f"/gestao/secretario/planos/{co}/versoes/1/decisao", json=corpo, headers=cliente.headers_secretaria).json()
    assert len(decidido["versao"]["apontamentos"]) == 2

    plano = _plano(cliente, diretora).json()
    por_codigo = {a["codigo"]: a for a in plano["apontamentos"]}
    assert por_codigo[com_relato]["acaoId"] == plano["acoes"][0]["id"] and "prazo" in por_codigo[com_relato]["texto"]
    assert por_codigo[sem_acao]["acaoId"] is None

    # Na nova versão os apontamentos saem da tela do diretor (ficam na versão anterior).
    _enviar(cliente, diretora, acao="Organizar com a secretaria, em até 3 meses, a contratação do profissional de AEE.")
    assert _plano(cliente, diretora).json()["apontamentos"] == []


def test_apontamento_invalido_ou_com_dado_sensivel_e_recusado(ambiente):
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    url = f"/gestao/secretario/planos/{co}/versoes/1/decisao"
    base = {"decisao": "ajustes", "comentario": "Revise os pontos marcados no plano."}
    sec = cliente.headers_secretaria

    assert cliente.post(url, json={**base, "apontamentos": [{"codigo": "B-X-99"}]}, headers=sec).status_code == 404
    assert cliente.post(url, json={**base, "apontamentos": [{"codigo": "B-I-01", "itemId": "nao-existe"}]}, headers=sec).status_code == 404
    assert cliente.post(url, json={"decisao": "aceitar", "apontamentos": [{"codigo": "B-I-01"}]}, headers=sec).status_code == 422
    sensivel = [{"codigo": "B-I-01", "texto": "O aluno Pedro toma Ritalina."}]
    assert cliente.post(url, json={**base, "apontamentos": sensivel}, headers=sec).status_code == 422
    # Nada foi gravado: a versão segue em análise.
    assert _plano(cliente, diretora).json()["versoes"][0]["estado"] == "aguardando_analise"

    # Item de outra escola não pode ser apontado nesta versão.
    _emitir(cliente, outra)
    _enviar(cliente, outra)
    co_outra = _co_entidade(cliente, outra)
    item_outra = cliente.get(f"/gestao/secretario/planos/{co_outra}/versoes/1", headers=sec).json()["versao"]["itens"][0]
    resposta = cliente.post(url, json={**base, "apontamentos": [{"codigo": item_outra["codigo"], "itemId": item_outra["id"]}]}, headers=sec)
    assert resposta.status_code == 404


# --- Publicação do plano aceito (decisões de 2026-10-26) ------------------------------------------

def _publicar_declaracao(cliente, auth):
    versao = cliente.get("/gestao/diretor/declaracao", headers=auth).json()["versoes"][-1]["versao"]
    return cliente.post(f"/gestao/diretor/declaracao/versoes/{versao}/publicar", json={"aprovado": True}, headers=auth)


def _publico(cliente, co):
    from app.features.declaracao.router_publico import limpar_cache

    limpar_cache()
    return cliente.get(f"/escolas/{co}/declaracao-publica").json()


def test_plano_aceito_publicado_pelo_diretor_aparece_com_a_declaracao(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _enviar(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    url = "/gestao/diretor/plano/versoes/1"

    # Em análise: não publica.
    assert cliente.post(f"{url}/publicar", json={"aprovado": True}, headers=diretora).status_code == 409
    _decidir(cliente, co, 1, "aceitar")

    # Aceito, mas sem Declaração publicada: não publica (só aparece junto com ela).
    previa = cliente.get(f"{url}/publica", headers=diretora).json()
    assert not previa["podePublicar"] and "Declaração" in previa["motivo"]
    assert _publicar_declaracao(cliente, diretora).status_code == 200

    previa = cliente.get(f"{url}/publica", headers=diretora).json()
    assert previa["podePublicar"] and previa["itens"][0]["acao"] == ACAO
    assert cliente.post(f"{url}/publicar", json={"aprovado": False}, headers=diretora).status_code == 422
    assert cliente.post(f"{url}/publicar", json={"aprovado": True}, headers=diretora).status_code == 200

    publico = _publico(cliente, co)
    assert publico["plano"]["versao"] == 1 and publico["plano"]["itens"][0]["acao"] == ACAO
    assert "submetidaPor" not in str(publico) and "decididaPor" not in str(publico)
    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()["plano"]
    assert painel["versaoAceita"] == 1 and painel["versaoPublicada"] == 1

    # Retirar o plano tira só o plano; a Declaração continua pública.
    cliente.post(f"{url}/retirar", json={"motivo": "decisao_da_escola"}, headers=diretora)
    publico = _publico(cliente, co)
    assert publico is not None and publico["plano"] is None


def test_publicacao_avisa_profissional_de_atendimento(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    codigo = _plano(cliente, diretora).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": codigo, "acao": ACAO, "horizonte": "LOA", "responsavel": "professora do AEE"}, headers=diretora)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "aceitar")
    _publicar_declaracao(cliente, diretora)
    previa = cliente.get("/gestao/diretor/plano/versoes/1/publica", headers=diretora).json()
    assert any("uma só pessoa" in p["mensagem"] and not p["bloqueia"] for p in previa["pontos"])


def _aceito_e_publicavel(cliente, diretora, acao=ACAO, responsavel=None):
    _emitir(cliente, diretora)
    codigo = _plano(cliente, diretora).json()["barreiras"][0]["codigo"]
    corpo = {"codigo": codigo, "acao": acao, "horizonte": "LOA", **({"responsavel": responsavel} if responsavel else {})}
    assert cliente.post("/gestao/diretor/plano/acoes", json=corpo, headers=diretora).status_code == 201
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "aceitar")
    _publicar_declaracao(cliente, diretora)
    return co


def _entrar_admin(cliente, monkeypatch):
    from app.shared import email as envio
    from tests.test_declaracao import _entrar

    codigos = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))
    return _entrar(cliente, codigos, "admin@teste.gov.br", pedir=True)


def test_publicar_limpa_o_cache_e_nao_expoe_premissas_nem_autoria(ambiente):
    cliente, diretora, _ = ambiente
    co = _aceito_e_publicavel(cliente, diretora)
    assert cliente.get(f"/escolas/{co}/declaracao-publica").json()["plano"] is None  # entra no cache
    cliente.post("/gestao/diretor/plano/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    publico = cliente.get(f"/escolas/{co}/declaracao-publica").json()  # sem limpar o cache à mão
    assert publico["plano"]["versao"] == 1
    texto = str(publico)
    assert "premissas" not in texto and "publicadaPor" not in texto and "Sec Niterói" not in texto


def test_versao_retirada_nao_volta_ao_ar(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    co = _aceito_e_publicavel(cliente, diretora)
    cliente.post("/gestao/diretor/plano/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    admin = _entrar_admin(cliente, monkeypatch)
    assert cliente.post(f"/gestao/admin/planos/{co}/versoes/1/retirar", json={"motivo": "pedido_de_titular"}, headers=admin).status_code == 204
    assert cliente.get(f"/escolas/{co}/declaracao-publica").json()["plano"] is None
    previa = cliente.get("/gestao/diretor/plano/versoes/1/publica", headers=diretora).json()
    assert not previa["podePublicar"] and "retirada" in previa["motivo"]
    assert cliente.post("/gestao/diretor/plano/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 409
    assert cliente.post(f"/gestao/admin/planos/{co}/versoes/1/retirar", json={"motivo": "pedido_de_titular"}, headers=diretora).status_code == 403


def test_declaracao_retirada_por_titular_leva_o_plano_junto(ambiente):
    from sqlalchemy import select

    from app.features.plano.modelos import ItemVersaoPlano
    from app.shared import banco_gestao

    cliente, diretora, _ = ambiente
    co = _aceito_e_publicavel(cliente, diretora)
    cliente.post("/gestao/diretor/plano/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post("/gestao/diretor/declaracao/versoes/1/retirar", json={"motivo": "dado_pessoal"}, headers=diretora)
    versao = _plano(cliente, diretora).json()["versoes"][0]
    assert versao["retiradaEm"] is not None
    sessao = next(banco_gestao.obter_sessao())
    assert all(i.publico is None for i in sessao.scalars(select(ItemVersaoPlano)))  # texto público apagado
    sessao.close()


def test_celula_pequena_bloqueia_estudante_individual_e_profissional_de_atendimento(ambiente, monkeypatch):
    from app.features.plano import publicacao

    cliente, diretora, _ = ambiente
    monkeypatch.setattr(publicacao, "celula_pequena", lambda escola: True)
    _aceito_e_publicavel(cliente, diretora, acao="Instalar rampa para o estudante cadeirante do 5º ano.", responsavel="intérprete de Libras")
    previa = cliente.get("/gestao/diretor/plano/versoes/1/publica", headers=diretora).json()
    assert not previa["podePublicar"]
    bloqueios = [p["mensagem"] for p in previa["pontos"] if p["bloqueia"]]
    assert any("um estudante" in m for m in bloqueios) and any("profissional de atendimento" in m for m in bloqueios)


def test_secretaria_como_responsavel_nao_gera_aviso(ambiente):
    cliente, diretora, _ = ambiente
    _aceito_e_publicavel(cliente, diretora, responsavel="secretaria municipal de educação")
    previa = cliente.get("/gestao/diretor/plano/versoes/1/publica", headers=diretora).json()
    assert previa["podePublicar"] and previa["pontos"] == []


def test_lista_publica_do_municipio_mostra_publicacoes(ambiente):
    from tests.test_declaracao import NITEROI

    cliente, diretora, _ = ambiente
    url = f"/municipios/{NITEROI}/publicacoes-gestao"
    assert cliente.get(url).json() == {"escolas": []}
    co = _aceito_e_publicavel(cliente, diretora)  # Declaração publicada, plano aceito ainda não publicado
    assert cliente.get(url).json()["escolas"] == [{"coEntidade": co, "declaracaoVersao": 1, "planoVersao": None}]
    cliente.post("/gestao/diretor/plano/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    resposta = cliente.get(url)
    assert resposta.json()["escolas"][0]["planoVersao"] == 1  # o cache foi limpo pela publicação
    assert resposta.headers["cache-control"] == "no-store" and resposta.headers["x-robots-tag"] == "noindex"
    # Declaração retirada: a escola sai da lista, e o plano não conta sem ela.
    cliente.post("/gestao/diretor/declaracao/versoes/1/retirar", json={"motivo": "decisao_da_escola"}, headers=diretora)
    assert cliente.get(url).json() == {"escolas": []}
