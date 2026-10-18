# Regras de Negócio — Diretor | Dashboard da Situação Atual da Escola

**Status:** Proposta para validação  
**Rastreabilidade:** RF-01, RF-02, RF-33, RF-35 e RF-38 do PRD da Fase 2

## RN-DSE-01 — O dashboard é a entrada da Gestão Ativa do diretor

Após login e autorização, o diretor inicia no dashboard privado da escola vinculada. O dashboard não substitui a página pública nem dá acesso a outras escolas.

## RN-DSE-02 — A situação é baseada em indicadores existentes

Score, faixa, eixos e barreiras exibidos vêm das regras e dados calculados da Fase 1. O dashboard pode ampliar o detalhamento, mas não recalcula score nem usa IA para decidir situação oficial.

## RN-DSE-03 — Dados e relatos são visualmente distintos

O valor observado no Censo, o obstáculo relatado, a sugestão da IA e a confirmação do diretor devem ter rótulos/estados distintos. Ausência de obstáculo registrado não significa ausência de barreira ou dificuldade.

## RN-DSE-04 — Registrar obstáculos é ação separada

O CTA do dashboard inicia a feature Declaração de Obstáculos. Ver ou analisar os eixos não registra automaticamente obstáculos e não é requisito para alterar os dados do Censo.

## RN-DSE-05 — Métricas exibem proveniência

Indicadores mostram edição/fonte dos dados quando disponível. Dados indisponíveis não são apresentados como zero ou conformidade presumida.
