"""Camada 5 do Guardião (locais): nomes da rede e códigos INEP não vão à IA. Pendência 16 da
arquitetura; PBD-028, 029 e 112; OWASP LLM02."""

from app.features.acesso import censo
from app.shared import ai_client
from app.shared.guardiao_lgpd import MARCADOR_LOCAL, SEM_LOCAIS, contem_local, nomes_da_rede, proteger, proteger_para_ia
from tests.test_declaracao import ESCOLA, _provedor, ambiente  # noqa: F401 — fixture e auxiliares compartilhados
from tests.test_plano import _emitir, _sugestao
from tests.test_plano_municipal import URL as MUNICIPAL
from tests.test_plano_municipal import _plano_aceito, _resposta, _sec
from tests.test_revisao_planos import _co_entidade


def _proibidos(escola) -> tuple[str, ...]:
    return escola.nome, escola.nome.title(), str(escola.co_entidade), escola.municipio


def _limpo(texto: str, locais) -> str:
    return proteger_para_ia(texto, locais).texto_mascarado


def test_nomes_da_rede_saem_com_e_sem_prefixo_e_sem_acento():
    nomes = nomes_da_rede("Lucas do Rio Verde", ["EMEF Santa Rita", "Escola Municipal de Ensino Fundamental São João Batista"])
    texto = "Na Escola Santa Rita e na SAO JOÃO BATISTA, em Lucas do Rio Verde (código 51234567)."
    limpo = _limpo(texto, nomes)
    for proibido in ("Santa Rita", "JOÃO BATISTA", "Lucas", "51234567"):
        assert proibido not in limpo, proibido
    assert MARCADOR_LOCAL in limpo and contem_local(texto, nomes) and not contem_local(limpo, nomes)
    assert " em [escola" in limpo  # a preposição fica
    assert _limpo("Formação para a rede.", nomes) == "Formação para a rede."
    # Sem os locais (texto que não vai à IA), a camada não roda.
    assert "Santa Rita" in proteger(texto).texto_mascarado


def test_variantes_de_escrita_do_censo():
    """Revisão do AgLGPD de 2026-11-03, A2: prefixos, abreviações, títulos, código no início e separadores."""
    nomes = nomes_da_rede("Lucas do Rio Verde", [
        "ESC MUN SANTA RITA", "EMEF PROFESSORA MARIA DA SILVA", "0101501 CIEP HENFIL", "MARIO ALVES DE CARVALHO DR",
        "MAUA BR DE", "UMEI MONTEIRO LOBATO",
    ])
    casos = {
        "Na Escola Santa Rita faltam rampas.": "Santa Rita",
        "Na esc. mun. santa rita faltam rampas.": "santa rita",
        "A Escola Municipal Santa-Rita pediu apoio.": "Santa-Rita",
        "A Santa\nRita pediu apoio.": "Rita",
        "A EMEF Profa. Maria da Silva pediu apoio.": "Maria",
        "O CIEP Henfil pediu apoio.": "Henfil",
        "A Escola Dr. Mário Alves de Carvalho pediu apoio.": "Carvalho",
        "A Escola Barão de Mauá pediu apoio.": "Mauá",
        "A UMEI Monteiro Lobato pediu apoio.": "Lobato",
    }
    for texto, proibido in casos.items():
        assert proibido not in _limpo(texto, nomes), texto


def test_nome_fraco_so_com_maiuscula_e_nome_generico_ignorado():
    """M1 e M3: município curto e palavra comum só casam com inicial maiúscula; nome só de tipo de escola é ignorado."""
    nomes = nomes_da_rede("Belém", ["EMEF INDEPENDENCIA", "EDUCACAO INFANTIL", "ESCOLA MUNICIPAL"])
    assert "Belém" not in _limpo("A rede de Belém ampliou o AEE.", nomes)
    assert "Independência" not in _limpo("A Independência pediu apoio.", nomes)
    assert "EMEF Independencia" not in _limpo("A EMEF Independencia pediu apoio.", nomes)
    for intacto in ("A independência do estudante é o objetivo.", "Na educação infantil faltam profissionais.",
                    "A escola municipal pediu apoio.", "Em belém de cima não há relato."):
        assert _limpo(intacto, nomes) == intacto, intacto


def test_outras_redes_e_bairros():
    """M2: a escola estadual vizinha e o bairro de duas palavras também localizam a escola."""
    nomes = nomes_da_rede("Niterói", ["COLEGIO ESTADUAL HENRIQUE LAGE"], bairros=["Ponta D'Areia", "Centro", "Jardim Icaraí"])
    limpo = _limpo("Fica ao lado do Colégio Estadual Henrique Lage, no Jardim Icaraí, perto do Centro.", nomes)
    assert "Henrique Lage" not in limpo and "Icaraí" not in limpo and "Centro" in limpo


def test_codigo_com_pontuacao_e_valor_em_reais():
    locais = nomes_da_rede("Niterói", [])
    assert "052" not in _limpo("Códigos 5105.2348 e 51 052 348.", locais)
    assert "R$ 12.345.678,00" in _limpo("Custo de R$ 12.345.678,00.", locais)


def test_mascara_sobreposta_vira_uniao():
    """B4: nome de pessoa e de escola que se sobrepõem em parte não deixam pedaço do nome."""
    nomes = nomes_da_rede("Niterói", ["EMEF SANTA RITA SOUZA"])
    assert "Souza" not in _limpo("A professora Santa Rita Souza Lima pediu apoio.", nomes)


def test_cobertura_com_nomes_reais_do_censo():
    """Amostra das escolas municipais do Censo: o nome, escrito como no Censo ou em caixa de título, é
    trocado; nome só de tipo de escola fica de fora."""
    from app.database import get_connection
    from app.shared.guardiao_lgpd import locais

    conn = get_connection()
    try:
        linhas = conn.execute("SELECT no_entidade FROM escolas WHERE rede = 'Municipal' ORDER BY co_entidade LIMIT 3000").fetchall()
    finally:
        conn.close()
    falhas = []
    for (nome,) in linhas:
        unico = nomes_da_rede("", [nome])
        if not unico.nomes:
            continue
        for escrito in (nome, nome.title()):
            if not locais.encontrar(f"A {escrito} pediu apoio.", unico):
                falhas.append(escrito)
    assert len(falhas) <= len(linhas) * 0.01, falhas[:20]


def test_locais_da_rede_vem_do_censo():
    escola = censo.escola(ESCOLA)
    locais = censo.locais_da_escola(ESCOLA)
    assert locais is censo.locais_da_rede(escola.co_municipio) and contem_local(escola.nome, locais)
    assert censo.locais_da_escola(99999999) is SEM_LOCAIS


def test_conversa_da_declaracao_nao_leva_o_nome_da_escola(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    codigo = cliente.get("/gestao/diretor/declaracao", headers=diretora).json()["barreiras"][0]["codigo"]
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([{"resposta": "Entendi.", "texto_formal": None, "resumo": None}], recebidos))])
    mensagem = f"A {escola.nome}, em {escola.municipio}, pediu o recurso e nada aconteceu."
    assert cliente.post(f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa", json={"mensagem": mensagem}, headers=diretora).status_code == 200
    enviado = str(recebidos[0])
    for proibido in _proibidos(escola):
        assert proibido not in enviado, proibido
    assert MARCADOR_LOCAL in enviado


def test_sugestoes_do_plano_escolar_nao_levam_o_nome_da_escola(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    com_relato, _ = _emitir(cliente, diretora, f"A {escola.nome} pediu o recurso à secretaria em 2025 e não teve resposta.")
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao()], recebidos))])
    orientacao = {"orientacao": f"Considere que a {escola.nome} fica longe do centro."}
    assert cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json=orientacao, headers=diretora).status_code == 200
    enviado = str(recebidos[0])
    for proibido in _proibidos(escola):
        assert proibido not in enviado, proibido
    assert "pediu o recurso" in enviado and MARCADOR_LOCAL in enviado


def test_sugestoes_do_plano_municipal_nao_levam_nomes_da_rede(ambiente, monkeypatch):
    cliente, diretora, outra = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    vizinha = censo.escola(_co_entidade(cliente, outra))
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, f"Dividir a sala de recursos com a {vizinha.nome} ({vizinha.co_entidade}).")
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta([{"ref": "E1-A1", "cobertura": "total"}])], recebidos))])
    corpo = {"orientacao": f"Priorize a {escola.nome}."}
    assert cliente.post(f"{MUNICIPAL}/barreiras/{codigo}/sugestoes", json=corpo, headers=_sec(cliente)).status_code == 200
    enviado = str(recebidos[0])
    for proibido in (*_proibidos(escola), *_proibidos(vizinha)):
        assert proibido not in enviado, proibido
    assert "Dividir a sala de recursos" in enviado


def test_sintese_do_analitico_nao_leva_nomes_da_rede(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    barreiras = cliente.get("/gestao/diretor/declaracao", headers=diretora).json()["barreiras"]
    for i, b in enumerate(barreiras):
        corpo = ({"posicao": "obstaculo", "texto": "A gestão escolar pediu o recurso em 2025.", "resumo": f"Pedido da {escola.nome} sem resposta"}
                 if i == 0 else {"posicao": "sem_relato"})
        cliente.put(f"/gestao/diretor/declaracao/barreiras/{b['codigo']}", json=corpo, headers=diretora)
    cliente.post("/gestao/diretor/declaracao/emitir", headers=diretora)

    recebidos = []
    resposta = {"achados": [{"tipo": "observacao", "texto": "Há pedidos sem resposta [R1].", "barreiras": [barreiras[0]["codigo"]], "relatos": ["R1"]}],
                "limitacoes": []}
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([resposta], recebidos))])
    assert cliente.post("/gestao/secretario/analitico/sintese", headers=_sec(cliente)).status_code == 200
    enviado = str(recebidos[0])
    for proibido in _proibidos(escola):
        assert proibido not in enviado, proibido
    assert "sem resposta" in enviado


def test_historico_da_conversa_e_ajuste_tambem_passam_pela_camada(ambiente, monkeypatch):
    """B8: a fala gravada antes volta à IA na segunda chamada, e o pedido de ajuste do plano também."""
    cliente, diretora, _ = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    codigo = cliente.get("/gestao/diretor/declaracao", headers=diretora).json()["barreiras"][0]["codigo"]
    recebidos = []
    retornos = [{"resposta": "Entendi.", "texto_formal": None, "resumo": None}, {"resposta": "Certo.", "texto_formal": None, "resumo": None}]
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor(retornos, recebidos))])
    url = f"/gestao/diretor/declaracao/barreiras/{codigo}/conversa"
    cliente.post(url, json={"mensagem": f"A {escola.nome} pediu o recurso."}, headers=diretora)
    cliente.post(url, json={"mensagem": "E não houve resposta."}, headers=diretora)
    assert len(recebidos) == 2 and escola.nome not in str(recebidos[1]) and escola.nome.title() not in str(recebidos[1])

    com_relato, _ = _emitir(cliente, diretora)
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_sugestao(), _sugestao("Pedir apoio à rede.")], recebidos))])
    plano = cliente.post(f"/gestao/diretor/plano/barreiras/{com_relato}/sugestoes", json={}, headers=diretora).json()
    sugestao = plano["sugestoes"][0]["id"]
    pedido = {"pedido": f"Ajuste considerando que a {escola.nome.title()} fica longe."}
    assert cliente.post(f"/gestao/diretor/plano/sugestoes/{sugestao}/ajustar", json=pedido, headers=diretora).status_code == 200
    assert escola.nome.title() not in str(recebidos[-1]) and escola.nome not in str(recebidos[-1])
