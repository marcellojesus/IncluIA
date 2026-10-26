"""Spec: docs/sdd/fase-2/requirements/secretario/plano-estrategico-municipal.md e business-rules (RN-SPM-01 a 06)."""

from app.shared import ai_client
from tests.test_declaracao import _provedor, ambiente  # noqa: F401 — fixture e auxiliares compartilhados
from tests.test_plano import _emitir, _plano
from tests.test_revisao_planos import _co_entidade, _decidir

URL = "/gestao/secretario/plano-municipal"


def _plano_aceito(cliente, auth, acao):
    codigo = _plano(cliente, auth).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": codigo, "acao": acao, "horizonte": "LOA"}, headers=auth)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=auth)
    _decidir(cliente, _co_entidade(cliente, auth), 1, "aceitar")
    return codigo


def _resposta(atende, acao="Contratar profissionais de AEE em regime compartilhado entre as escolas da rede.", fontes=None):
    return {
        "acoes": [{
            "acao": acao, "justificativa": f"Atende às ações {', '.join('[' + a['ref'] + ']' for a in atende)} das escolas.",
            "atende": atende, "responsavel": "secretaria municipal de educação", "prazo": "até 12 meses", "horizonte": "PPA",
            "custo_estimado": "a estimar", "premissas": "Dotação no PPA.", "prioridade": "alta", "fontes": fontes or [],
            "incertezas": "Quantidade de profissionais disponíveis.",
        }],
        "lacunas": ["A base normativa entregue não trata de contratação compartilhada."],
    }


def _sec(cliente):
    return cliente.headers_secretaria


def test_base_da_rede_usa_so_planos_aceitos(ambiente):
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _emitir(cliente, outra)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    # A outra escola enviou, mas não foi aceita: fica de fora (decisão de 2026-10-26).
    cod_outra = _plano(cliente, outra).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": cod_outra, "acao": "Pedir à secretaria a sala de recursos.", "horizonte": "LOA"}, headers=outra)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=outra)

    estado = cliente.get(URL, headers=_sec(cliente)).json()
    assert estado["escolasComPlanoAceito"] == 1 and estado["escolasMunicipais"] > 1
    barreira = next(b for b in estado["barreiras"] if b["codigo"] == codigo)
    assert [i["ref"] for i in barreira["itens"]] == ["E1-A1"] and barreira["escolasComBarreira"] >= 1
    assert cliente.get(URL, headers=diretora).status_code == 403


def test_ia_propoe_acao_municipal_e_sistema_conta_as_escolas(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _emitir(cliente, outra)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    cod_outra = _plano_aceito(cliente, outra, "Pedir à secretaria um professor de AEE compartilhado.")
    assert cod_outra == codigo, "as escolas de teste precisam ter a mesma primeira barreira"

    recebidos = []
    resposta = _resposta([{"ref": "E1-A1", "cobertura": "total"}, {"ref": "E2-A1", "cobertura": "parcial"}])
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], recebidos))])
    estado = cliente.post(f"{URL}/barreiras/{codigo}/sugestoes", json={}, headers=_sec(cliente)).json()
    [sugestao] = estado["sugestoes"]
    assert len(sugestao["escolas"]) == 2 and {e["cobertura"] for e in sugestao["escolas"]} == {"total", "parcial"}
    assert "E1-A1" not in sugestao["justificativa"]  # referências saem do texto gravado
    enviado = str(recebidos[0])
    assert "[E1-A1]" in enviado
    # Nenhum nome nem código de escola, nem o município, vai à IA.
    nomes = {i["escola"] for b in cliente.get(URL, headers=_sec(cliente)).json()["barreiras"] for i in b["itens"]}
    for proibido in (*nomes, str(_co_entidade(cliente, diretora)), str(_co_entidade(cliente, outra)), "Niterói", "NITERÓI"):
        assert proibido not in enviado, proibido

    estado = cliente.post(f"{URL}/sugestoes/{sugestao['id']}/aceitar", json={}, headers=_sec(cliente)).json()
    assert estado["escolasAtendidas"] == 2 and estado["acoes"][0]["origem"] == "ia"

    versao = cliente.post(f"{URL}/confirmar", json={"confirmado": True}, headers=_sec(cliente)).json()
    assert versao["versao"] == 1 and versao["escolasAtendidas"] == 2

    # Cada diretor vê só a ação que atende a própria escola, com a própria cobertura (RN-SPM-03).
    da_escola = cliente.get("/gestao/diretor/acoes-municipais", headers=outra).json()
    assert da_escola["versao"] == 1 and da_escola["acoes"][0]["cobertura"] == "parcial" and "escolas" not in da_escola["acoes"][0]


def test_referencia_inventada_passa_ao_proximo_provedor(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    inventada = _resposta([{"ref": "E9-A9", "cobertura": "total"}])
    valida = _resposta([{"ref": "E1-A1", "cobertura": "total"}])
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("inventa", _provedor([inventada], [])), ("certo", _provedor([valida], []))])
    estado = cliente.post(f"{URL}/barreiras/{codigo}/sugestoes", json={}, headers=_sec(cliente)).json()
    assert estado["sugestoes"][0]["escolas"][0]["coEntidade"] == _co_entidade(cliente, diretora)


def test_sem_plano_aceito_nao_chama_a_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    codigo = _plano(cliente, diretora).json()["barreiras"][0]["codigo"]

    async def nao_pode(*_args):
        raise AssertionError("a IA não pode ser chamada")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", nao_pode)])
    resposta = cliente.post(f"{URL}/barreiras/{codigo}/sugestoes", json={}, headers=_sec(cliente))
    assert resposta.status_code == 409


def test_acao_propria_valida_escola_e_item_da_rede(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    co = _co_entidade(cliente, diretora)
    item = cliente.get(URL, headers=_sec(cliente)).json()["barreiras"][0]["itens"][0]
    nova = {"codigos": [codigo], "acao": "Realizar formação da rede sobre AEE.", "horizonte": "LOA", "prioridade": "media",
            "escolas": [{"coEntidade": co, "itemIds": [item["itemId"]], "cobertura": "parcial"}]}
    estado = cliente.post(f"{URL}/acoes", json=nova, headers=_sec(cliente)).json()
    assert estado["acoes"][0]["origem"] == "secretario" and estado["escolasAtendidas"] == 1

    fora = {**nova, "escolas": [{"coEntidade": 99999999, "cobertura": "total"}]}
    assert cliente.post(f"{URL}/acoes", json=fora, headers=_sec(cliente)).status_code == 404
    item_falso = {**nova, "escolas": [{"coEntidade": co, "itemIds": ["nao-existe"], "cobertura": "total"}]}
    assert cliente.post(f"{URL}/acoes", json=item_falso, headers=_sec(cliente)).status_code == 404
    sensivel = {**nova, "acao": "Acompanhar o aluno Pedro, que toma Ritalina."}
    assert cliente.post(f"{URL}/acoes", json=sensivel, headers=_sec(cliente)).status_code == 422
    assert cliente.post(f"{URL}/confirmar", json={"confirmado": False}, headers=_sec(cliente)).status_code == 422


def test_diretor_sem_plano_municipal_confirmado(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.get("/gestao/diretor/acoes-municipais", headers=diretora).json() == {"versao": None, "confirmadaEm": None, "acoes": []}


def test_referencias_saem_do_texto_sem_deixar_frase_quebrada():
    from app.features.plano_municipal.sugestoes import _sem_referencias

    assert _sem_referencias("demandas expressas em [E1-A1] e [E1-A2].") == "demandas expressas nos planos das escolas."
    assert _sem_referencias("Atende às ações [E1-A1], [E2-A1] das escolas.") == "Atende às ações das escolas."
    assert _sem_referencias("Consolida (E1-A1, E2-A3) numa contratação.") == "Consolida numa contratação."
    assert _sem_referencias("Sem referência.") == "Sem referência."


def test_fatos_da_rede_so_tem_contagens():
    from dataclasses import fields

    from app.shared.contexto_ia import FatosDaRede

    assert all(f.type in (int, "int") for f in fields(FatosDaRede))


def test_secretario_de_outro_municipio_nao_alcanca_o_plano(ambiente, monkeypatch):
    from sqlalchemy import select

    from app.features.acesso import servico as acesso
    from app.features.acesso.modelos import Conta
    from app.shared import banco_gestao
    from app.shared import email as envio
    from tests.test_declaracao import _entrar

    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta([{"ref": "E1-A1", "cobertura": "total"}])], []))])
    estado = cliente.post(f"{URL}/barreiras/{codigo}/sugestoes", json={}, headers=_sec(cliente)).json()
    sugestao = estado["sugestoes"][0]["id"]
    nova = {"codigos": [codigo], "acao": "Realizar formação da rede sobre AEE.", "horizonte": "LOA", "prioridade": "media"}
    acao = cliente.post(f"{URL}/acoes", json=nova, headers=_sec(cliente)).json()["acoes"][0]["id"]
    cliente.post(f"{URL}/confirmar", json={"confirmado": True}, headers=_sec(cliente))

    codigos = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))
    sessao = next(banco_gestao.obter_sessao())
    admin = sessao.scalar(select(Conta).where(Conta.papel == "admin"))
    acesso.provisionar_secretario(sessao, admin=admin, nome="Sec Rio", email="sec@rio.gov.br", co_municipio=3304557, categoria="oficio", metodo="Ofício de teste")
    sessao.close()
    rio = _entrar(cliente, codigos, "sec@rio.gov.br")

    assert cliente.get(URL, headers=rio).json()["acoes"] == []
    assert cliente.post(f"{URL}/sugestoes/{sugestao}/aceitar", json={}, headers=rio).status_code == 404
    assert cliente.post(f"{URL}/sugestoes/{sugestao}/descartar", json={}, headers=rio).status_code == 404
    assert cliente.put(f"{URL}/acoes/{acao}", json=nova, headers=rio).status_code == 404
    assert cliente.delete(f"{URL}/acoes/{acao}", headers=rio).status_code == 404
    assert cliente.get(f"{URL}/versoes/1", headers=rio).status_code == 404
    # Escola de Niterói não pode ser apontada por uma ação do Rio.
    com_escola = {**nova, "escolas": [{"coEntidade": _co_entidade(cliente, diretora), "cobertura": "total"}]}
    assert cliente.post(f"{URL}/acoes", json=com_escola, headers=rio).status_code == 404
    # Diretor de escola não atendida pela versão confirmada não vê ações.
    assert cliente.get("/gestao/diretor/acoes-municipais", headers=outra).json()["acoes"] == []
