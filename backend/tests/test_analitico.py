"""Spec: docs/sdd/fase-2/requirements/secretario/analitico-barreiras.md e business-rules (RN-SAB-01 a 05)."""

from app.shared import ai_client
from tests.test_declaracao import _provedor, ambiente  # noqa: F401 — fixture e auxiliares compartilhados
from tests.test_plano import _emitir, _plano
from tests.test_revisao_planos import _co_entidade

URL = "/gestao/secretario/analitico"


def _sec(cliente):
    return cliente.headers_secretaria


def _enviar_plano(cliente, auth, acao="Pedir à secretaria o profissional de AEE."):
    codigo = _plano(cliente, auth).json()["barreiras"][0]["codigo"]
    cliente.post("/gestao/diretor/plano/acoes", json={"codigo": codigo, "acao": acao, "horizonte": "LOA"}, headers=auth)
    cliente.post("/gestao/diretor/plano/submeter", json={"confirmado": True}, headers=auth)
    return codigo


def test_numeros_da_rede_cruzam_censo_declaracoes_e_planos(ambiente):
    cliente, diretora, outra = ambiente
    vazio = cliente.get(URL, headers=_sec(cliente)).json()
    assert vazio["comDeclaracao"] == vazio["comPlano"] == 0 and vazio["sintese"] is None
    alunos = [b["alunos"] for b in vazio["barreiras"]]
    assert alunos == sorted(alunos, reverse=True), "ordem por alunos atingidos (decisão de 2026-10-27)"

    codigo, _ = _emitir(cliente, diretora)
    _emitir(cliente, outra)
    _enviar_plano(cliente, diretora)

    dados = cliente.get(URL, headers=_sec(cliente)).json()
    assert (dados["comDeclaracao"], dados["comPlano"]) == (2, 1)
    barreira = next(b for b in dados["barreiras"] if b["codigo"] == codigo)
    assert barreira["obstaculos"] >= 1 and barreira["comAcao"] == 1 and barreira["comAcaoAceita"] == 0
    evidencia = next(e for e in barreira["evidencias"] if e["coEntidade"] == _co_entidade(cliente, diretora))
    assert evidencia["posicao"] == "obstaculo" and evidencia["acoes"] and evidencia["planoEstado"] == "aguardando_analise"
    # Rascunho não entra: barreira sem posição emitida nem ação não gera evidência (RN-SAB-04 / SAB-RF-01).
    assert all(e["posicao"] is not None or e["acoes"] for b in dados["barreiras"] for e in b["evidencias"])


def test_so_o_secretario_ve(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.get(URL, headers=diretora).status_code == 403
    assert cliente.post(f"{URL}/sintese", headers=diretora).status_code == 403


def test_sintese_cita_relatos_sem_levar_escola_nem_municipio_a_ia(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    codigo, _ = _emitir(cliente, diretora)
    _emitir(cliente, outra)

    recebidos = []
    resposta = {
        "achados": [
            {"tipo": "observacao", "texto": "As escolas relatam pedidos sem resposta [R1].", "barreiras": [codigo], "relatos": ["R1"]},
            {"tipo": "hipotese", "texto": "A barreira pode depender de contratação da rede.", "barreiras": [codigo], "relatos": []},
        ],
        "limitacoes": ["Poucas Declarações emitidas."],
    }
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], recebidos))])
    dados = cliente.post(f"{URL}/sintese", headers=_sec(cliente)).json()

    sintese = dados["sintese"]
    assert sintese["modelo"] == "teste" and sintese["desatualizada"] is False
    [observacao, hipotese] = sintese["achados"]
    assert "[R1]" not in observacao["texto"] and observacao["evidencias"][0]["codigo"] == codigo
    assert observacao["evidencias"][0]["escola"] and hipotese["tipo"] == "hipotese"

    enviado = str(recebidos[0])
    assert "[R1]" in enviado
    nomes = {e["escola"] for b in dados["barreiras"] for e in b["evidencias"]}
    for proibido in (*nomes, str(_co_entidade(cliente, diretora)), "Niterói", "NITERÓI"):
        assert proibido not in enviado, proibido

    # Nova emissão depois da síntese: a tela avisa que há registros novos.
    _emitir(cliente, diretora, texto="Pedimos de novo à secretaria e seguimos sem resposta.")
    assert cliente.get(URL, headers=_sec(cliente)).json()["sintese"]["desatualizada"] is True


def test_referencia_inventada_passa_ao_proximo_provedor(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo, _ = _emitir(cliente, diretora)
    inventada = {"achados": [{"tipo": "observacao", "texto": "x", "barreiras": ["B-IX-99"], "relatos": ["R9"]}]}
    valida = {"achados": [{"tipo": "observacao", "texto": "Relato de obstáculo.", "barreiras": [codigo], "relatos": ["R1"]}]}
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("inventa", _provedor([inventada], [])), ("certo", _provedor([valida], []))])
    dados = cliente.post(f"{URL}/sintese", headers=_sec(cliente)).json()
    assert dados["sintese"]["modelo"] == "certo"


def test_ia_nao_recebe_contagens_exatas(ambiente):
    """Revisão do AgLGPD: contagens exatas identificam o município e, numa barreira de uma escola só,
    os alunos dela. À IA vão só proporções arredondadas e "poucas escolas"."""
    import re

    from app.features.acesso import censo
    from app.features.analitico import base as base_rede
    from app.features.analitico import sintese
    from app.shared import banco_gestao

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    sessao = next(banco_gestao.obter_sessao())
    co_municipio = censo.escola(_co_entidade(cliente, diretora)).co_municipio
    texto = sintese.renderizar_rede(base_rede.montar(sessao, co_municipio))
    sessao.close()
    sem_codigos = re.sub(r"cerca de \d+%|B-[IV]+-\d{2}", "", texto)
    assert not re.search(r"\d", sem_codigos), sem_codigos


def test_declaracao_retirada_por_lgpd_nao_vai_a_ia(ambiente, monkeypatch):
    from app.features.declaracao.modelos import Declaracao
    from app.shared import banco_gestao

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora, texto="Relato que a administração retirou por conter dado pessoal.")
    sessao = next(banco_gestao.obter_sessao())
    for declaracao in sessao.query(Declaracao).all():
        declaracao.retirada_motivo = "dado_pessoal"
    sessao.commit()
    sessao.close()

    recebidos = []
    resposta = {"achados": [{"tipo": "observacao", "texto": "Sem relatos disponíveis.", "barreiras": [], "relatos": []}]}
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], recebidos))])
    dados = cliente.post(f"{URL}/sintese", headers=_sec(cliente)).json()
    enviado = str(recebidos[0])
    assert "Pedido sem resposta" not in enviado and "[R1] B-" not in enviado
    assert dados["sintese"]["relatosFora"] >= 1


def test_sem_registro_novo_reaproveita_a_sintese(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    codigo, _ = _emitir(cliente, diretora)
    resposta = {"achados": [{"tipo": "observacao", "texto": "Relato de obstáculo.", "barreiras": [codigo], "relatos": ["R1"]}]}
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], recebidos))])
    primeira = cliente.post(f"{URL}/sintese", headers=_sec(cliente)).json()["sintese"]
    segunda = cliente.post(f"{URL}/sintese", headers=_sec(cliente)).json()["sintese"]
    assert len(recebidos) == 1 and primeira["geradaEm"] == segunda["geradaEm"]


def test_contexto_bloqueado_na_juncao_responde_409(ambiente, monkeypatch):
    from app.features.analitico import sintese
    from app.shared.guardiao_lgpd import TextoBloqueado

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)

    def bloquear(*_args, **_kwargs):
        raise TextoBloqueado("risco alto")

    monkeypatch.setattr(sintese, "juntar_protegidos", bloquear)
    assert cliente.post(f"{URL}/sintese", headers=_sec(cliente)).status_code == 409


def test_sem_ia_os_numeros_continuam(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)

    async def fora_do_ar(*_args):
        raise RuntimeError("provedor fora")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("fora", fora_do_ar)])
    assert cliente.post(f"{URL}/sintese", headers=_sec(cliente)).status_code == 503
    assert cliente.get(URL, headers=_sec(cliente)).json()["comDeclaracao"] == 1
