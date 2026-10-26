"""Spec: docs/sdd/fase-2/requirements/acesso-gestao-ativa.md e business-rules/acesso-gestao-ativa.md.

Banco temporário criado pelas migrações Alembic; o e-mail é substituído por uma captura do código.
"""

import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.features.acesso import servico
from app.features.acesso.modelos import CodigoUsoUnico, Conta, EventoAuditoria, Vinculo
from app.features.login.security import criar_token as criar_token_fase1
from app.main import app
from app.shared import banco_gestao
from app.shared import email as envio

NITEROI, RIO = 3303302, 3304557
ESCOLA_NITEROI, OUTRA_ESCOLA_NITEROI = 33055238, 33056323
ESCOLA_ESTADUAL_NITEROI = 33055300
ESCOLA_RIO = 33062358


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    banco_gestao.configurar(f"sqlite:///{(tmp_path / 'gestao.db').as_posix()}")
    banco_gestao.migrar()
    codigos: dict[str, str] = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))

    sessao = next(banco_gestao.obter_sessao())
    admin = servico.criar_admin(sessao, nome="Admin Teste", email="admin@teste.gov.br")
    for nome, email, municipio in (("Sec Niterói", "sec@niteroi.gov.br", NITEROI), ("Sec Rio", "sec@rio.gov.br", RIO)):
        servico.provisionar_secretario(sessao, admin=admin, nome=nome, email=email, co_municipio=municipio, categoria="oficio", metodo="Ofício da secretaria, teste")
    sessao.close()

    cliente = TestClient(app)
    yield cliente, codigos
    banco_gestao.configurar()


def _entrar(cliente, codigos, email):
    cliente.post("/gestao/acesso/codigo", json={"email": email})
    return cliente.post("/gestao/acesso/entrar", json={"email": email, "codigo": codigos[email]}).json()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _sessao_secretario(cliente, codigos, email="sec@niteroi.gov.br"):
    resposta = cliente.post("/gestao/acesso/entrar", json={"email": email, "codigo": codigos[email]}).json()
    assert resposta["situacao"] == "ativo"
    return _auth(resposta["token"])


def _solicitar(cliente, email="diretora@escola.gov.br", escola=ESCOLA_NITEROI):
    return cliente.post("/gestao/acesso/diretor", json={"nome": "Diretora Teste", "email": email, "coEntidade": escola})


def _pendente_id(cliente, auth):
    [pedido] = cliente.get("/gestao/secretario/vinculos", headers=auth).json()
    return pedido["id"]


# --- Solicitação e código ----------------------------------------------------------------------

def test_solicitacao_nasce_pendente_e_nao_da_acesso(ambiente):
    cliente, codigos = ambiente
    assert _solicitar(cliente).status_code == 202
    resposta = cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]}).json()
    assert resposta["situacao"] == "aguardando_aprovacao"
    assert resposta["token"] is None
    assert cliente.get("/gestao/diretor/escola").status_code == 401


def test_escola_fora_do_piloto_ou_inexistente(ambiente):
    cliente, _ = ambiente
    assert _solicitar(cliente, escola=ESCOLA_ESTADUAL_NITEROI).status_code == 422
    assert _solicitar(cliente, escola=99999999).status_code == 404


def test_resposta_uniforme_para_email_desconhecido(ambiente):
    cliente, codigos = ambiente
    resposta = cliente.post("/gestao/acesso/codigo", json={"email": "ninguem@exemplo.gov.br"})
    assert resposta.status_code == 202
    assert "ninguem@exemplo.gov.br" not in codigos
    entrada = cliente.post("/gestao/acesso/entrar", json={"email": "ninguem@exemplo.gov.br", "codigo": "123456"})
    assert entrada.status_code == 400


def test_codigo_vale_uma_vez(ambiente):
    cliente, codigos = ambiente
    corpo = {"email": "sec@niteroi.gov.br", "codigo": codigos["sec@niteroi.gov.br"]}
    assert cliente.post("/gestao/acesso/entrar", json=corpo).status_code == 200
    assert cliente.post("/gestao/acesso/entrar", json=corpo).status_code == 400


def test_codigo_bloqueia_apos_tentativas_erradas(ambiente):
    cliente, codigos = ambiente
    certo = codigos["sec@niteroi.gov.br"]
    errado = f"{(int(certo) + 1) % 1_000_000:06d}"
    for _ in range(5):
        cliente.post("/gestao/acesso/entrar", json={"email": "sec@niteroi.gov.br", "codigo": errado})
    assert cliente.post("/gestao/acesso/entrar", json={"email": "sec@niteroi.gov.br", "codigo": certo}).status_code == 400


def test_codigo_expirado_nao_vale(ambiente):
    cliente, codigos = ambiente
    sessao = next(banco_gestao.obter_sessao())
    registro = sessao.scalar(select(CodigoUsoUnico).where(CodigoUsoUnico.email == "sec@niteroi.gov.br"))
    registro.expira_em = registro.expira_em - timedelta(minutes=11)
    sessao.commit()
    sessao.close()
    assert cliente.post("/gestao/acesso/entrar", json={"email": "sec@niteroi.gov.br", "codigo": codigos["sec@niteroi.gov.br"]}).status_code == 400


def test_reenvio_respeita_intervalo(ambiente):
    cliente, codigos = ambiente
    primeiro = codigos["sec@niteroi.gov.br"]
    cliente.post("/gestao/acesso/codigo", json={"email": "sec@niteroi.gov.br"})
    assert codigos["sec@niteroi.gov.br"] == primeiro  # dentro de 60 s não gera outro


# --- Aprovação pelo secretário -----------------------------------------------------------------

def test_fluxo_completo_ate_o_dashboard(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    secretario = _sessao_secretario(cliente, codigos)

    pedido_id = _pendente_id(cliente, secretario)
    sem_metodo = cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": ""}, headers=secretario)
    assert sem_metodo.status_code == 422
    aprovado = cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": "Portaria de designação 12/2026"}, headers=secretario)
    assert aprovado.status_code == 200

    cliente.app.dependency_overrides.clear()
    entrada = _entrar(cliente, codigos, "diretora@escola.gov.br")
    assert entrada["situacao"] == "ativo"
    diretora = _auth(entrada["token"])

    eu = cliente.get("/gestao/eu", headers=diretora).json()
    assert eu["papel"] == "diretor" and eu["escopo"]["coEntidade"] == ESCOLA_NITEROI

    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()
    assert painel["coEntidade"] == ESCOLA_NITEROI and painel["municipio"].startswith("Niter")
    assert len(painel["eixos"]) == 4
    assert all(b["posicao"] == "sem_posicao" for b in painel["barreiras"])
    assert painel["declaracao"].items() >= {"estado": "rascunho", "versao": None, "comPosicao": 0, "total": len(painel["barreiras"])}.items()


def _id_do_pedido(email):
    sessao = next(banco_gestao.obter_sessao())
    vinculo = sessao.scalar(select(Vinculo).join(Conta, Vinculo.conta_id == Conta.id).where(Conta.email == email).order_by(Vinculo.criado_em.desc()))
    sessao.close()
    return vinculo.id


def test_pedido_nao_confirmado_nao_aparece_nem_e_aprovado(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)  # código enviado, mas não usado
    secretario = _sessao_secretario(cliente, codigos)
    assert cliente.get("/gestao/secretario/vinculos", headers=secretario).json() == []
    resposta = cliente.post(
        f"/gestao/secretario/vinculos/{_id_do_pedido('diretora@escola.gov.br')}/aprovar",
        json={"categoria": "oficio", "texto": "Portaria 12/2026"}, headers=secretario,
    )
    assert resposta.status_code == 409


def test_pedido_com_email_de_outra_pessoa_nao_vale(ambiente):
    """Revisão do AgLGPD, I3: a confirmação antiga da conta não confirma um pedido novo."""
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    secretario = _sessao_secretario(cliente, codigos)
    pedido = _pendente_id(cliente, secretario)
    cliente.post(f"/gestao/secretario/vinculos/{pedido}/rejeitar", json={"categoria": "nao_consta", "texto": "Não consta como diretora"}, headers=secretario)

    # Outra pessoa pede vínculo com o e-mail dela para outra escola; ela só entra com código comum.
    _envelhecer_codigos("diretora@escola.gov.br")
    _solicitar(cliente, escola=OUTRA_ESCOLA_NITEROI)
    _envelhecer_codigos("diretora@escola.gov.br")
    _entrar(cliente, codigos, "diretora@escola.gov.br")
    assert cliente.get("/gestao/secretario/vinculos", headers=secretario).json() == []


def test_secretario_de_outra_rede_nao_ve_nem_decide(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    niteroi = _sessao_secretario(cliente, codigos)
    pedido_id = _pendente_id(cliente, niteroi)

    rio = _sessao_secretario(cliente, codigos, "sec@rio.gov.br")
    assert cliente.get("/gestao/secretario/vinculos", headers=rio).json() == []
    resposta = cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": "Portaria 12/2026"}, headers=rio)
    assert resposta.status_code == 404


def test_suspensao_e_revogacao_valem_na_hora(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    secretario = _sessao_secretario(cliente, codigos)
    pedido_id = _pendente_id(cliente, secretario)
    cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": "Portaria 12/2026"}, headers=secretario)
    diretora = _auth(_entrar(cliente, codigos, "diretora@escola.gov.br")["token"])
    assert cliente.get("/gestao/diretor/escola", headers=diretora).status_code == 200

    cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/suspender", json={"categoria": "outro", "texto": "Afastamento informado pela rede"}, headers=secretario)
    assert cliente.get("/gestao/diretor/escola", headers=diretora).status_code == 403  # mesmo token

    cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/reativar", json={"categoria": "outro", "texto": "Retorno às funções"}, headers=secretario)
    assert cliente.get("/gestao/diretor/escola", headers=diretora).status_code == 200

    cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/revogar", json={"categoria": "outro", "texto": "Mudou de escola"}, headers=secretario)
    assert cliente.get("/gestao/diretor/escola", headers=diretora).status_code == 403

    # Nova escola exige nova solicitação e nova aprovação (RN-05, RN-12).
    assert _solicitar(cliente, escola=OUTRA_ESCOLA_NITEROI).status_code == 202
    assert cliente.get("/gestao/diretor/escola", headers=diretora).status_code == 403


def test_rejeicao_informa_o_que_fazer(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    secretario = _sessao_secretario(cliente, codigos)
    cliente.post(f"/gestao/secretario/vinculos/{_pendente_id(cliente, secretario)}/rejeitar", json={"categoria": "outro", "texto": "Não consta como diretora"}, headers=secretario)
    resposta = _entrar(cliente, codigos, "diretora@escola.gov.br")
    assert resposta["situacao"] == "rejeitado" and resposta["token"] is None
    assert "solicite de novo" in resposta["mensagem"]


# --- Autorização ---------------------------------------------------------------------------------

def test_perfis_nao_cruzam_rotas(ambiente):
    cliente, codigos = ambiente
    secretario = _sessao_secretario(cliente, codigos)
    assert cliente.get("/gestao/diretor/escola", headers=secretario).status_code == 403
    admin = _auth(_entrar(cliente, codigos, "admin@teste.gov.br")["token"])
    assert cliente.get("/gestao/secretario/vinculos", headers=admin).status_code == 403


def test_token_da_fase_1_nao_vale(ambiente):
    cliente, _ = ambiente
    token = criar_token_fase1(usuario_id="u-joao-niteroi", nome="João", perfil="municipal", municipio_id=NITEROI, uf="RJ")
    assert cliente.get("/gestao/eu", headers=_auth(token)).status_code == 401


def test_admin_provisiona_secretario(ambiente):
    cliente, codigos = ambiente
    admin = _auth(_entrar(cliente, codigos, "admin@teste.gov.br")["token"])
    corpo = {"nome": "Sec Nova", "email": "sec@nova.gov.br", "coMunicipio": 3550308, "categoria": "telefone_institucional", "metodoVerificacao": "Contato pelo telefone oficial"}
    assert cliente.post("/gestao/admin/secretarios", json=corpo, headers=admin).status_code == 201
    assert _entrar(cliente, codigos, "sec@nova.gov.br")["situacao"] == "ativo"
    secretario = _sessao_secretario(cliente, codigos)
    assert cliente.post("/gestao/admin/secretarios", json=corpo, headers=secretario).status_code == 403


def test_auditoria_registra_sem_codigo(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    sessao = next(banco_gestao.obter_sessao())
    eventos = sessao.scalars(select(EventoAuditoria)).all()
    sessao.close()
    acoes = {e.acao for e in eventos}
    assert {"admin_criado", "secretario_provisionado", "conta_criada", "vinculo_solicitado", "canal_confirmado", "entrada"} <= acoes
    for evento in eventos:
        assert not re.search(r"\b\d{6}\b", evento.detalhe or "")


def _envelhecer_codigos(email, horas=0, minutos=2):
    """Simula a passagem do tempo para os limites de reenvio e de quantidade."""
    sessao = next(banco_gestao.obter_sessao())
    for registro in sessao.scalars(select(CodigoUsoUnico).where(CodigoUsoUnico.email == email)):
        registro.criado_em = registro.criado_em - timedelta(hours=horas, minutes=minutos)
    sessao.commit()
    sessao.close()


# --- Correções da revisão do AgLGPD (2026-10-23) ------------------------------------------------

def test_justificativa_com_dado_de_saude_e_recusada_e_auditoria_guarda_so_categoria(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})
    secretario = _sessao_secretario(cliente, codigos)
    pedido = _pendente_id(cliente, secretario)
    cliente.post(f"/gestao/secretario/vinculos/{pedido}/aprovar", json={"categoria": "oficio", "texto": "Portaria 12/2026 conferida"}, headers=secretario)

    sensivel = cliente.post(
        f"/gestao/secretario/vinculos/{pedido}/suspender",
        json={"categoria": "afastamento", "texto": "A diretora está internada no hospital"}, headers=secretario,
    )
    assert sensivel.status_code == 422
    assert cliente.post(f"/gestao/secretario/vinculos/{pedido}/suspender", json={"categoria": "inventada", "texto": "Afastamento"}, headers=secretario).status_code == 422

    com_nome = cliente.post(
        f"/gestao/secretario/vinculos/{pedido}/suspender",
        json={"categoria": "afastamento", "texto": "Afastamento informado pela coordenadora Maria José"}, headers=secretario,
    )
    assert com_nome.status_code == 200
    sessao = next(banco_gestao.obter_sessao())
    vinculo = sessao.get(Vinculo, pedido)
    eventos = sessao.scalars(select(EventoAuditoria).where(EventoAuditoria.alvo_id == pedido)).all()
    sessao.close()
    assert "Maria" not in vinculo.justificativa and "[NOME]" in vinculo.justificativa
    assert {e.detalhe for e in eventos if e.acao.startswith("vinculo_")} <= {"oficio", "afastamento", "escola 33055238"}


def test_limite_diario_de_codigos(ambiente):
    cliente, codigos = ambiente
    enviados = set()
    for _ in range(12):
        _envelhecer_codigos("sec@niteroi.gov.br", horas=1, minutos=1)  # fora da janela por hora, dentro do dia
        cliente.post("/gestao/acesso/codigo", json={"email": "sec@niteroi.gov.br"})
        enviados.add(codigos["sec@niteroi.gov.br"])
    sessao = next(banco_gestao.obter_sessao())
    total = sessao.query(CodigoUsoUnico).filter(CodigoUsoUnico.email == "sec@niteroi.gov.br").count()
    sessao.close()
    assert total == 10


def test_erros_do_dia_bloqueiam_a_entrada(ambiente):
    cliente, codigos = ambiente
    for _ in range(4):  # 4 códigos × 5 erros = 20 erros no dia
        certo = codigos["sec@niteroi.gov.br"]
        errado = f"{(int(certo) + 1) % 1_000_000:06d}"
        for _ in range(5):
            cliente.post("/gestao/acesso/entrar", json={"email": "sec@niteroi.gov.br", "codigo": errado})
        _envelhecer_codigos("sec@niteroi.gov.br")
        cliente.post("/gestao/acesso/codigo", json={"email": "sec@niteroi.gov.br"})
    ultimo = codigos["sec@niteroi.gov.br"]
    assert cliente.post("/gestao/acesso/entrar", json={"email": "sec@niteroi.gov.br", "codigo": ultimo}).status_code == 400


def test_limite_por_ip(ambiente):
    cliente, _ = ambiente
    respostas = [cliente.post("/gestao/acesso/codigo", json={"email": f"x{i}@exemplo.gov.br"}).status_code for i in range(31)]
    assert respostas[:30] == [202] * 30 and respostas[30] == 429


@pytest.mark.parametrize(
    "variaveis",
    [
        {"AMBIENTE": None, "EMAIL_MODO": "console"},  # console fora de dev
        {"AMBIENTE": None, "EMAIL_MODO": "provedor", "GESTAO_SEGREDO_TOKEN": None},  # sem segredo
        {"AMBIENTE": None, "EMAIL_MODO": "provedor", "GESTAO_SEGREDO_TOKEN": "curto", "GESTAO_SEGREDO_CODIGO": "x" * 40},
    ],
)
def test_configuracao_de_producao_incompleta_falha_fechado(ambiente, monkeypatch, variaveis):
    cliente, _ = ambiente
    for nome, valor in variaveis.items():
        if valor is None:
            monkeypatch.delenv(nome, raising=False)
        else:
            monkeypatch.setenv(nome, valor)
    assert cliente.post("/gestao/acesso/codigo", json={"email": "sec@niteroi.gov.br"}).status_code == 503
    assert cliente.get("/gestao/eu").status_code == 503
    assert cliente.get("/health").status_code == 200  # o site público segue no ar


def test_email_no_console_so_em_desenvolvimento(monkeypatch):
    monkeypatch.delenv("AMBIENTE", raising=False)
    with pytest.raises(envio.EnvioIndisponivel):
        envio.enviar_codigo("a@b.gov.br", "123456")


def test_demo_so_em_desenvolvimento(monkeypatch):
    from app.features.acesso import cli

    monkeypatch.delenv("AMBIENTE", raising=False)
    with pytest.raises(SystemExit, match="AMBIENTE=dev"):
        cli.demo()


def test_limpeza_apaga_pedido_nunca_confirmado(ambiente):
    cliente, codigos = ambiente
    _solicitar(cliente, email="fantasma@exemplo.gov.br")
    sessao = next(banco_gestao.obter_sessao())
    for modelo in (Conta, Vinculo):
        for registro in sessao.scalars(select(modelo)):
            registro.criado_em = registro.criado_em - timedelta(hours=73)
    sessao.commit()
    _envelhecer_codigos("fantasma@exemplo.gov.br", horas=25)
    removidos = servico.limpar(sessao)
    restantes = sessao.scalar(select(Conta).where(Conta.email == "fantasma@exemplo.gov.br"))
    secretaria = sessao.scalar(select(Conta).where(Conta.email == "sec@niteroi.gov.br"))
    sessao.close()
    assert removidos["pedidos_nao_confirmados"] == 1 and removidos["contas_nao_confirmadas"] == 1
    assert restantes is None and secretaria is not None


# --- Caixa de e-mails de teste -------------------------------------------------------------------

def test_caixa_de_teste_mostra_codigo_so_em_dev_e_so_localmente(tmp_path, monkeypatch):
    from app.shared import email as modulo_email

    banco_gestao.configurar(f"sqlite:///{(tmp_path / 'gestao.db').as_posix()}")
    banco_gestao.migrar()
    sessao = next(banco_gestao.obter_sessao())
    servico.criar_admin(sessao, nome="Admin Teste", email="admin@teste.gov.br")
    sessao.close()
    local = TestClient(app, client=("127.0.0.1", 50000))
    remoto = TestClient(app, client=("10.0.0.7", 50000))

    local.post("/gestao/acesso/codigo", json={"email": "admin@teste.gov.br"})
    [mensagem] = [m for m in local.get("/gestao/dev/emails").json() if m["para"] == "admin@teste.gov.br"]
    assert re.fullmatch(r"\d{6}", mensagem["codigo"])
    assert local.post("/gestao/acesso/entrar", json={"email": "admin@teste.gov.br", "codigo": mensagem["codigo"]}).json()["situacao"] == "ativo"

    assert remoto.get("/gestao/dev/emails").status_code == 404
    monkeypatch.delenv("AMBIENTE")
    assert local.get("/gestao/dev/emails").status_code == 404
    assert modulo_email.caixa_de_teste() == []
    banco_gestao.configurar()
