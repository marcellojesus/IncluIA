# Índice de Requisitos — Funcionalidades da Gestão Ativa

Este arquivo é somente o mapa das especificações; requisitos detalhados estão separados por perfil e objetivo funcional. RF, nesta família de documentos, significa requisito funcional.

## Fluxo do Diretor

1. **Dashboard da Situação Atual da Escola** — tela inicial privada, análise ampliada dos eixos e entrada para as ações do diretor: [requisitos](diretor/dashboard-situacao-escola.md), [regras](../business-rules/diretor/dashboard-situacao-escola.md).
2. **Declaração de Obstáculos** — posição por barreira, emissão (pré-requisito do Plano de Ação) e publicação da declaração: [requisitos](diretor/declaracao-obstaculos.md), [regras](../business-rules/diretor/declaracao-obstaculos.md).
3. **Plano de Ação Escolar** — cruzamento barreira × obstáculo, sugestões conversacionais, seleção das ações pelo diretor e submissão: [requisitos](diretor/plano-acao-escolar.md), [regras](../business-rules/diretor/plano-acao-escolar.md).

## Fluxo do Secretário Municipal

1. **Dashboard Municipal** — tela inicial privada, eixos críticos, escolas prioritárias e fila de análise: [requisitos](secretario/dashboard-municipal.md), [regras](../business-rules/secretario/dashboard-municipal.md).
2. **Fila e Revisão de Planos Escolares** — lista de submissões e decisões de aceitar, solicitar ajustes ou reprovar: [requisitos](secretario/fila-revisao-planos.md), [regras](../business-rules/secretario/fila-revisao-planos.md).
3. **Analítico de Barreiras** — varredura assistida por IA de barreiras, obstáculos e ações da rede: [requisitos](secretario/analitico-barreiras.md), [regras](../business-rules/secretario/analitico-barreiras.md).
4. **Plano Estratégico Municipal** — composição de ações sistêmicas e cobertura parcial de ações escolares: [requisitos](secretario/plano-estrategico-municipal.md), [regras](../business-rules/secretario/plano-estrategico-municipal.md).

## Fluxo de ponta a ponta

`Dashboard da Escola` → `Declaração de Obstáculos` → `Plano de Ação Escolar` → submissão → `Dashboard Municipal`/`Fila e Revisão` → `Analítico de Barreiras` → `Plano Estratégico Municipal`.

São features independentes, com telas, critérios de aceite e regras próprias. A Declaração de Obstáculos não é parte do Plano de Ação: é insumo anterior. O Plano Estratégico Municipal também é separado da decisão do secretário sobre cada plano escolar.
