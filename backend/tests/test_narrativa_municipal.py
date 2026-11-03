"""Spec: RF-30 do PRD da Fase 2; SPM-RF-05 e 06 em requirements/secretario/plano-estrategico-municipal.md; RN-SPM-04."""

from app.features.plano_municipal import narrativa
from app.shared import ai_client
from app.shared.guardiao_lgpd import MARCADOR_LOCAL, SEM_LOCAIS
from tests.test_declaracao import _provedor, ambiente  # noqa: F401 — fixture e auxiliares compartilhados
from tests.test_plano import _emitir
from tests.test_plano_municipal import URL, _plano_aceito, _sec
from tests.test_revisao_planos import _co_entidade

CUSTO = "R$ 120.000,00 por ano"


def _versao_confirmada(cliente, diretora):
    _emitir(cliente, diretora)
    codigo = _plano_aceito(cliente, diretora, "Solicitar à secretaria a contratação do profissional de AEE.")
    cliente.post(f"{URL}/acoes", json={
        "codigos": [codigo], "acao": "Contratar profissionais de AEE compartilhados entre as escolas da rede.", "horizonte": "PPA",
        "prioridade": "alta", "custoEstimado": CUSTO, "premissas": "Dotação aprovada no PPA.",
        "escolas": [{"coEntidade": _co_entidade(cliente, diretora), "itemIds": [], "cobertura": "parcial"}],
    }, headers=_sec(cliente))
    cliente.post(f"{URL}/acoes", json={
        "codigos": [codigo], "acao": "Oferecer formação em educação inclusiva para as equipes da rede.", "horizonte": "LOA",
    }, headers=_sec(cliente))
    assert cliente.post(f"{URL}/confirmar", json={"confirmado": True}, headers=_sec(cliente)).status_code == 201
    return codigo


def _resposta(**trocas):
    resposta = {
        "resumo": "A rede enfrenta falta de atendimento especializado; o plano organiza a resposta da secretaria [A1].",
        "situacao": "A barreira aparece na maioria das escolas da rede.",
        "estrategia": [
            {"texto": "Atendimento especializado compartilhado [A1].", "acoes": ["A1"]},
            {"texto": "Formação das equipes.", "acoes": ["A2"]},
        ],
        "fundamentacao": "A base normativa entregue não trata de contratação compartilhada.",
        "proximos_passos": "Prever a dotação no PPA e estimar os custos.",
        "incertezas": ["Custos ainda a estimar."],
        "fontes": [],
        "lacunas": ["Sem trecho normativo sobre contratação compartilhada."],
    }
    return {**resposta, **trocas}


def test_narrativa_da_versao_sem_escola_municipio_nem_valor_na_ia(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)
    recebidos = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta()], recebidos))])

    dados = cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).json()
    texto = dados["narrativa"]
    assert texto["modelo"] == "teste" and texto["editada"] is False
    assert [b["acoes"] for b in texto["estrategia"]] == [["A1"], ["A2"]]
    # Números calculados pelo sistema a partir da versão congelada (SPM-RF-05).
    n = dados["numeros"]
    assert (n["acoes"], n["loa"], n["ppa"], n["prioridadeAlta"], n["comCustoEstimado"], n["comCoberturaParcial"]) == (2, 1, 1, 1, 1, 1)
    assert n["escolasAtendidas"] == 1 and n["escolasMunicipais"] > 1

    enviado = str(recebidos[0])
    assert "[A1]" in enviado and "[A2]" in enviado and "estimativa registrada pela secretaria" in enviado
    escola = next(e["escola"] for a in dados["acoes"] for e in a["escolas"])
    for proibido in (escola, str(_co_entidade(cliente, diretora)), "Niterói", "NITERÓI", "120.000", "%"):
        assert proibido not in enviado, proibido

    # Abrir a versão devolve a narrativa guardada; gerar de novo substitui.
    assert cliente.get(f"{URL}/versoes/1", headers=_sec(cliente)).json()["narrativa"]["resumo"] == texto["resumo"]


def test_numero_no_texto_passa_ao_proximo_provedor(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)
    com_numero = _resposta(resumo="O plano custará R$ 120 mil e atende 40% das escolas.")
    com_contagem = _resposta(situacao="A barreira aparece em 12 escolas.")
    monkeypatch.setattr(ai_client, "_PROVEDORES", [
        ("valor", _provedor([com_numero], [])), ("contagem", _provedor([com_contagem], [])), ("certo", _provedor([_resposta()], [])),
    ])
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).json()["narrativa"]["modelo"] == "certo"


def test_acao_inventada_passa_ao_proximo_provedor(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)
    inventada = _resposta(estrategia=[{"texto": "Ação que não está no plano [A9].", "acoes": ["A9"]}])
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("inventa", _provedor([inventada], [])), ("certo", _provedor([_resposta()], []))])
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).json()["narrativa"]["modelo"] == "certo"


def test_secretario_edita_e_texto_passa_pelo_guardiao(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)
    assert cliente.put(f"{URL}/versoes/1/narrativa", json={"resumo": "Texto sem narrativa gerada."}, headers=_sec(cliente)).status_code == 404
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta()], []))])
    cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente))

    corpo = {
        "resumo": "Resumo revisto pela secretaria com a professora Ana Clara.",
        "estrategia": [{"texto": "Atendimento especializado e formação.", "acoes": ["A1", "A2"]}],
        "incertezas": ["Valor depende da licitação."],
    }
    dados = cliente.put(f"{URL}/versoes/1/narrativa", json=corpo, headers=_sec(cliente)).json()
    assert dados["narrativa"]["editada"] is True and "Ana Clara" not in dados["narrativa"]["resumo"]
    assert dados["narrativa"]["estrategia"] == [{"texto": "Atendimento especializado e formação.", "acoes": ["A1", "A2"]}]
    assert dados["avisoGuardiao"]

    fora = {**corpo, "estrategia": [{"texto": "Ação de outra versão.", "acoes": ["A7"]}]}
    assert cliente.put(f"{URL}/versoes/1/narrativa", json=fora, headers=_sec(cliente)).status_code == 404


def test_so_o_secretario_e_so_versao_existente(ambiente):
    cliente, diretora, _ = ambiente
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=diretora).status_code == 403
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).status_code == 404


def test_sem_ia_a_versao_continua(ambiente, monkeypatch):
    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)

    async def fora_do_ar(*_args):
        raise RuntimeError("provedor fora")

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("fora", fora_do_ar)])
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).status_code == 503
    versao = cliente.get(f"{URL}/versoes/1", headers=_sec(cliente)).json()
    assert versao["narrativa"] is None and versao["numeros"]["acoes"] == 2


def test_faixas_tiram_os_percentuais_do_contexto():
    texto = "presente em cerca de 95% das escolas da rede; Plano enviado: cerca de 45% das escolas; poucas escolas."
    assert narrativa.sem_percentuais(texto) == (
        "presente em quase todas as escolas da rede; Plano enviado: cerca de metade das escolas; poucas escolas."
    )


def test_nome_de_escola_e_municipio_no_texto_da_acao_nao_vai_a_ia(ambiente, monkeypatch):
    """Revisão do AgLGPD (B1): o Guardião trata "EMEF ..." e município composto como nomes públicos."""
    from app.features.acesso import censo

    cliente, diretora, _ = ambiente
    escola = censo.escola(_co_entidade(cliente, diretora))
    codigo = _versao_confirmada(cliente, diretora)
    cliente.post(f"{URL}/acoes", json={
        "codigos": [codigo], "horizonte": "LOA",
        "acao": f"Abrir sala de recursos na {escola.nome} ({escola.co_entidade}), em Niterói, com apoio da rede.",
    }, headers=_sec(cliente))
    cliente.post(f"{URL}/confirmar", json={"confirmado": True}, headers=_sec(cliente))

    recebidos = []
    citando_escola = _resposta(resumo=f"O plano começa pela {escola.nome}.")
    monkeypatch.setattr(ai_client, "_PROVEDORES", [
        ("cita", _provedor([citando_escola], [])), ("certo", _provedor([_resposta()], recebidos)),
    ])
    dados = cliente.post(f"{URL}/versoes/2/narrativa", headers=_sec(cliente)).json()
    assert dados["narrativa"]["modelo"] == "certo", "resposta com nome de escola passa ao próximo provedor"
    enviado = str(recebidos[0])
    for proibido in (escola.nome, str(escola.co_entidade), "Niterói", "NITERÓI"):
        assert proibido not in enviado, proibido
    assert MARCADOR_LOCAL in enviado


def test_trilha_e_auditoria_da_geracao(ambiente, monkeypatch):
    from app.features.acesso.modelos import EventoAuditoria
    from app.features.plano_municipal.modelos import NarrativaPlanoMunicipal
    from app.shared import banco_gestao

    cliente, diretora, _ = ambiente
    _versao_confirmada(cliente, diretora)
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta(), _resposta()], []))])
    cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente))
    cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente))

    sessao = next(banco_gestao.obter_sessao())
    registro = sessao.query(NarrativaPlanoMunicipal).one()
    trilha = registro.conteudo["trilha"]
    assert len(trilha) == 2 and len(trilha[-1]["acoes_enviadas"]) == 2
    assert "acao" not in str(trilha).replace("acoes_enviadas", "")  # só ids, sem texto
    assert sessao.query(EventoAuditoria).filter_by(acao="narrativa_plano_municipal_gerada").count() == 2
    sessao.close()


def test_texto_livre_retido_para_escola_pequena_ou_retirada_lgpd():
    """Revisão do AgLGPD (B2 e R1): mesma regra do Analítico; vai só a linha estruturada."""
    restricoes = narrativa.Restricoes(nomes=SEM_LOCAIS, pequenas=frozenset({1}), retiradas=frozenset({2}))
    acao = {"acao": "Texto que descreve a situação da escola.", "codigos": ["B-IV-01"], "horizonte": "LOA",
            "escolas": [{"co_entidade": 1, "cobertura": "parcial"}]}
    assert narrativa.motivo_restricao(acao, restricoes) == "escola_pequena"
    linha = narrativa._linha(1, acao, 40, restricoes)
    assert "Texto que descreve" not in linha and "ação localizada" in linha and "parcial" not in linha

    retirada = {**acao, "codigos": ["B-I-01"], "escolas": [{"co_entidade": 2}, {"co_entidade": 3}, {"co_entidade": 4}]}
    assert narrativa.motivo_restricao(retirada, restricoes) == "retirada_lgpd"
    comum = {**retirada, "escolas": [{"co_entidade": 3}, {"co_entidade": 4}, {"co_entidade": 5}]}
    assert narrativa.motivo_restricao(comum, restricoes) is None


# --- Edição conferida e PDF da narrativa (PDF-RF-07; RN-PDF-09; decisões de 2026-11-03) -----------

def _gerada(cliente, diretora, monkeypatch):
    _versao_confirmada(cliente, diretora)
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor([_resposta()], []))])
    assert cliente.post(f"{URL}/versoes/1/narrativa", headers=_sec(cliente)).status_code == 200


def test_edicao_com_numero_ou_nome_da_rede_nao_e_salva(ambiente, monkeypatch):
    from app.features.acesso import censo

    cliente, diretora, _ = ambiente
    _gerada(cliente, diretora, monkeypatch)
    escola = censo.escola(_co_entidade(cliente, diretora))
    base = {"resumo": "Resumo revisto.", "estrategia": [{"texto": "Atendimento especializado.", "acoes": ["A1"]}]}

    for trecho, motivo in ((f"O plano começa pela {escola.nome}.", "nomes de escola"), ("Em Niterói, a rede avança.", "nomes de escola"),
                           ("O plano custa R$ 120 mil.", "valores em reais"), ("Atende 12 escolas.", "valores em reais")):
        resposta = cliente.put(f"{URL}/versoes/1/narrativa", json={**base, "resumo": trecho}, headers=_sec(cliente))
        assert resposta.status_code == 422 and motivo in resposta.json()["detail"], trecho
    em_incerteza = {**base, "incertezas": [f"Obra na {escola.nome} depende de licitação."]}
    assert cliente.put(f"{URL}/versoes/1/narrativa", json=em_incerteza, headers=_sec(cliente)).status_code == 422

    versao = cliente.get(f"{URL}/versoes/1", headers=_sec(cliente)).json()
    assert versao["narrativa"]["editada"] is False and versao["narrativa"]["resumo"] == _resposta()["resumo"]
    assert cliente.put(f"{URL}/versoes/1/narrativa", json=base, headers=_sec(cliente)).status_code == 200


def test_pdf_da_narrativa_sem_escola_nem_texto_das_acoes(ambiente, monkeypatch):
    from app.features.acesso import censo
    from tests.test_documentos_pdf import _eventos, _texto

    cliente, diretora, _ = ambiente
    assert cliente.get(f"{URL}/versoes/1/narrativa/pdf", headers=_sec(cliente)).status_code == 404
    _gerada(cliente, diretora, monkeypatch)
    assert cliente.get(f"{URL}/versoes/1/narrativa/pdf", headers=diretora).status_code == 403

    chamadas = []
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", lambda *a, **k: chamadas.append(a))])
    resposta = cliente.get(f"{URL}/versoes/1/narrativa/pdf", headers=_sec(cliente))
    texto = _texto(resposta)
    assert chamadas == []
    assert resposta.headers["content-disposition"].endswith('_v1.pdf"') and "narrativa-executiva_" in resposta.headers["content-disposition"]
    for esperado in ("Narrativa executiva do Plano Estratégico Municipal — versão 1", "apoio à decisão orçamentária",
                     "A rede enfrenta falta de atendimento especializado", "Frente 1", "Escolas municipais atendidas",
                     "Estimativa registrada pela secretaria", "Escrito pelo assistente de IA, sem revisão", "Custos ainda a estimar."):
        assert esperado in texto, esperado
    escola = censo.escola(_co_entidade(cliente, diretora))
    for proibido in (escola.nome, "Contratar profissionais de AEE", "Dotação aprovada", "120.000", "Uso interno"):
        assert proibido not in texto, proibido
    assert _eventos()[-1].alvo_tipo == "narrativa_plano_municipal" and _eventos()[-1].resultado == "ok"


def test_pdf_recusa_narrativa_gravada_com_nome_da_rede(ambiente, monkeypatch):
    """Narrativa editada antes da checagem ao salvar: o PDF confere de novo (RN-PDF-09)."""
    from app.features.plano_municipal.modelos import NarrativaPlanoMunicipal
    from app.shared import banco_gestao
    from tests.test_documentos_pdf import _eventos

    cliente, diretora, _ = ambiente
    _gerada(cliente, diretora, monkeypatch)
    sessao = next(banco_gestao.obter_sessao())
    try:
        registro = sessao.query(NarrativaPlanoMunicipal).one()
        registro.conteudo = {**registro.conteudo, "situacao": "Em Niterói a barreira é comum."}
        sessao.commit()
    finally:
        sessao.close()
    resposta = cliente.get(f"{URL}/versoes/1/narrativa/pdf", headers=_sec(cliente))
    assert resposta.status_code == 409 and "Edite o texto" in resposta.json()["detail"]
    assert "Niterói" not in resposta.text
    assert _eventos()[-1].resultado == "recusado"


# --- Revisão do AgLGPD do PDF da narrativa (2026-11-03) -------------------------------------------

def test_estudante_descrito_com_a_condicao_e_recusado():
    """A1: dado de saúde de pessoa identificável não sai no texto para fora da secretaria."""
    for texto in ("Um estudante cego precisa de material em braile.", "Uma aluna surda depende de intérprete.",
                  "A aluna com autismo precisa de apoio.", "O aluno cadeirante não entra na sala.",
                  "Esse estudante, que tem laudo de TEA, ficou sem AEE."):
        assert narrativa.problema([texto], SEM_LOCAIS) == "estudante", texto
    for texto in ("Estudantes surdos da rede precisam de intérprete.", "O estudante com deficiência tem direito ao AEE.",
                  "A criança com deficiência deve estar na classe comum."):
        assert narrativa.problema([texto], SEM_LOCAIS) is None, texto


def test_contagem_por_extenso_e_unica_escola_sao_recusadas():
    """M2: "a única escola com classe exclusiva", junto do Censo, aponta a escola."""
    for texto in ("A única escola com classe exclusiva precisa de apoio.", "Duas escolas atendem estudantes surdos.",
                  "Apenas uma turma tem intérprete.", "Três professores fazem o AEE."):
        assert narrativa.problema([texto], SEM_LOCAIS) == "numero", texto
    for texto in ("O plano quer uma rede inclusiva.", "Cada estudante tem direito a uma escola acessível."):
        assert narrativa.problema([texto], SEM_LOCAIS) is None, texto


def test_bairro_de_uma_palavra_so_na_conferencia_do_que_sai():
    """M1: bairro de uma palavra entra só na conferência do texto que sai, e só com maiúscula."""
    from app.shared.guardiao_lgpd import nomes_da_rede

    para_ia = nomes_da_rede("Rio de Janeiro", [], ["Jacarepaguá", "Centro"])
    para_fora = nomes_da_rede("Rio de Janeiro", [], ["Jacarepaguá", "Centro"], bairros_curtos=True)
    assert narrativa.problema(["No Jacarepaguá a barreira é comum."], para_ia) is None
    assert narrativa.problema(["No Jacarepaguá a barreira é comum."], para_fora) == "local"
    assert narrativa.problema(["No Centro a barreira é comum.", "O centro da estratégia é o AEE."], para_fora) is None


def test_lacunas_editaveis_e_conferidas(ambiente, monkeypatch):
    """B2: a lacuna da IA também é texto do PDF e o secretário consegue revisá-la."""
    cliente, diretora, _ = ambiente
    _gerada(cliente, diretora, monkeypatch)
    base = {"resumo": "Resumo revisto.", "estrategia": [{"texto": "Atendimento especializado.", "acoes": ["A1"]}]}

    mantidas = cliente.put(f"{URL}/versoes/1/narrativa", json=base, headers=_sec(cliente)).json()
    assert mantidas["narrativa"]["lacunas"] == _resposta()["lacunas"]  # cliente sem o campo mantém as gravadas
    ruim = cliente.put(f"{URL}/versoes/1/narrativa", json={**base, "lacunas": ["Falta norma para as duas escolas."]}, headers=_sec(cliente))
    assert ruim.status_code == 422 and "lacunas" in ruim.json()["detail"]
    novas = cliente.put(f"{URL}/versoes/1/narrativa", json={**base, "lacunas": ["Sem norma sobre transporte."]}, headers=_sec(cliente))
    assert novas.json()["narrativa"]["lacunas"] == ["Sem norma sobre transporte."]


def test_pdf_nao_mostra_alcance_nem_contagem_pequena():
    """B1: ação retida aparece como localizada e poucas escolas viram "menos de N"."""
    from app.features.plano_municipal import documento

    restricoes = narrativa.Restricoes(nomes=SEM_LOCAIS, pequenas=frozenset({1}), retiradas=frozenset({2}))
    retida = {"codigos": ["B-I-01"], "escolas": [{"co_entidade": 2}]}
    comum = {"codigos": ["B-I-01"], "escolas": [{"co_entidade": e} for e in (3, 4, 5)]}
    assert documento._alcance(retida, restricoes) == "Ação localizada"
    assert documento._alcance(comum, restricoes) == "Nas escolas da rede"
    assert documento._alcance({"codigos": ["B-I-01"]}, restricoes) == "Ação da rede, sem escola específica"
    assert [documento._poucas(n) for n in (0, 1, 2, 3, 40)] == ["0", "menos de 3", "menos de 3", "3", "40"]
