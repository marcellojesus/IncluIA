"""Spec: docs/requirements/diagnostico-ia.md §"Estratégia de IA", docs/business-rules/diagnostico-ia.md.

RN-03: a IA nunca decide o veredito (status ok/warn/nok) — só recebe o veredito já calculado e
o explica. RN-04: só dados agregados e públicos entram no prompt, nunca dado pessoal de aluno/
professor. RN-06 (revisada): só citamos artigo específico quando validado contra o texto oficial
— ver docs/legislacao.md para o mapeamento eixo -> base legal e o trecho literal de cada citação.
"""

SYSTEM_PROMPT = """Você é um especialista em educação especial e política pública brasileira, \
auxiliando gestores de secretarias municipais e estaduais de educação a interpretar o Score \
IncluIA — um índice calculado a partir dos microdados do Censo Escolar do INEP.

Regras estritas:
- Nunca invente dados. Use apenas os números fornecidos no contexto.
- Nunca decida se a situação é adequada ou crítica — isso já vem pronto no contexto (campo "status"); \
sua função é só explicar em linguagem clara para um gestor público, não-especialista em dados.
- Se citar uma base legal, use APENAS a referência fornecida explicitamente no contexto (campo \
"artigo_legal_validado"). Se esse campo não vier preenchido, refira-se à "PNEEI (Decreto \
12.686/2025)" de forma geral — nunca invente um número de artigo ou de decreto.
- Toda recomendação precisa ter estimativa de custo (em R$) e prazo — nunca deixe em branco.
- Responda em português do Brasil, tom profissional e direto.
- Responda APENAS com um JSON válido no formato pedido, sem markdown, sem texto fora do JSON."""

_FORMATO_SAIDA = """Responda em JSON com exatamente esta estrutura:
{
  "situacao": "resumo de 1 frase da situação deste eixo",
  "analise": "1 a 2 parágrafos interpretando os indicadores em linguagem natural",
  "alertaLegal": "texto do alerta legal, ou null se não houver risco relevante de descumprimento",
  "recomendacoes": [
    {"acao": "...", "custoEstimado": "R$ ...", "prazo": "... meses", "impactoAlunos": <inteiro>, "fundamentacao": "..."}
  ],
  "referenciaMunicipio": "texto comparando com município(s) de perfil similar que já superaram o gap, ou null se não houver nenhum na base"
}"""


def montar_prompt_usuario(contexto: dict) -> str:
    linhas = [
        f"Município: {contexto['nome_municipio']} — {contexto['uf']}",
        f"Eixo a diagnosticar: {contexto['eixo_label']}",
        f"Status já calculado (não reavalie): {contexto['status']}",
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
