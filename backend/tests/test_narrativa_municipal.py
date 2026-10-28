"""Spec: RF-30 do PRD da Fase 2; SPM-RF-05 e 06 em requirements/secretario/plano-estrategico-municipal.md; RN-SPM-04."""

from app.features.plano_municipal import narrativa
from app.shared import ai_client
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
    assert narrativa.MARCADOR_LOCAL in enviado


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
    restricoes = narrativa.Restricoes(nomes=[], pequenas=frozenset({1}), retiradas=frozenset({2}))
    acao = {"acao": "Texto que descreve a situação da escola.", "codigos": ["B-IV-01"], "horizonte": "LOA",
            "escolas": [{"co_entidade": 1, "cobertura": "parcial"}]}
    assert narrativa.motivo_restricao(acao, restricoes) == "escola_pequena"
    linha = narrativa._linha(1, acao, 40, restricoes)
    assert "Texto que descreve" not in linha and "ação localizada" in linha and "parcial" not in linha

    retirada = {**acao, "codigos": ["B-I-01"], "escolas": [{"co_entidade": 2}, {"co_entidade": 3}, {"co_entidade": 4}]}
    assert narrativa.motivo_restricao(retirada, restricoes) == "retirada_lgpd"
    comum = {**retirada, "escolas": [{"co_entidade": 3}, {"co_entidade": 4}, {"co_entidade": 5}]}
    assert narrativa.motivo_restricao(comum, restricoes) is None


def test_nomes_da_rede_saem_com_e_sem_prefixo_e_sem_acento():
    nomes = narrativa.nomes_da_rede("Lucas do Rio Verde", ["EMEF Santa Rita", "Escola Municipal de Ensino Fundamental São João Batista"])
    texto = "Na Escola Santa Rita e na SAO JOÃO BATISTA, em Lucas do Rio Verde (código 51234567)."
    limpo = narrativa.sem_nomes(texto, nomes)
    for proibido in ("Santa Rita", "JOÃO BATISTA", "Lucas", "51234567"):
        assert proibido not in limpo, proibido
    assert narrativa.sem_nomes("Formação para a rede.", nomes) == "Formação para a rede."
