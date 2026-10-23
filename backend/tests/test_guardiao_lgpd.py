"""Spec: docs/sdd/fase-2/arquitetura.md AD-05 — nada de dado pessoal passa sem máscara ou bloqueio."""

import logging

import pytest

from app.shared.guardiao_lgpd import TextoProtegido, proteger


def mascarado(texto: str) -> str:
    return proteger(texto).texto_mascarado


# --- Camada 1: documentos e contatos -----------------------------------------------------------

@pytest.mark.parametrize(
    "texto, motivo",
    [
        ("O CPF da mãe é 529.982.247-25.", "CPF"),
        ("CPF 52998224725 cadastrado", "CPF"),
        ("RG 12.345.678-9 do responsável", "RG"),
        ("rg: 1234567 SSP", "RG"),
        ("NIS 123.45678.90-1", "NIS"),
        ("cartão do SUS 898 0012 3456 7890", "CARTAO_SUS"),
    ],
)
def test_documento_de_identificacao_bloqueia(texto, motivo):
    resultado = proteger(texto)
    assert resultado.bloqueado
    assert resultado.texto_protegido is None
    assert motivo in resultado.motivos_bloqueio


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Ligue para (61) 98765-4321.", "Ligue para [TELEFONE]."),
        ("Contato 61 98765-4321", "Contato [TELEFONE]"),
        ("whatsapp 61987654321", "whatsapp [TELEFONE]"),
        ("e-mail: fulano.tal@gmail.com", "e-mail: [EMAIL]"),
        ("nascido em 12/03/2015, ainda não lê", "nascido em [DATA_NASCIMENTO], ainda não lê"),
        ("Data de nascimento: 3 de março de 2016", "Data de nascimento: [DATA_NASCIMENTO]"),
        ("matrícula nº 2024-0153 na secretaria", "matrícula nº [MATRICULA] na secretaria"),
        ("ID INEP do aluno 123456789012", "ID INEP do aluno [MATRICULA]"),
        ("o número 123456789012 aparece no Educacenso", "o número [ID_ESTUDANTE] aparece no Educacenso"),
    ],
)
def test_contato_e_registro_sao_mascarados(texto, esperado):
    resultado = proteger(texto)
    assert not resultado.bloqueado
    assert resultado.texto_mascarado == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "A escola de código INEP 53012345 fica no município 5300108.",
        "O prazo da ação vai até 30/06/2027.",
        "A matrícula no AEE caiu de 2024 para 2025.",
        "Temos 3 turmas do 5º ano sem intérprete de Libras.",
    ],
)
def test_dado_publico_ou_agregado_passa_intacto(texto):
    assert mascarado(texto) == texto


# --- Camada 2: nomes ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "texto, nome",
    [
        ("A professora Maria José disse que o AEE está parado.", "Maria José"),
        ("Falei com a aluna Ana Clara sobre a sala de recursos.", "Ana Clara"),
        ("pedro do 3o ano não tem intérprete", "pedro"),
        ("Joao chegou ontem e precisa de apoio.", "Joao"),
        ("O menino se chama Davi e usa cadeira de rodas.", "Davi"),
    ],
)
def test_nome_de_pessoa_e_mascarado(texto, nome):
    resultado = mascarado(texto)
    assert nome not in resultado
    assert "[NOME]" in resultado


def test_termos_do_dominio_nao_sao_confundidos_com_nomes():
    texto = "Falta revisor de Braille, intérprete de Libras e oferta de AEE conforme a PNEEI e o Censo."
    assert mascarado(texto) == texto


# --- Camada 3: contexto escolar ----------------------------------------------------------------

def test_exemplo_do_diagrama():
    resultado = proteger("O Pedro, do 3º ano, é cego e não temos material em Braille. Que ação proponho?")
    assert not resultado.bloqueado
    assert resultado.texto_mascarado == "O [NOME], do [TURMA], é cego e não temos material em Braille. Que ação proponho?"


def test_unico_estudante_com_deficiencia_na_turma():
    texto = "O único estudante surdo do 5º ano B não tem intérprete."
    assert mascarado(texto) == "O [ESTUDANTE] surdo do [TURMA] não tem intérprete."


def test_unico_sem_substantivo():
    assert mascarado("Ela é a única cadeirante da turma 7A.") == "Ela é a [ESTUDANTE] cadeirante da [TURMA]."


def test_idade_de_estudante_com_deficiencia():
    assert mascarado("O aluno autista de 8 anos fica sem apoio.") == "O aluno autista de [IDADE] fica sem apoio."


def test_deficiencia_em_grupo_nao_e_mascarada():
    texto = "Os alunos cegos do 4º ano usam material ampliado."
    assert mascarado(texto) == texto


@pytest.mark.parametrize(
    "texto",
    [
        "O aluno do 2º ano tem laudo de autismo.",
        "A Beatriz toma medicação controlada.",
        "Uma aluna teve crise convulsiva na sala.",
        "Estudante com CID F84.0 sem acompanhamento.",
    ],
)
def test_dado_de_saude_individual_bloqueia(texto):
    resultado = proteger(texto)
    assert resultado.bloqueado
    assert "SAUDE" in resultado.motivos_bloqueio


def test_saude_em_grupo_nao_bloqueia():
    resultado = proteger("Muitos alunos chegam sem laudo e a rede exige diagnóstico para o AEE.")
    assert not resultado.bloqueado


# --- Garantias do componente -------------------------------------------------------------------

def test_texto_protegido_so_e_criado_pelo_guardiao():
    with pytest.raises(TypeError):
        TextoProtegido("texto cru")


def test_texto_protegido_carrega_o_texto_mascarado():
    resultado = proteger("A aluna Ana Clara usa cadeira de rodas.")
    assert str(resultado.texto_protegido) == resultado.texto_mascarado
    assert "Ana" not in repr(resultado.texto_protegido)


def test_log_e_resumo_nao_guardam_o_dado_original(caplog):
    caplog.set_level(logging.INFO, logger="guardiao_lgpd")
    resultado = proteger("O Pedro, do 3º ano, é cego. CPF 529.982.247-25, fone (61) 98765-4321.")
    registros = " ".join(r.getMessage() for r in caplog.records)
    for dado in ("Pedro", "3º ano", "529.982.247-25", "98765-4321"):
        assert dado not in registros
        assert dado not in str(resultado.resumo())
    assert resultado.resumo() == {"NOME": 1, "TURMA": 1, "CPF": 1, "TELEFONE": 1}
