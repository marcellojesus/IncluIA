"""Spec: AD-07 em docs/sdd/fase-2/arquitetura.md e RN-RET-01 a 08 em business-rules/retencao.md.

As datas são envelhecidas direto no banco; a auditoria não pode ser alterada, então o evento antigo
entra já com a data antiga.
"""

from datetime import timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError

from app.features import retencao
from app.features.acesso import censo
from app.features.acesso.modelos import Conta, EventoAuditoria, Vinculo
from app.features.analitico.modelos import SinteseAnalitica
from app.features.declaracao.modelos import Declaracao, MensagemObstaculo, Posicao
from app.features.plano.modelos import SugestaoPlano, VersaoPlano
from app.features.plano_municipal.modelos import SugestaoMunicipal
from app.features.retencao.servico import NOME_PSEUDONIMIZADO, TEXTO_APAGADO
from app.shared import banco_gestao
from app.shared.banco_gestao import agora
from tests.test_declaracao import NITEROI, ambiente  # noqa: F401 — fixture compartilhada
from tests.test_documentos_pdf import DECL, PLANO, _plano_enviado
from tests.test_plano import TEXTO, _emitir
from tests.test_revisao_planos import _co_entidade, _decidir

DIAS = timedelta(days=1)


def _sessao():
    return next(banco_gestao.obter_sessao())


def _aplicar() -> dict[str, int]:
    sessao = _sessao()
    try:
        return retencao.aplicar(sessao)
    finally:
        sessao.close()


def _conta(sessao, email: str) -> Conta:
    return sessao.scalar(select(Conta).where(Conta.email == email))


# --- RN-RET-03: auditoria -------------------------------------------------------------------------

def _evento_antigo(acao: str, dias: int) -> None:
    """A auditoria só aceita a data do servidor; o teste tira o gatilho só para gravar o evento antigo."""
    inserir = text("INSERT INTO auditoria (id, acao, alvo_tipo, alvo_id, resultado, criado_em) VALUES (:id, :acao, 'conta', 'x', 'ok', :em)")
    with banco_gestao.engine().begin() as conexao:
        if conexao.dialect.name == "postgresql":
            conexao.execute(text("ALTER TABLE auditoria DISABLE TRIGGER auditoria_protegida"))
            conexao.execute(inserir, {"id": acao, "acao": acao, "em": agora() - dias * DIAS})
            conexao.execute(text("ALTER TABLE auditoria ENABLE TRIGGER auditoria_protegida"))
            return
        gatilho = conexao.execute(text("SELECT sql FROM sqlite_master WHERE name = 'auditoria_data_do_servidor'")).scalar_one()
        conexao.execute(text("DROP TRIGGER auditoria_data_do_servidor"))
        conexao.execute(inserir, {"id": acao, "acao": acao, "em": (agora() - dias * DIAS).strftime("%Y-%m-%d %H:%M:%S.%f")})
        conexao.execute(text(gatilho))


def test_auditoria_nao_muda_e_so_sai_depois_de_5_anos(ambiente):
    _evento_antigo("teste_antigo", 1830)
    _evento_antigo("teste_recente", 1800)
    forjar = ("INSERT INTO auditoria (id, acao, alvo_tipo, alvo_id, resultado, criado_em) "
              "VALUES ('f', 'forjado', 'conta', 'x', 'ok', '2020-01-01 00:00:00.000000')")
    with banco_gestao.engine().connect() as conexao:
        postgres = conexao.dialect.name == "postgresql"
        comandos = ["UPDATE auditoria SET detalhe = 'alterado'", "DELETE FROM auditoria WHERE acao = 'teste_recente'"]
        if postgres:
            comandos.append("TRUNCATE auditoria")
        else:
            comandos.append(forjar)  # no SQLite, data que não é a do servidor é recusada
        for comando in comandos:
            with pytest.raises(DatabaseError, match="auditoria"):
                conexao.execute(text(comando))
            conexao.rollback()
        if postgres:
            # No PostgreSQL, o gatilho troca a data forjada pela do servidor.
            conexao.execute(text(forjar))
            gravada = conexao.execute(text("SELECT criado_em FROM auditoria WHERE id = 'f'")).scalar_one()
            assert abs((gravada - agora()).total_seconds()) < 3600
            conexao.rollback()
    sessao = _sessao()
    sessao.add(EventoAuditoria(acao="teste_agora", alvo_tipo="conta", alvo_id="x", resultado="ok"))  # a data do servidor entra
    sessao.commit()
    sessao.close()

    assert _aplicar()["auditoria_antiga"] == 1
    acoes = set(_sessao().scalars(select(EventoAuditoria.acao)))
    assert "teste_antigo" not in acoes and {"teste_recente", "teste_agora"} <= acoes


def test_rotina_nao_aceita_data_futura_e_regra_que_falha_nao_derruba_as_outras(ambiente, monkeypatch):
    with pytest.raises(ValueError):
        retencao.aplicar(_sessao(), agora() + 2 * DIAS)

    def quebra(_sessao, _momento):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(retencao.servico, "_REGRAS", [("sugestoes_apagadas", quebra), *retencao.servico._REGRAS[2:]])
    resultado = _aplicar()
    assert resultado["sugestoes_apagadas"] == -1 and resultado["auditoria_antiga"] == 0


# --- RN-RET-01: rascunhos -------------------------------------------------------------------------

def test_sugestao_nao_usada_perde_o_conteudo_em_30_dias(ambiente):
    from app.features.plano.modelos import AcaoPlano

    sessao = _sessao()
    diretora = _conta(sessao, "diretora@escola.gov.br").id
    velha, nova = agora() - 31 * DIAS, agora() - 29 * DIAS
    conteudo = {"acao": "Texto da IA"}
    for estado, criado in (("descartada", velha), ("substituida", velha), ("pendente", velha), ("aceita", velha), ("descartada", nova)):
        sessao.add(SugestaoPlano(co_entidade=1, codigo="B-I-01", declaracao_versao=1, conteudo=conteudo, estado=estado, criado_em=criado))
    # Aceita e usada sem edição: o texto é o mesmo da ação, fica.
    usada = SugestaoPlano(id="usada", co_entidade=1, codigo="B-I-01", declaracao_versao=1, conteudo=conteudo, estado="aceita", criado_em=velha)
    sessao.add(usada)
    sessao.flush()
    sessao.add(AcaoPlano(co_entidade=1, codigo="B-I-01", acao="Texto da IA", horizonte="LOA", origem="ia", sugestao_id="usada", autor_id=diretora))
    sessao.add(SugestaoMunicipal(co_municipio=NITEROI, codigo="B-I-01", conteudo=conteudo, estado="descartada", criado_em=velha))
    sessao.commit()
    sessao.close()

    assert _aplicar()["sugestoes_apagadas"] == 5
    sessao = _sessao()
    plano = {(s.id == "usada", s.estado, bool(s.conteudo)) for s in sessao.scalars(select(SugestaoPlano))}
    assert plano == {(False, "descartada", False), (False, "substituida", False), (False, "expirada", False),
                     (False, "aceita", False), (True, "aceita", True), (False, "descartada", True)}
    assert sessao.scalar(select(SugestaoMunicipal)).conteudo == {}
    assert _aplicar()["sugestoes_apagadas"] == 0  # a segunda rodada não repete


# --- RN-RET-02 e 04: pedidos recusados e contas encerradas ----------------------------------------

def _decidir_vinculo(email: str, estado: str, dias: int) -> str:
    sessao = _sessao()
    conta = _conta(sessao, email)
    vinculo = conta.vinculo_vigente()
    vinculo.estado, vinculo.decidido_em, vinculo.justificativa = estado, agora() - dias * DIAS, "Justificativa com dado da pessoa"
    sessao.commit()
    conta_id = conta.id
    sessao.close()
    return conta_id


def test_conta_revogada_pseudonimizada_em_6_meses(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    conta_id = _decidir_vinculo("diretora@escola.gov.br", "revogado", 182)
    assert _aplicar()["contas_pseudonimizadas"] == 0

    sessao = _sessao()
    sessao.get(Conta, conta_id).vinculos[0].decidido_em = agora() - 184 * DIAS
    sessao.commit()
    sessao.close()
    assert _aplicar()["contas_pseudonimizadas"] == 1

    sessao = _sessao()
    conta = sessao.get(Conta, conta_id)
    assert conta.nome == NOME_PSEUDONIMIZADO and "escola.gov.br" not in conta.email and conta.anonimizada_em
    assert conta.vinculos[0].justificativa is None
    # A versão emitida fica e passa a apontar para a conta encerrada (RN-RET-06).
    assert sessao.scalar(select(Declaracao).where(Declaracao.emitida_por == conta_id)) is not None
    assert sessao.scalar(select(EventoAuditoria).where(EventoAuditoria.acao == "conta_pseudonimizada")).alvo_id == conta_id
    assert _conta(sessao, "diretora@escola.gov.br") is None  # o e-mail sai; quem voltar começa um pedido novo


def test_pedido_recusado_sai_em_30_dias_com_a_conta_pseudonimizada(ambiente):
    cliente, _, _ = ambiente
    conta_id = _decidir_vinculo("outra@escola.gov.br", "rejeitado", 31)
    resultado = _aplicar()
    assert resultado["pedidos_recusados"] == 1 and resultado["contas_pseudonimizadas"] == 1
    sessao = _sessao()
    assert sessao.scalars(select(Vinculo).where(Vinculo.conta_id == conta_id)).all() == []
    assert sessao.get(Conta, conta_id).nome == NOME_PSEUDONIMIZADO
    # Secretário e diretora ativa não são tocados.
    assert _conta(sessao, "sec@niteroi.gov.br") and _conta(sessao, "diretora@escola.gov.br")


# --- RN-RET-05: texto da versão retirada por proteção de dados ------------------------------------

def test_texto_da_versao_retirada_por_dado_pessoal_sai_em_30_dias(ambiente):
    cliente, diretora, _ = ambiente
    codigo, _ = _emitir(cliente, diretora)
    _plano_enviado(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "aceitar", comentario="Plano conferido pela secretaria.")
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post(f"{PLANO}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    assert cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "dado_pessoal"}, headers=diretora).status_code == 200

    sessao = _sessao()
    sessao.add(MensagemObstaculo(co_entidade=co, codigo=codigo, papel="diretor", texto=TEXTO))
    sessao.commit()
    assert _aplicar()["versoes_com_texto_apagado"] == 0  # antes dos 30 dias
    for modelo in (Declaracao, VersaoPlano):
        sessao.scalar(select(modelo).where(modelo.co_entidade == co)).retirada_em = agora() - 31 * DIAS
    sessao.commit()
    sessao.close()

    assert _aplicar()["versoes_com_texto_apagado"] == 1  # o plano sobre a Declaração sai junto
    sessao = _sessao()
    declaracao = sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co))
    item = next(i for i in declaracao.itens if i.codigo == codigo)
    assert item.texto == TEXTO_APAGADO and item.resumo is None and item.texto_publico is None and declaracao.texto_apagado_em
    assert item.posicao == "obstaculo" and item.dado_censo  # a estrutura fica
    posicao = sessao.scalar(select(Posicao).where(Posicao.co_entidade == co, Posicao.codigo == codigo))
    assert posicao.texto is None and posicao.relato_original is None
    assert sessao.scalars(select(MensagemObstaculo).where(MensagemObstaculo.co_entidade == co)).all() == []
    plano = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == co))
    assert {i.acao for i in plano.itens} == {TEXTO_APAGADO} and plano.comentario is None
    assert all(i.custo_estimado is None for i in plano.itens)

    tela = cliente.get(f"{DECL}/versoes/1", headers=diretora)
    assert tela.status_code == 200 and TEXTO not in tela.text
    assert _aplicar()["versoes_com_texto_apagado"] == 0


def test_retirada_por_decisao_da_escola_mantem_o_texto(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "decisao_da_escola"}, headers=diretora)
    sessao = _sessao()
    sessao.scalar(select(Declaracao)).retirada_em = agora() - 90 * DIAS
    sessao.commit()
    sessao.close()
    assert _aplicar()["versoes_com_texto_apagado"] == 0
    assert TEXTO in cliente.get(f"{DECL}/versoes/1", headers=diretora).text


# --- RN-RET-07: sínteses do Analítico -------------------------------------------------------------

def test_sintese_sai_em_1_ano_na_edicao_nova_ou_com_relato_retirado(ambiente):
    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "pedido_de_titular"}, headers=diretora)
    sessao = _sessao()
    retirada = sessao.scalar(select(Declaracao)).id
    secretario = _conta(sessao, "sec@niteroi.gov.br").id
    edicao = censo.edicao_do_municipio(NITEROI)

    def sintese(nome, dias, **conteudo):
        sessao.add(SinteseAnalitica(co_municipio=NITEROI, gerada_por=secretario, assinatura=nome, modelo="teste",
                                    gerada_em=agora() - dias * DIAS, conteudo={"achados": [], "censo_versao": edicao, **conteudo}))

    sintese("antiga", 366)
    sintese("outra_edicao", 10, censo_versao="2019")
    sintese("com_retirada", 10, enviados=[{"declaracao_id": retirada, "codigo": "B-I-01"}])
    sintese("valida", 10, enviados=[{"declaracao_id": "outra", "codigo": "B-I-01"}])
    sintese("sem_edicao", 10, censo_versao=None)  # síntese anterior à regra: vale só o prazo de 1 ano
    sessao.commit()
    sessao.close()

    assert _aplicar()["sinteses_apagadas"] == 3
    assert sorted(_sessao().scalars(select(SinteseAnalitica.assinatura))) == ["sem_edicao", "valida"]


# --- Revisão do AgLGPD da retenção (2026-11-03) ---------------------------------------------------

def test_conta_pseudonimizada_nao_quebra_a_rotina_seguinte(ambiente):
    """A1: a conta com e-mail confirmado e auditoria não pode ser apagada na rodada seguinte."""
    conta_id = _decidir_vinculo("outra@escola.gov.br", "rejeitado", 31)
    assert _aplicar()["contas_pseudonimizadas"] == 1
    for _ in range(2):
        resultado = _aplicar()
        assert -1 not in resultado.values(), resultado
    sessao = _sessao()
    assert sessao.get(Conta, conta_id).nome == NOME_PSEUDONIMIZADO
    assert sessao.scalar(select(EventoAuditoria).where(EventoAuditoria.ator_id == conta_id)) is not None


def test_apagamento_alcanca_as_outras_copias_da_escola(ambiente):
    """A2: versão anterior com o mesmo relato, plano não publicado feito sobre a Declaração retirada,
    rascunho corrigido depois da retirada."""
    from app.features.plano.modelos import AcaoPlano

    cliente, diretora, _ = ambiente
    codigo, outro = _emitir(cliente, diretora)  # v1, não publicada, mesmo relato
    corpo = {"posicao": "obstaculo", "texto": "A escola relata falta de intérprete nas reuniões.", "resumo": "Sem intérprete"}
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{outro}", json=corpo, headers=diretora)
    assert cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora).status_code in (200, 201)  # v2
    _plano_enviado(cliente, diretora)  # plano sobre a v2, nunca publicado
    co = _co_entidade(cliente, diretora)
    cliente.post(f"{DECL}/versoes/2/publicar", json={"aprovado": True}, headers=diretora)
    assert cliente.post(f"{DECL}/versoes/2/retirar", json={"motivo": "pedido_de_titular"}, headers=diretora).status_code == 200
    # O diretor corrige o relato depois da retirada; o relato original da conversa ainda é o antigo.
    corrigido = "A escola pediu o recurso à secretaria e aguarda resposta."
    cliente.put(f"/gestao/diretor/declaracao/barreiras/{codigo}", json={"posicao": "obstaculo", "texto": corrigido}, headers=diretora)
    sessao = _sessao()
    posicao = sessao.scalar(select(Posicao).where(Posicao.co_entidade == co, Posicao.codigo == codigo))
    posicao.relato_original = TEXTO + "!"  # mesma frase, outra pontuação
    sessao.scalar(select(Declaracao).where(Declaracao.co_entidade == co, Declaracao.versao == 2)).retirada_em = agora() - 31 * DIAS
    sessao.commit()
    sessao.close()

    _aplicar()
    sessao = _sessao()
    for declaracao in sessao.scalars(select(Declaracao).where(Declaracao.co_entidade == co)):
        assert TEXTO not in {i.texto for i in declaracao.itens}, declaracao.versao
    posicao = sessao.scalar(select(Posicao).where(Posicao.co_entidade == co, Posicao.codigo == codigo))
    assert posicao.relato_original is None and posicao.texto == corrigido  # o texto novo do diretor fica
    plano = sessao.scalar(select(VersaoPlano).where(VersaoPlano.co_entidade == co))
    assert plano.texto_apagado_em and {i.acao for i in plano.itens} == {TEXTO_APAGADO}
    assert {a.acao for a in sessao.scalars(select(AcaoPlano).where(AcaoPlano.co_entidade == co))} <= {TEXTO_APAGADO}


def test_base_da_rede_nao_usa_plano_sobre_declaracao_retirada(ambiente):
    """M1: o texto do plano vai ser apagado e não pode seguir para a IA municipal."""
    from app.features.plano_municipal import base as base_rede

    cliente, diretora, _ = ambiente
    _emitir(cliente, diretora)
    _plano_enviado(cliente, diretora)
    co = _co_entidade(cliente, diretora)
    _decidir(cliente, co, 1, "aceitar")
    sessao = _sessao()
    assert co in base_rede._ultimas_aceitas(sessao, NITEROI)
    sessao.close()
    cliente.post(f"{DECL}/versoes/1/publicar", json={"aprovado": True}, headers=diretora)
    cliente.post(f"{DECL}/versoes/1/retirar", json={"motivo": "dado_pessoal"}, headers=diretora)
    sessao = _sessao()
    assert co not in base_rede._ultimas_aceitas(sessao, NITEROI)
    sessao.close()


def test_sintese_de_municipio_fora_do_artefato_nao_e_apagada_pela_edicao(ambiente, monkeypatch):
    """M4: sem a edição atual não dá para dizer que mudou."""
    sessao = _sessao()
    secretario = _conta(sessao, "sec@niteroi.gov.br").id
    sessao.add(SinteseAnalitica(co_municipio=NITEROI, gerada_por=secretario, assinatura="x", modelo="teste",
                                conteudo={"achados": [], "censo_versao": "2024"}))
    sessao.commit()
    sessao.close()
    monkeypatch.setattr(censo, "edicao_do_municipio", lambda _co: None)
    assert _aplicar()["sinteses_apagadas"] == 0
