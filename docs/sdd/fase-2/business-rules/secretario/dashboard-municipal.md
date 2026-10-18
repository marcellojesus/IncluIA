# Regras de Negócio — Secretário | Dashboard Municipal

**Status:** Proposta para validação  
**Rastreabilidade:** RF-01, RF-02, RF-18, RF-34, RF-36 a RF-38 do PRD da Fase 2

## RN-DMS-01 — O dashboard é a entrada do secretário na Gestão Ativa

Após login e autorização, o secretário inicia no dashboard privado do município vinculado. A tela pública municipal não é substituída nem recebe dados administrativos privados.

## RN-DMS-02 — Eixos são ordenados por regra determinística

A ordem “mais crítico → mais adequado” usa scores/status já calculados pela metodologia aprovada. A IA não decide score, situação nem ordenação oficial.

## RN-DMS-03 — Prioridade de escola exige critério explicável

A lista de escolas que contribuem para o score municipal baixo deve usar uma métrica reproduzível, como contribuição ponderada do score ou lacunas por eixo, a ser aprovada. A lista não deve afirmar causalidade maior que a métrica suporta. Casos com amostra pequena/sem denominador adequado são identificados.

## RN-DMS-04 — Indicadores de registro têm denominadores explícitos

Contagem de escolas com barreiras, obstáculos e planos submetidos deve declarar o universo e recorte usado. Escola sem submissão não significa escola sem barreiras.

## RN-DMS-05 — Fila de análise é subconjunto identificado

A fila sinalizada no dashboard inclui escolas com versões de plano submetidas e pendentes de decisão. Ela é distinta da lista de prioridade de indicadores e não deve misturar severidade da escola com status de workflow.

## RN-DMS-06 — Acesso restrito à rede municipal

O dashboard e seus dados são autorizados no servidor para o município associado ao secretário. Modificar código municipal na URL, filtros ou requisições não amplia o escopo.

## RN-DMS-07 — Informação administrativa não é pública

Estado de submissão, comentários de revisão, justificativas de reprovação e planos privados não aparecem na área pública; exposição pública depende de regra e autorização próprias.
