"""Spec: docs/sdd/fase-2/requirements/documentos-pdf.md e business-rules (RN-PDF-01 a 07)."""

import io
import logging

from pypdf import PdfReader
from sqlalchemy import select

from app.features.acesso.modelos import EventoAuditoria
from app.shared import ai_client, banco_gestao
from app.shared.pdf import Campo, Documento, Secao, codigo_conferencia
from tests.test_declaracao import ESCOLA, ambiente  # noqa: F401 — fixture compartilhada
from tests.test_plano import _emitir, _plano
from tests.test_plano_municipal import _plano_aceito, _sec
from tests.test_revisao_planos import _co_entidade, _decidir

DECL = "/gestao/diretor/declaracao"
PLANO = "/gestao/diretor/plano"
MUNICIPAL = "/gestao/secretario/plano-municipal"


def _texto(resposta) -> str:
    assert resposta.status_code == 200, resposta.text
    assert resposta.headers["content-type"] == "application/pdf"
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.headers["x-content-type-options"] == "nosniff"
    leitor = PdfReader(io.BytesIO(resposta.content))
    return " ".join(" ".join(p.extract_text().split()) for p in leitor.pages)


def _metadados(resposta):
    return PdfReader(io.BytesIO(resposta.content)).metadata


def _codigo(texto: str) -> str:
    return texto.split("Código de conferência ")[1][:14]


def _eventos(acao="pdf_baixado") -> list[EventoAuditoria]:
    sessao = next(banco_gestao.obter_sessao())
    try:
        return list(sessao.scalars(select(EventoAuditoria).where(EventoAuditoria.acao == acao)))
    finally:
        sessao.close()


def _plano_enviado(cliente, auth, acao="Solicitar à secretaria a sala de recursos."):
    codigo = _plano(cliente, auth).json()["barreiras"][0]["codigo"]
    cliente.post(f"{PLANO}/acoes", json={"codigo": codigo, "acao": acao, "horizonte": "LOA", "custo_estimado": "R$ 5 mil"}, headers=auth)
    cliente.post(f"{PLANO}/submeter", json={"confirmado": True}, headers=auth)


def test_declaracao_em_pdf_para_diretor_e_secretario(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    co = _co_entidade(cliente, diretora)

    resposta = cliente.get(f"{DECL}/versoes/1/pdf", headers=diretora)
    texto = _texto(resposta)
    assert f'declaracao-obstaculos_{co}_v1.pdf' in resposta.headers["content-disposition"]
    for esperado in ("Declaração de Obstáculos — versão 1", "Obstáculo relatado", "Sem relato nesta versão", "pediu o recurso à secretaria",
                     "Não publicada", "Uso interno da escola e da secretaria", "Não tem assinatura nem valor jurídico",
                     "não acompanha correções nem retiradas", "Código de conferência", "Página 1 de"):
        assert esperado in texto, esperado
    # Nada além do que a tela mostra (RN-PDF-06; revisão do AgLGPD, M4): sem resumo, autoria nem e-mail.
    for ausente in ("Pedido sem resposta", "Diretora Teste", "diretora@escola.gov.br", "@"):
        assert ausente not in texto, ausente
    metadados = _metadados(resposta)
    assert metadados.title == "Declaração de Obstáculos — versão 1" and metadados.author == "Escola Sem Barreiras"
    assert "Diretora" not in str(dict(metadados))

    # O secretário da rede baixa o mesmo conteúdo, com o mesmo código de conferência (RN-PDF-04).
    do_secretario = _texto(cliente.get(f"/gestao/secretario/declaracoes/{co}/versoes/1/pdf", headers=_sec(cliente)))
    assert _codigo(texto) == _codigo(do_secretario)
    # Cada download entra na auditoria, sem conteúdo (revisão do AgLGPD, M3).
    eventos = _eventos()
    assert len(eventos) == 2 and {e.resultado for e in eventos} == {"ok"} and {e.alvo_tipo for e in eventos} == {"declaracao"}


def test_so_versao_emitida_e_do_proprio_escopo(ambiente):
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    # Rascunho não tem PDF (RN-PDF-01); versão de outra escola não existe para a diretora (RN-PDF-02).
    assert cliente.get(f"{DECL}/versoes/1/pdf", headers=outra).status_code == 404
    assert cliente.get(f"{DECL}/versoes/2/pdf", headers=diretora).status_code == 404
    assert cliente.get(f"/gestao/secretario/declaracoes/{co}/versoes/1/pdf", headers=diretora).status_code == 403
    assert cliente.get(f"/gestao/secretario/planos/{co}/versoes/1/pdf", headers=_sec(cliente)).status_code == 404
    assert cliente.get(f"{MUNICIPAL}/versoes/1/pdf", headers=diretora).status_code == 403
    assert cliente.get(f"{DECL}/versoes/1/pdf").status_code in (401, 403)


def test_secretario_de_outro_municipio_nao_baixa(ambiente, monkeypatch):
    from app.features.acesso import servico as acesso
    from app.features.acesso.modelos import Conta
    from app.shared import email as envio
    from tests.test_declaracao import _entrar

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    cliente.post(f"{MUNICIPAL}/acoes", json={"codigos": ["B-I-01"], "acao": "Formação da rede.", "horizonte": "LOA", "prioridade": "media"},
                 headers=_sec(cliente))
    cliente.post(f"{MUNICIPAL}/confirmar", json={"confirmado": True}, headers=_sec(cliente))
    co = _co_entidade(cliente, diretora)

    codigos = {}
    monkeypatch.setattr(envio, "enviar_codigo", lambda email, codigo, escola=None: codigos.__setitem__(email, codigo))
    sessao = next(banco_gestao.obter_sessao())
    admin = sessao.scalar(select(Conta).where(Conta.papel == "admin"))
    acesso.provisionar_secretario(sessao, admin=admin, nome="Sec Rio", email="sec@rio.gov.br", co_municipio=3304557, categoria="oficio", metodo="Ofício de teste")
    sessao.close()
    rio = _entrar(cliente, codigos, "sec@rio.gov.br")

    assert cliente.get(f"{MUNICIPAL}/versoes/1/pdf", headers=_sec(cliente)).status_code == 200
    for url in (f"/gestao/secretario/declaracoes/{co}/versoes/1/pdf", f"/gestao/secretario/planos/{co}/versoes/1/pdf", f"{MUNICIPAL}/versoes/1/pdf"):
        assert cliente.get(url, headers=rio).status_code == 404, url


def test_plano_escolar_em_pdf_com_decisao_e_base_desatualizada(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    _plano_enviado(cliente, diretora)

    antes = _texto(cliente.get(f"{PLANO}/versoes/1/pdf", headers=diretora))
    for esperado in ("Plano de Ação Escolar — versão 1", "Aguardando análise da secretaria", "Solicitar à secretaria a sala de recursos.",
                     "Escrita pelo diretor", "LOA — exercício corrente", "Custos são estimativas da escola", "Uso interno"):
        assert esperado in antes, esperado

    _decidir(cliente, co, 1, "ajustes", "Detalhar o prazo da ação.")
    _emitir(cliente, diretora, "A gestão escolar pediu de novo o recurso e segue sem resposta.")  # nova Declaração depois do envio
    depois = _texto(cliente.get(f"/gestao/secretario/planos/{co}/versoes/1/pdf", headers=_sec(cliente)))
    assert "Ajustes solicitados pela secretaria" in depois and "Detalhar o prazo da ação." in depois
    assert "emitiu a versão 2 depois deste envio" in depois
    # Quem decidiu aparece só pelo papel (decisão de 2026-11-03).
    assert "pela Secretaria Municipal de Educação" in depois and "Sec Niterói" not in depois
    # A decisão não muda o código: ele identifica o conteúdo enviado (RN-PDF-04).
    assert _codigo(antes) == _codigo(depois)


def test_plano_municipal_em_pdf_so_para_o_secretario(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    co = _co_entidade(cliente, diretora)
    item = cliente.get(MUNICIPAL, headers=_sec(cliente)).json()["barreiras"][0]["itens"][0]
    nova = {"codigos": [codigo], "acao": "Realizar formação da rede sobre AEE.", "horizonte": "PPA", "prioridade": "alta",
            "escolas": [{"coEntidade": co, "itemIds": [item["itemId"]], "cobertura": "parcial"}]}
    cliente.post(f"{MUNICIPAL}/acoes", json=nova, headers=_sec(cliente))
    cliente.post(f"{MUNICIPAL}/confirmar", json={"confirmado": True}, headers=_sec(cliente))

    chamadas = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", lambda *a, **k: chamadas.append(a))])
    texto = _texto(cliente.get(f"{MUNICIPAL}/versoes/1/pdf", headers=_sec(cliente)))
    assert chamadas == []  # nenhuma IA na geração (RN-PDF-07)
    for esperado in ("Plano Estratégico Municipal — versão 1", "Realizar formação da rede sobre AEE.", "prioridade Alta",
                     "cobertura parcial", "Escrita pelo secretário", "não é aprovar orçamento", "Plano de Ação aceito, versão 1",
                     "pela Secretaria Municipal de Educação", item["escola"]):
        assert esperado in texto, esperado
    assert "Sec Niterói" not in texto


def test_retirada_por_dado_pessoal_bloqueia_o_pdf(ambiente):
    """Revisão do AgLGPD, A1: a versão retirada por dado pessoal ou pedido de titular continua na tela,
    mas não sai em cópia portátil. Outras retiradas seguem gerando o PDF."""
    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _plano_enviado(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "aceitar")
    assert cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 200
    assert cliente.post(f"{PLANO}/versoes/1/publicar", json={"aprovado": True}, headers=diretora).status_code == 200
    publicada = _texto(cliente.get(f"{DECL}/versoes/1/pdf", headers=diretora))
    assert "Versão publicada em" in publicada and "página da escola" in publicada

    assert cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "pedido_de_titular"}, headers=diretora).status_code == 200
    for url, auth in ((f"{DECL}/versoes/1/pdf", diretora), (f"/gestao/secretario/declaracoes/{co}/versoes/1/pdf", _sec(cliente)),
                      (f"{PLANO}/versoes/1/pdf", diretora), (f"/gestao/secretario/planos/{co}/versoes/1/pdf", _sec(cliente))):
        resposta = cliente.get(url, headers=auth)
        assert resposta.status_code == 409 and "proteção de dados pessoais" in resposta.json()["detail"], url
    assert cliente.get(f"{DECL}/versoes/1", headers=diretora).status_code == 200  # a tela continua (AD-03)
    assert {e.resultado for e in _eventos()} >= {"recusado"}

    # Retirada por decisão da escola não bloqueia.
    _emitir(cliente, outra)
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=outra)
    assert cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "decisao_da_escola"}, headers=outra).status_code == 200
    assert "Publicação retirada em" in _texto(cliente.get(f"{DECL}/versoes/1/pdf", headers=outra))


def test_retirada_por_dado_pessoal_tambem_bloqueia(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "dado_pessoal"}, headers=diretora)
    assert cliente.get(f"{DECL}/versoes/1/pdf", headers=diretora).status_code == 409


def test_achado_do_guardiao_na_rota_nao_vaza_no_log_nem_na_resposta(ambiente, caplog):
    from app.features.declaracao.modelos import DeclaracaoItem

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    # Simula texto gravado antes de uma melhoria do Guardião.
    sessao = next(banco_gestao.obter_sessao())
    item = sessao.scalar(select(DeclaracaoItem).where(DeclaracaoItem.posicao == "obstaculo"))
    item.texto = "Ligar para a responsável no 21 99999-1234."
    sessao.commit()
    sessao.close()

    with caplog.at_level(logging.DEBUG):
        resposta = cliente.get(f"{DECL}/versoes/1/pdf", headers=diretora)
    assert resposta.status_code == 409
    assert "99999" not in resposta.text and "99999" not in caplog.text
    assert any(e.resultado == "recusado" and e.detalhe.startswith("guardiao") for e in _eventos())


def test_limite_de_downloads_por_conta(ambiente, monkeypatch):
    from app.features.acesso.protecao import limitar_pdf

    cliente, diretora, outra = ambiente
    _emitir(cliente, diretora)
    _emitir(cliente, outra)
    monkeypatch.setattr(limitar_pdf, "limite", 2)
    assert [cliente.get(f"{DECL}/versoes/1/pdf", headers=diretora).status_code for _ in range(3)] == [200, 200, 429]
    assert cliente.get(f"{DECL}/versoes/1/pdf", headers=outra).status_code == 200  # o limite é por conta


def _documento(texto_livre: str) -> Documento:
    return Documento(
        tipo="Teste", sujeito="Escola", versao=1, identificacao=[], ressalvas=[], nome_arquivo="t.pdf", congelado={"a": 1},
        alvo=("teste", "1"), secoes=[Secao("S", campos=[Campo("Relato", texto_livre, livre=True), Campo("Dado do Censo", "CPF 123.456.789-09")])],
    )


def test_guardiao_confere_de_novo_o_texto_livre():
    from app.shared.pdf import DocumentoInseguro, conferir

    limpo = conferir(_documento("A escola pediu a sala de recursos."))
    assert limpo.secoes[0].campos[0].valor == "A escola pediu a sala de recursos." and limpo.ressalvas == []
    try:
        conferir(_documento("Ligar para a mãe no 21 99999-1234."))
    except DocumentoInseguro as erro:
        assert erro.tipos and "99999" not in str(erro)
    else:
        raise AssertionError("telefone em texto livre deveria impedir o PDF")


def test_nome_que_escapou_na_gravacao_e_mascarado_so_no_pdf():
    """Revisão do AgLGPD, M1: a camada de nomes também roda na geração; o PDF mostra menos que a tela, nunca mais."""
    from app.shared.pdf import conferir, gerar

    documento = _documento("A aluna Joana Pereira Lima precisa de ledor.")
    conferido = conferir(documento)
    assert "Joana" not in conferido.secoes[0].campos[0].valor and "[NOME]" in conferido.secoes[0].campos[0].valor
    assert any("trocados por marcadores" in r for r in conferido.ressalvas)
    texto = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(gerar(documento))).pages)
    assert "Joana" not in texto
    # O código continua sobre o conteúdo congelado, não sobre o texto mascarado.
    assert codigo_conferencia(documento.congelado) in " ".join(texto.split())


def test_codigo_de_conferencia_depende_so_do_conteudo():
    from datetime import datetime, timezone

    base = {"versao": 1, "itens": [{"texto": "a"}], "em": datetime(2026, 11, 3, 12, tzinfo=timezone.utc)}
    sem_fuso = {**base, "em": datetime(2026, 11, 3, 12)}
    assert codigo_conferencia(base) == codigo_conferencia(dict(reversed(base.items()))) == codigo_conferencia(sem_fuso)
    assert codigo_conferencia(base) != codigo_conferencia({**base, "itens": [{"texto": "b"}]})
    assert len(codigo_conferencia(base)) == 14
