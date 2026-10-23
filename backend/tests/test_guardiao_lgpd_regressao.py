"""Regressão do Guardião LGPD com os casos da revisão do AgLGPD (2026-10-23).

Serve de base para a decisão pendente 1 do AD-05 (taxa de detecção): cada caso novo encontrado em
relato real entra aqui, como positivo (deve mascarar ou bloquear) ou negativo (deve passar).
"""

import pytest

from app.shared.guardiao_lgpd import GuardiaoIndisponivel, proteger
from app.shared.guardiao_lgpd import nomes

BLOQUEIA = [
    # saúde sem a palavra "laudo"
    "O aluno tem deficiência intelectual e toma Ritalina.",
    "O estudante tem TDAH e usa Concerta 36mg.",
    "O menino usa risperidona e fica agitado.",
    "A aluna tem epilepsia.",
    "A criança é soropositiva.",
    "O aluno faz acompanhamento no CAPSi com a psicóloga.",
    "A aluna faz tratamento com fonoaudióloga e psicóloga.",
    "A estudante com TEA do 2º ano A toma Ritalina.",
    "O aluno tem diagnóstico fechado.",
    # situações sensíveis
    "O aluno sofreu abuso sexual em casa.",
    "A aluna está grávida.",
    "Acionamos o Conselho Tutelar para a menina.",
    # vulnerabilidade social (decisão de 2026-10-23: bloqueia)
    "O menino é filho de pais presos.",
    "A aluna é autista e o pai está preso.",
    "O aluno vive em abrigo e é surdo.",
    "A aluna é cega, filha de mãe solteira, sofre bullying.",
    "O aluno está em situação de rua.",
    "A menina apanha em casa.",
    # CAPS (segunda revisão)
    "O aluno faz acompanhamento no CAPSi.",
    "O aluno faz acompanhamento no CAPS infantil.",
    "O CAPS infantil atende a aluna surda.",
    "O aluno é atendido pela neurologista do posto.",
    # CID sem rótulo ou sem ponto
    "cid-10 f840",
    "CID10 F840",
    "F84.0",
    "F84 confirmado pela neurologista",
    # documentos com formatação comum
    "CPF 529 982 247 25",
    "CPF 529.982.247 25",
    "CPF: 123.456.789/09",
    "R.G.: 1234567",
    "RG: MG-12.345.678",
    "registro geral 45678901",
    "Identidade nº 4.567.890",
    "passaporte FZ123456",
    "certidão de nascimento 123456 01 55 2015 1 00012 123 1234567 12",
]


@pytest.mark.parametrize("texto", BLOQUEIA)
def test_bloqueia(texto):
    assert proteger(texto).bloqueado


MASCARA = [
    # nomes fora do padrão "Nome Sobrenome"
    ("O João tem autismo e está no 5º ano B.", ["João", "5º ano"]),
    ("MARIA EDUARDA DOS SANTOS faltou.", ["MARIA", "EDUARDA", "SANTOS"]),
    ("maria eduarda dos santos faltou.", ["maria", "eduarda", "santos"]),
    ("ANA faltou de novo.", ["ANA"]),
    ("O PEDRO do 3º ano é surdo.", ["PEDRO", "3º ano"]),
    ("o joaozinho do 2 ano é autista", ["joaozinho", "2 ano"]),
    ("a aluna maria eduarda tem autismo e é do 5º ano.", ["maria", "eduarda", "5º ano"]),
    # turma e "único" em variações
    ("O aluno do 8º B é cadeirante.", ["8º B"]),
    ("Na turma do 8ºB há um estudante cadeirante.", ["8ºB"]),
    ("Temos 1 aluno autista no 7º ano C.", ["7º ano C"]),
    ("Só tem uma criança surda na escola.", ["uma criança"]),
    # endereço de quem mora
    ("O aluno mora na Rua 7, casa 12, Setor Leste.", ["Rua 7", "casa 12", "Setor Leste"]),
    ("Ela mora na Rua das Flores, 123, apto 45, Ceilândia.", ["Rua das Flores"]),
    ("CEP 72215-120 da família", ["72215-120"]),
    # rótulos que faltavam
    ("email joao.silva arroba gmail.com", ["joao.silva", "gmail"]),
    ("aniversário dia 12/05", ["12/05"]),
    ("mat. 556677", ["556677"]),
    # CPF com dígito verificador errado e sem rótulo
    ("o número 12345678901 foi informado", ["12345678901"]),
]


@pytest.mark.parametrize("texto, nao_pode_aparecer", MASCARA)
def test_mascara(texto, nao_pode_aparecer):
    resultado = proteger(texto)
    for trecho in nao_pode_aparecer:
        assert trecho not in resultado.texto_mascarado, resultado.resumo()


PASSA = [
    "O aluno precisa de um diagnóstico pedagógico da sala de recursos.",
    "Fizemos o diagnóstico de acessibilidade com o aluno cadeirante.",
    "O aluno chegou em meio à crise da merenda.",
    "Muitos alunos chegam sem laudo.",
    "A escola fica na Rua 7, Setor Leste, e não tem rampa.",
    "Secretaria de Educação do DF e Censo Escolar 2025.",
    "Temos 3 turmas do 5º ano sem intérprete de Libras.",
    "O estudante com TEA precisa de profissional de apoio.",
    # falta de profissional de saúde na escola é obstáculo, não dado de saúde (segunda revisão)
    "O aluno precisa de acompanhamento e a escola não tem psicólogo.",
    "A escola não tem fonoaudióloga para atender o aluno surdo.",
    "Faltam psicólogos e fonoaudiólogos para atender os alunos.",
    "O aluno cadeirante ficou preso no banheiro sem barra de apoio.",
    "A escola tem casos de bullying e precisa de formação.",
]

# Nomes públicos (municípios, escolas, leis, autores) e palavras comuns não viram [NOME].
INTACTO = [
    "A escola fica em São Paulo e atende 40 estudantes.",
    "A rede de Santa Catarina ampliou o AEE.",
    "São José dos Campos ampliou o AEE.",
    "São Luís precisa de mais intérpretes.",
    "O município de Santa Maria abriu concurso.",
    "Lucas do Rio Verde abriu sala de recursos.",
    "Escola Estadual Paulo Freire não tem rampa.",
    "EMEF Maria Luiza de Souza não tem banheiro adaptado.",
    "Escola Municipal Dom Pedro II",
    "A Lei Maria da Penha e a LBI se aplicam.",
    "Eu caio de bicicleta todo dia.",
    "A ferida sara em dois dias.",
    "O tratamento de dados segue a LGPD.",
    "Segundo a LGPD, a SEEDF deve responder.",
]


@pytest.mark.parametrize("texto", INTACTO)
def test_nome_publico_ou_palavra_comum_fica_intacto(texto):
    assert proteger(texto).texto_mascarado == texto


def test_dona_continua_sendo_pessoa():
    assert "Maria" not in proteger("A dona Maria, avó do aluno, buscou o material.").texto_mascarado


@pytest.mark.parametrize("texto", PASSA)
def test_passa_sem_bloqueio(texto):
    resultado = proteger(texto)
    assert not resultado.bloqueado, resultado.resumo()


def test_texto_do_dominio_passa_intacto():
    texto = "A escola fica na Rua 7, Setor Leste, e não tem rampa."
    assert proteger(texto).texto_mascarado == texto


def test_modelo_sem_reconhecimento_de_pessoas_falha_fechado(monkeypatch):
    import spacy

    nomes._modelo.cache_clear()
    monkeypatch.setattr(spacy, "load", lambda *a, **k: spacy.blank("pt"))
    try:
        with pytest.raises(GuardiaoIndisponivel):
            proteger("Pedro Henrique faltou.")
    finally:
        monkeypatch.undo()
        nomes._modelo.cache_clear()


def test_repr_do_resultado_nao_carrega_texto():
    resultado = proteger("A aluna Ana Clara usa cadeira de rodas.")
    assert "Ana" not in repr(resultado)
    assert "cadeira" not in repr(resultado)
