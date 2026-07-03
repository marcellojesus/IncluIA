# Regras de Negócio — Indicadores do Município (Módulo 2)

## RN-01 — Semáforo por eixo é uma classificação determinística, não uma opinião da IA (resolvida)

O status ✅/⚠️/❌ de cada eixo é calculado por regra de limiar numérico sobre os dados do Censo — a IA generativa (ver [[diagnostico-ia]]) nunca decide o veredito do semáforo, apenas explica em linguagem natural um veredito já calculado. Isso evita que uma alucinação de modelo altere a "nota" oficial de conformidade do município.

**Decisão final** (implementada em `backend/app/features/indicadores_municipio/service.py`): em vez de limiares percentuais diferentes por eixo (proposta anterior, descartada), o semáforo reaproveita **exatamente o mesmo `score_eixo_i..iv`** (0–10) já usado no painel "Score por Eixo" — convertido para % (`score_eixo/10`) como "valor" do card, e classificado pela **mesma régua de 5 faixas de `metodologia_score.md` §5** (limiares 3,0/5,0/7,0/8,5), colapsada em 3 estados:

| Faixa (5 níveis) | Status do semáforo |
|---|---|
| Crítico | ❌ nok |
| Insuficiente / Em desenvolvimento | ⚠️ warn |
| Adequado / Referência | ✅ ok |

**Por quê**: usar uma métrica diferente da que já aparece na barra de progresso do mesmo eixo, logo abaixo do semáforo, criaria risco real de contradição visual (ex.: semáforo ✅ ao lado de uma barra de score baixa) — o que mina a confiança do gestor no produto. Reaproveitar o mesmo número elimina esse risco e não exige nenhum limiar novo a validar juridicamente (a régua de 5 faixas já é a mesma usada no mapa e em toda a metodologia do score).

## RN-02 — A tabela de conformidade com a PNEEI nunca é uma fonte jurídica oficial no MVP

Todo painel de "Detalhamento — PNEEI (Decreto 12.686/2025)" (ver `docs/legislacao.md` para o texto legal correto — o decreto que institui a PNEEI é o 12.686/2025, não o 12.773/2025) deve exibir permanentemente o aviso "⚠️ Em validação jurídica" e não deve ser usado pelo gestor como evidência formal de conformidade perante o MEC ou auditorias.

**Por quê**: `context.md` §5 nota explicitamente que "o mapeamento score↔Decreto é aproximação metodológica não validada juridicamente" — isso é um requisito de compliance do produto, não apenas um detalhe de copy. Remover o aviso sem validação jurídica formal é uma regressão de conformidade, não uma melhoria de UI.

## RN-03 — Comparações são sempre com a mesma edição do Censo

O comparativo "média estadual" / "média nacional" e o indicador de tendência (melhora/piora) devem sempre citar explicitamente a edição do Censo usada (ex.: "vs. Censo 2024"). Nunca comparar dados de edições diferentes do Censo sem rotular qual é qual.

**Por quê**: `IncluIA_Metodologia_Score_v1` registra como limitação que o score "só é comparável dentro da mesma edição do Censo" — misturar edições sem indicação geraria conclusões de tendência falsas.

## RN-04 — Município sem histórico não recebe indicador de tendência fabricado

Se não houver dado da edição anterior do Censo para o município (ex.: escola nova, mudança de código INEP), o indicador de tendência deve ser omitido — nunca exibido como "0%" ou "estável", que seriam afirmações factualmente incorretas.

## RN-05 — Cada linha da tabela do Decreto deve apontar a variável exata do Censo

Toda linha de critério na tabela de detalhamento deve citar o nome técnico da variável do Censo que a origina (ex.: `TP_AEE`, `IN_ACESSIBILIDADE_RAMPAS`). Não é permitido exibir um critério de conformidade sem essa rastreabilidade.

**Como aplicar**: ao adicionar um novo critério à tabela, o time deve primeiro localizar a variável correspondente no dicionário de dados do Censo (ver [[score-incluia]] para a lista de variáveis já mapeadas) antes de expor o critério na UI.

**Atualização**: o ETL (`backend/etl/aggregate.py`) agora agrega por município **todas** as variáveis binárias do Censo usadas nos 4 eixos (antes só 3 de ~11 estavam agregadas) — a tabela do Decreto não precisa mais exibir "🔵 Em apuração" por falta de dado. Cada linha usa o mesmo limiar único de conformidade: `≥70%` Conforme, `40%–69%` Parcial, `<40%` Não conforme (mesma régua simplificada usada para os semáforos por eixo, RN-01) — aplicado sobre `pct_escolas_<variável>` (ou `taxa_inclusao_cc` para o critério do Eixo IV).
