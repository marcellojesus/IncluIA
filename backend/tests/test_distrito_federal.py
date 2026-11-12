"""Distrito Federal na Gestão Ativa (decisão de 2026-11-09).

O DF não tem municípios nem rede municipal: Brasília (5300108) é o único código IBGE, e as escolas
da Secretaria de Educação do DF aparecem no Censo como "Estadual". No DF, a rede atendida é essa rede
distrital; escolas federais e privadas continuam fora, e o escopo do secretário não cruza com outros
municípios.
"""

from app.database import get_connection
from app.features.acesso import censo, servico
from app.shared import banco_gestao
from tests.test_acesso_gestao import NITEROI, _auth, _entrar, _pendente_id, _sessao_secretario, _solicitar, ambiente  # noqa: F401

BRASILIA = 5300108
ESCOLA_DF = 53003578  # CED 02 de Taguatinga, rede distrital ("Estadual" no Censo)
FEDERAL_DF = 53001354  # Colégio Militar de Brasília
PRIVADA_DF = 53000013
SEC_DF = "sec@se.df.gov.br"


def _escolas(co_municipio, rede, com_score=False):
    conn = get_connection()
    try:
        filtro = " AND score IS NOT NULL" if com_score else ""
        return conn.execute(f"SELECT COUNT(*) FROM escolas WHERE co_municipio = ? AND rede = ?{filtro}", (co_municipio, rede)).fetchone()[0]
    finally:
        conn.close()


def _provisionar_df():
    sessao = next(banco_gestao.obter_sessao())
    admin = servico._conta_por_email(sessao, "admin@teste.gov.br")
    servico.provisionar_secretario(sessao, admin=admin, nome="Sec DF", email=SEC_DF, co_municipio=BRASILIA, categoria="oficio", metodo="Ofício da SEEDF, teste")
    sessao.close()


def test_rede_da_gestao_por_municipio():
    assert censo.rede_da_gestao(BRASILIA) == "Estadual"
    assert censo.rede_da_gestao(NITEROI) == "Municipal"
    assert censo.eh_distrito_federal(BRASILIA) and not censo.eh_distrito_federal(NITEROI)
    assert censo.rotulos_da_rede(BRASILIA).secretaria == "Secretaria de Estado de Educação do Distrito Federal"
    assert censo.rotulos_da_rede(NITEROI).secretaria == "Secretaria Municipal de Educação"
    # Premissa da decisão: o DF não tem rede municipal no Censo.
    assert _escolas(BRASILIA, "Municipal") == 0 and _escolas(BRASILIA, "Estadual") > 0


def test_diretor_distrital_pede_acesso_e_federal_ou_privada_nao(ambiente):
    cliente, _ = ambiente
    assert _solicitar(cliente, escola=ESCOLA_DF).status_code == 202
    for escola in (FEDERAL_DF, PRIVADA_DF):
        resposta = _solicitar(cliente, email=f"d{escola}@escola.gov.br", escola=escola)
        assert resposta.status_code == 422
        assert "rede distrital" in resposta.json()["detail"]
    privada = _solicitar(cliente, email="dp@escola.gov.br", escola=PRIVADA_DF).json()["detail"]
    assert "Brasília/DF) na rede privada" in privada


def test_recusa_fora_do_df_diz_a_rede_da_escola_e_nao_cita_o_df(ambiente):
    cliente, _ = ambiente
    maranata = 17054486  # escola privada de Palmas/TO
    detalhe = _solicitar(cliente, email="dm@escola.gov.br", escola=maranata).json()["detail"]
    assert detalhe == (
        "O Censo Escolar 2025 registra esta escola (Palmas/TO) na rede privada. "
        "Neste piloto, a Gestão Ativa atende só escolas da rede municipal."
    )


def test_secretario_do_df_aprova_e_o_de_outro_municipio_nao_ve(ambiente):
    cliente, codigos = ambiente
    _provisionar_df()
    _solicitar(cliente, escola=ESCOLA_DF)
    cliente.post("/gestao/acesso/entrar", json={"email": "diretora@escola.gov.br", "codigo": codigos["diretora@escola.gov.br"]})

    niteroi = _sessao_secretario(cliente, codigos)
    assert cliente.get("/gestao/secretario/vinculos", headers=niteroi).json() == []

    df = _sessao_secretario(cliente, codigos, SEC_DF)
    pedido_id = _pendente_id(cliente, df)
    negado = cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": "Portaria 12/2026"}, headers=niteroi)
    assert negado.status_code == 404
    aprovado = cliente.post(f"/gestao/secretario/vinculos/{pedido_id}/aprovar", json={"categoria": "outro", "texto": "Portaria 12/2026"}, headers=df)
    assert aprovado.status_code == 200

    diretora = _auth(_entrar(cliente, codigos, "diretora@escola.gov.br")["token"])
    painel = cliente.get("/gestao/diretor/escola", headers=diretora).json()
    assert painel["coEntidade"] == ESCOLA_DF and painel["uf"] == "DF"


def test_telas_do_secretario_do_df_cobrem_a_rede_distrital(ambiente):
    cliente, codigos = ambiente
    _provisionar_df()
    df = _sessao_secretario(cliente, codigos, SEC_DF)
    distritais = _escolas(BRASILIA, "Estadual")

    declaracoes = cliente.get("/gestao/secretario/declaracoes", headers=df).json()
    assert declaracoes["escolasMunicipais"] == distritais and declaracoes["uf"] == "DF"
    dashboard = cliente.get("/gestao/secretario/dashboard", headers=df).json()
    assert dashboard["cobertura"]["escolasMunicipais"] == _escolas(BRASILIA, "Estadual", com_score=True)
    assert cliente.get("/gestao/secretario/analitico", headers=df).json()["escolasMunicipais"] == distritais
    assert cliente.get("/gestao/secretario/plano-municipal", headers=df).json()["escolasMunicipais"] == distritais

    # O secretário de Niterói continua vendo só a rede municipal dele.
    niteroi = _sessao_secretario(cliente, codigos)
    assert cliente.get("/gestao/secretario/declaracoes", headers=niteroi).json()["escolasMunicipais"] == _escolas(NITEROI, "Municipal")
