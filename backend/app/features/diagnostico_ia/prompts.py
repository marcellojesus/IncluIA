"""Spec: docs/requirements/diagnostico-ia.md §"Estratégia de IA", docs/business-rules/diagnostico-ia.md.

RN-03: a IA nunca decide o veredito (status ok/warn/nok) — só recebe o veredito já calculado e
o explica. RN-04: só dados agregados e públicos entram no prompt, nunca dado pessoal de aluno/
professor. RN-06 (revisada): só citamos artigo específico quando validado contra o texto oficial
— ver docs/legislacao.md para o mapeamento eixo -> base legal e o trecho literal de cada citação.
"""

SYSTEM_PROMPT = """Você é um especialista em educação especial e política pública brasileira. \
Escreve a leitura pública de um município no índice Escola Sem Barreiras — calculado a partir \
dos microdados do Censo Escolar do INEP — para famílias, imprensa e gestores.

Regras estritas:
- Nunca invente dados. Use apenas os números fornecidos no contexto.
- Nunca decida se a situação é adequada ou crítica — isso já vem pronto no contexto (linha "Situação já calculada"); \
sua função é só explicar em linguagem clara para quem não é especialista em dados.
- Se citar uma base legal, use APENAS a referência fornecida explicitamente no contexto (campo \
"artigo_legal_validado"). Se esse campo não vier preenchido, refira-se à "PNEEI (Decreto \
12.686/2025)" de forma geral — nunca invente um número de artigo ou de decreto.
- Não proponha ações, custos, prazos nem número de alunos beneficiados: o texto é uma leitura dos dados, não um plano. Planos são feitos pelas escolas e pela secretaria na Gestão Ativa.
- Não atribua culpa a pessoas ou órgãos.
- Não use nomes de campos nem códigos técnicos (como "score_eixo" ou "warn"); escreva para quem não conhece a base.
- Responda em português do Brasil, tom profissional e direto.
- Responda APENAS com um JSON válido no formato pedido, sem markdown, sem texto fora do JSON."""

_FORMATO_SAIDA = """Responda em JSON com exatamente esta estrutura:
{
  "situacao": "resumo de 1 frase da situação deste eixo",
  "analise": "1 a 2 parágrafos interpretando os indicadores em linguagem natural",
  "alertaLegal": "texto do alerta legal, ou null se não houver risco relevante de descumprimento",
  "referenciaMunicipio": "texto comparando com município(s) de perfil similar que já superaram o gap, ou null se não houver nenhum na base"
}"""


_SITUACAO = {"ok": "adequada", "warn": "em atenção", "nok": "crítica"}


def montar_prompt_usuario(contexto: dict) -> str:
    linhas = [
        f"Município: {contexto['nome_municipio']} — {contexto['uf']}",
        f"Eixo a diagnosticar: {contexto['eixo_label']}",
        f"Situação já calculada (não reavalie): {_SITUACAO.get(contexto['status'], contexto['status'])}",
        f"Valor do indicador: {contexto['valor']} ({contexto['subtexto']})",
        f"Score do eixo (0 a 10): {contexto['score_eixo']:.1f}",
    ]
    if contexto.get("artigo_legal_validado"):
        linhas.append(f"artigo_legal_validado: {contexto['artigo_legal_validado']}")

    if contexto.get("criterios_decreto"):
        linhas.append("Critérios do Decreto relevantes a este eixo:")
        for c in contexto["criterios_decreto"]:
            linhas.append(f"  - {c['criterio']} ({c['variavel_censo']}): {c['resultado']} — {c['conformidade']}")

    if contexto.get("benchmarking"):
        nomes = ", ".join(f"{b['nome']} (score {b['score']:.1f})" for b in contexto["benchmarking"])
        linhas.append(f"Municípios da mesma UF com melhor desempenho neste eixo: {nomes}")
    else:
        linhas.append("Não há município da mesma UF com desempenho melhor neste eixo para comparar.")

    return "\n".join(linhas) + "\n\n" + _FORMATO_SAIDA
