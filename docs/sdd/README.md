# SDD — Escola Sem Barreiras

Este diretório organiza os Documentos de Requisitos do Produto (PRDs) por nível do produto e por fase, seguindo o desenvolvimento orientado por especificação (SDD, do inglês Spec-Driven Development).

| Documento | Finalidade | Situação |
|---|---|---|
| [`prd.md`](prd.md) | Visão geral, produto atual e backlog proposto | Atualizado por engenharia reversa; Fase 2 ainda sujeita a validação |
| [`fase-1/prd.md`](fase-1/prd.md) | Comportamento observado no software local | Engenharia reversa concluída para o checkout local |
| [`fase-2/prd.md`](fase-2/prd.md) | Escopo proposto para Gestão Ativa | Rascunho v0.2, com as decisões da validação do protótipo (2026-10-18) |
| [`fase-2/impacto-fase-1.md`](fase-2/impacto-fase-1.md) | Decisão por rota da Fase 1 (mantém, ajusta, substitui, remove) e requisitos novos da área pública | Proposta para validação |
| [`fase-2/arquitetura.md`](fase-2/arquitetura.md) | Decisões de arquitetura da Fase 2 (persistência, autenticação, auditoria, IA, hospedagem) | Proposta para revisão |
| [`../../metodologia_barreiras.md`](../../metodologia_barreiras.md) | Regra determinística de identificação das barreiras por escola | Proposta v0.1 para validação |
| [`fase-2/requirements/acesso-gestao-ativa.md`](fase-2/requirements/acesso-gestao-ativa.md) | Requisitos e critérios de aceite para cadastro e acesso | Proposta para validação |
| [`fase-2/business-rules/acesso-gestao-ativa.md`](fase-2/business-rules/acesso-gestao-ativa.md) | Regras de vínculo, autorização e auditoria | Proposta para validação |
| [`fase-2/requirements/planos-de-acao.md`](fase-2/requirements/planos-de-acao.md) | Índice do fluxo e das features de Planos de Ação | Mapa; detalhes separados abaixo |
| [`fase-2/requirements/diretor/dashboard-situacao-escola.md`](fase-2/requirements/diretor/dashboard-situacao-escola.md) | Diretor: tela inicial e dashboard da situação da escola | Proposta para validação |
| [`fase-2/requirements/diretor/declaracao-obstaculos.md`](fase-2/requirements/diretor/declaracao-obstaculos.md) | Diretor: Declaração de Obstáculos | Proposta para validação |
| [`fase-2/requirements/diretor/plano-acao-escolar.md`](fase-2/requirements/diretor/plano-acao-escolar.md) | Diretor: Plano de Ação Escolar | Proposta para validação |
| [`fase-2/requirements/secretario/dashboard-municipal.md`](fase-2/requirements/secretario/dashboard-municipal.md) | Secretário: tela inicial municipal, prioridades e fila de análise | Proposta para validação |
| [`fase-2/requirements/secretario/fila-revisao-planos.md`](fase-2/requirements/secretario/fila-revisao-planos.md) | Secretário: entrada, fila e decisão sobre planos escolares | Proposta para validação |
| [`fase-2/requirements/secretario/analitico-barreiras.md`](fase-2/requirements/secretario/analitico-barreiras.md) | Secretário: analítico assistido por IA | Proposta para validação |
| [`fase-2/requirements/secretario/plano-estrategico-municipal.md`](fase-2/requirements/secretario/plano-estrategico-municipal.md) | Secretário: Plano Estratégico Municipal, inclusive cobertura parcial | Proposta para validação |
| [`fase-2/business-rules/planos-de-acao.md`](fase-2/business-rules/planos-de-acao.md) | Índice das regras das features de Planos de Ação | Mapa; regras detalhadas separadas abaixo |
| [`fase-2/business-rules/diretor/dashboard-situacao-escola.md`](fase-2/business-rules/diretor/dashboard-situacao-escola.md) | Diretor: regras do dashboard da escola | Proposta para validação |
| [`fase-2/business-rules/diretor/declaracao-obstaculos.md`](fase-2/business-rules/diretor/declaracao-obstaculos.md) | Diretor: regras da Declaração de Obstáculos | Proposta para validação |
| [`fase-2/business-rules/diretor/plano-acao-escolar.md`](fase-2/business-rules/diretor/plano-acao-escolar.md) | Diretor: regras do Plano de Ação Escolar | Proposta para validação |
| [`fase-2/business-rules/secretario/fila-revisao-planos.md`](fase-2/business-rules/secretario/fila-revisao-planos.md) | Secretário: regras da fila e revisão de planos | Proposta para validação |
| [`fase-2/business-rules/secretario/dashboard-municipal.md`](fase-2/business-rules/secretario/dashboard-municipal.md) | Secretário: regras do dashboard municipal | Proposta para validação |
| [`fase-2/business-rules/secretario/analitico-barreiras.md`](fase-2/business-rules/secretario/analitico-barreiras.md) | Secretário: regras do analítico de barreiras | Proposta para validação |
| [`fase-2/business-rules/secretario/plano-estrategico-municipal.md`](fase-2/business-rules/secretario/plano-estrategico-municipal.md) | Secretário: regras do Plano Estratégico Municipal | Proposta para validação |

Os documentos detalhados existentes em `docs/requirements/`, `docs/business-rules/`, `interface.md`, `context.md` e `arquitetura.md` permanecem nos caminhos atuais nesta etapa. Eles contêm referências cruzadas e serão revisados, reconciliados com o software local e reorganizados somente após a avaliação do produto e autorização do responsável. As novas especificações da Fase 2 são organizadas dentro de `docs/sdd/fase-2/`.

## Fluxo de trabalho

1. Avaliar o software no ambiente local.
2. Receber autorização para a engenharia reversa e revisão documental.
3. Confrontar comportamento observado, código e documentos-fonte aprovados.
4. Atualizar requisitos, regras, arquitetura e estrutura documental com rastreabilidade.
5. Validar o protótipo HTML da Fase 2 antes de iniciar sua implementação.
