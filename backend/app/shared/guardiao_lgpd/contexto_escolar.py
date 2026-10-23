"""Camada 3 do Guardião LGPD (AD-05): identificação indireta e dados sensíveis no contexto escolar.

Atua por sentença, quando ela fala de UM estudante (nome, "o aluno", "a única estudante", "1 aluno"):
- deficiência + turma, ano ou idade → mascara turma, ano e idade; a deficiência fica, porque a IA
  precisa dela para propor a ação;
- saúde (laudo, medicamento, doença, terapia) ou situação sensível (abuso, gravidez, Conselho
  Tutelar) → bloqueia o envio.
Em qualquer sentença: código CID bloqueia; endereço e CEP de quem "mora" ou "reside" são mascarados.
Frases sobre grupos ("muitos alunos chegam sem laudo") passam.
"""

import re

from app.shared.guardiao_lgpd.texto import Trecho, normalizar, sentencas

_ESTUDANTE = r"(?:alun[oa]|estudante|crianca|menin[oa])"
_UNICO = re.compile(
    rf"\b(?:unic[oa]s?\s+{_ESTUDANTE}|um[a]? unic[oa]\s+{_ESTUDANTE}|"
    rf"(?:so|apenas)\s+(?:[a-z]+\s+){{0,2}}(?:um[a]?|1)\s+{_ESTUDANTE})\b"
)
_DEFICIENCIA = (
    r"(?:ceg[oa]|surd[oa]|surdoceg[oa]|autista|autismo|tea\b|tdah|deficiencia|deficiente|cadeirante|"
    r"baixa visao|sindrome de down|down\b|paralisia cerebral|altas habilidades|superdota\w*|"
    r"mobilidade reduzida|nao verbal|nao fala|nao enxerga|nao ouve)"
)
_UNICO_SEM_SUBSTANTIVO = re.compile(rf"\b(unic[oa])\s+(?={_DEFICIENCIA})")
_TEM_DEFICIENCIA = re.compile(rf"\b{_DEFICIENCIA}")
_INDIVIDUO = re.compile(
    r"\b(?:o|a|um|uma|1|meu|minha|esse|essa|este|esta|nosso|nossa|aquele|aquela)\s+"
    r"(?:alun[oa]|estudante|crianca|menin[oa]|filh[oa])\b(?!s)"
)
_TURMA = [
    re.compile(r"\bturma\s+(?:d[oa]\s+)?(?:\d{1,2}\s?[ºª°o]?\s?[a-z]?|[a-z])(?![a-z0-9])"),
    re.compile(r"\b\d{1,2}\s?[ºª°oa]?\s*(?:ano|serie)\b(?:\s+[a-z]\b)?"),
    re.compile(r"(?<![\w])\d{1,2}\s?[ºª°]\s?[a-z](?![a-z0-9])"),  # "8º B", "8ºB"
    re.compile(r"\b(?:primeiro|segundo|terceiro|quarto|quinto|sexto|setimo|oitavo|nono)\s+ano\b(?:\s+[a-z]\b)?"),
]
_IDADE = re.compile(r"\b(?:de|tem|com|aos)\s+(\d{1,2}\s+anos)\b")

_MEDICAMENTOS = (
    r"ritalina|concerta|metilfenidato|venvanse|lisdexanfetamina|risperidona|rispiridona|aripiprazol|"
    r"fluoxetina|sertralina|escitalopram|imipramina|carbamazepina|oxcarbazepina|trileptal|valproato|"
    r"depakene|depakote|fenobarbital|gardenal|clonazepam|rivotril|diazepam|topiramato|levetiracetam|"
    r"keppra|lamotrigina|quetiapina|haloperidol|haldol|melatonina|insulina|canabidiol|cbd"
)
_SAUDE = re.compile(
    r"\b(?:laudo|laudad[oa]|"
    r"diagnostic(?:o|os|ad[oa]s?|ou)(?![a-z])(?!\s+(?:pedagogic|de acessibilidade|da escola|escolar|de barreiras|do municipio|da rede|ia\b))|"
    r"relatorio medico|atestado|medicac\w*|medicament\w*|remedio\w*|" + _MEDICAMENTOS + r"|\d+\s?mg\b|"
    r"em tratamento|faz tratamento|tratamento (?:medico|psicologic|psiquiatric|com)\w*|"
    r"internad[oa]|internacao|hospital\w*|"
    r"crises?\s+(?:convulsiv|epilep|de ausencia|de ansiedade|de panico|nervos|asmatic)\w*|convuls\w*|"
    r"epilep\w*|hiv|aids|soropositiv\w*|diabet\w*|asma\w*|cancer|leucemia|hepatite|tuberculose|"
    r"depress\w*|bipolar|esquizofren\w*|transtorno\w*(?! do espectro))"
)
# Profissional ou serviço de saúde: é dado de saúde quando atende o estudante ("faz acompanhamento
# com a psicóloga", "é atendido no CAPS"), mas não quando falta na escola ("não tem psicólogo"),
# que é um obstáculo típico da Declaração.
_ATENDIMENTO_SAUDE = re.compile(
    r"\b(?:neurolog|neuropediatr|psiquiatr|psicolog|psicoterap|fono|terapi|terapeut|caps)\w*"
)
_AUSENCIA = re.compile(
    r"(?:nao tem|nao ha|nao possui|nao oferece|nao conta com|falta\w*|sem|contratar|contratacao de)"
    r"\s+(?:[a-z]+\s+){0,2}$"
)
_SENSIVEL = re.compile(
    r"\b(?:abus\w*|violencia sexual|violentad[oa]|estupr\w*|assedi\w*|gravid\w*|gestante|"
    r"medida protetiva|conselho tutelar|maus[- ]tratos|negligenciad[oa]|acolhimento institucional|"
    r"abrigad[oa]|ato infracional|liberdade assistida|socioeducativ\w*|"
    # Vulnerabilidade social (decisão de 2026-10-23: bloqueia, o diretor reescreve). "Preso" só com
    # familiar, para não pegar "ficou preso no banheiro" (obstáculo de acessibilidade).
    r"(?:pai|mae|pais|irmao|irma|responsavel|familia|padrasto|madrasta|tio|tia|avo)\s+(?:[a-z]+\s+){0,2}"
    r"(?:pres[oa]s?|detid[oa]s?|reclus[oa]s?)\b|presidiari\w*|sistema prisional|cumpr\w* pena|"
    r"(?:vive|mora|esta|morando|vivendo)\s+(?:em|num|no|na)\s+(?:um\s+)?abrigo|situacao de rua|"
    r"bullying|trabalho infantil|passa fome|violencia domestica|agredid[oa]|apanha\w*|"
    r"dependente quimic\w*|dependencia quimica|usuari[oa] de drogas|alcoolismo|alcoolatra)"
)
_CID = re.compile(r"\bcid\s*-?\s*(?:10|11)?\s*:?\s*[a-z]\d{2}\.?\d?\b|\b[fgq]\d{2}(?:\.\d)?\b")

_MORADIA = re.compile(r"\b(?:mora|moram|morando|reside|residente|endereco|cep|vive na|vive no)\b")
_ENDERECO = re.compile(
    r"\b(?:rua|r\.|av\.?|avenida|travessa|tv\.|alameda|quadra|qd\.?|conjunto|conj\.?|qnm|qnn|qr|setor|"
    r"casa|apto\.?|apartamento|lote|lt\.?|bloco|chacara|fazenda|sitio|condominio)\s+[^,.;\n]+"
)
_CEP = re.compile(r"(?<!\d)\d{5}-?\d{3}(?!\d)")


def _sobrepoe(inicio: int, fim: int, trechos: list[Trecho]) -> bool:
    return any(t.inicio < fim and inicio < t.fim for t in trechos)


def encontrar(texto: str, nomes: list[Trecho]) -> list[Trecho]:
    norm = normalizar(texto)
    trechos: list[Trecho] = []

    for m in _CID.finditer(norm):
        trechos.append(Trecho(m.start(), m.end(), "SAUDE", "[SAUDE]", "bloquear"))

    for inicio, fim in sentencas(texto):
        frase = norm[inicio:fim]

        def marcar(m: re.Match, tipo: str, acao: str = "mascarar", grupo: int = 0) -> None:
            trechos.append(Trecho(inicio + m.start(grupo), inicio + m.end(grupo), tipo, f"[{tipo}]", acao))

        if _MORADIA.search(frase):
            for m in _ENDERECO.finditer(frase):
                marcar(m, "ENDERECO")
            for m in _CEP.finditer(frase):
                marcar(m, "ENDERECO")

        unicos = list(_UNICO.finditer(frase))
        for m in unicos:
            marcar(m, "ESTUDANTE")
        unicos_sem_substantivo = list(_UNICO_SEM_SUBSTANTIVO.finditer(frase))
        for m in unicos_sem_substantivo:
            marcar(m, "ESTUDANTE", grupo=1)
        unicos += unicos_sem_substantivo

        individual = bool(unicos) or _sobrepoe(inicio, fim, nomes) or bool(_INDIVIDUO.search(frase))
        if not individual:
            continue

        if _TEM_DEFICIENCIA.search(frase):
            for padrao in _TURMA:
                for m in padrao.finditer(frase):
                    marcar(m, "TURMA")
            for m in _IDADE.finditer(frase):
                marcar(m, "IDADE", grupo=1)

        for m in _SAUDE.finditer(frase):
            marcar(m, "SAUDE", "bloquear")
        for m in _ATENDIMENTO_SAUDE.finditer(frase):
            if not _AUSENCIA.search(frase[max(0, m.start() - 40) : m.start()]):
                marcar(m, "SAUDE", "bloquear")
        for m in _SENSIVEL.finditer(frase):
            marcar(m, "SENSIVEL", "bloquear")

    return trechos
