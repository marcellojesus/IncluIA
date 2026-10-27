# Requisitos — Diretor | Dashboard da Situação Atual da Escola

**Status:** Implementado · notas de implementação em 2026-10-26  
**PRD:** RF-01, RF-02, RF-33, RF-35 e RF-38  
**Dependência:** acesso aprovado e vínculo ativo com a escola

## Objetivo

Ser a tela inicial do diretor na Gestão Ativa e oferecer uma visão ampliada e privada da situação da escola antes de iniciar o registro dos obstáculos.

## Conteúdo proposto

- Identificação da escola e edição/ano dos dados apresentados.
- Score geral, faixa e explicação de que se trata de indicador calculado, não de certificação legal.
- Situação detalhada nos quatro eixos da PNEEI, com indicadores e dados de origem disponíveis.
- Barreiras identificadas por eixo e sinalização de quais têm obstáculo registrado ou permanecem sem contexto.
- Declaração de Obstáculos existente, Plano de Ação atual, submissões e decisões municipais.
- Ação principal para **Registrar obstáculos**, habilitada a partir da revisão dos eixos/barreiras, além de acesso ao Plano de Ação quando aplicável.

## Requisitos funcionais

- **DSE-RF-01:** abrir este dashboard como tela inicial do diretor após autenticação e autorização.
  - **Aceite:** diretor é encaminhado apenas à escola do vínculo ativo; solicitações pendentes não entram no dashboard.
- **DSE-RF-02:** apresentar score geral, faixa, quatro eixos e indicadores disponíveis em visão ampliada.
  - **Aceite:** cada métrica identifica fonte/edição do Censo; dado ausente aparece como indisponível, não como zero.
- **DSE-RF-03:** apresentar barreiras por eixo e a posição registrada pelo diretor (sem posição, rascunho, obstáculo relatado, divergência com o Censo, sem relato nesta versão).
  - **Aceite:** obstáculo confirmado, rascunho e ausência de registro são estados distintos; nenhum deles altera o indicador de origem.
- **DSE-RF-04:** apresentar status e atalhos para Declaração de Obstáculos (rascunho, emitida vN, publicada vN) e Plano de Ação, incluindo decisão municipal mais recente. O atalho do Plano de Ação só fica ativo após a emissão da declaração.
- **DSE-RF-05:** oferecer ação explícita para iniciar a Declaração de Obstáculos a partir da situação da escola.
  - **Aceite:** iniciar o fluxo leva à feature própria e preserva escola/eixo/barreira selecionados quando aplicável.
- **DSE-RF-06:** impedir que dados deste dashboard sejam acessíveis por outro diretor ou por visitante público.
  - **Aceite:** autorização é validada no servidor; a interface pública da escola continua independente.

## Decisões pendentes

Quais indicadores detalhados serão exibidos além dos quatro eixos; como mostrar data/edição dos dados; se score deve ser apresentado em destaque ou contextualizado; comportamento quando dados do Censo e relato do diretor divergem.

## Notas de implementação (2026-10-23, revisadas em 2026-10-26)

- **Código:** backend em `backend/app/features/diretor/` (`GET /gestao/diretor/escola`, escola vinda do vínculo); telas `DashboardDiretor.tsx` e `PainelTrabalhoDiretor.tsx`, rota `/gestao/diretor`.
- **Decisões que o código fixou:**
  - **indicadores:** score e faixa em destaque, com o aviso de que não é certificação legal; os quatro eixos; matrículas da educação especial e em classe comum; o dado do Censo de cada barreira;
  - **edição dos dados:** um selo único "Censo {edição}" e a versão da metodologia de barreiras; não há fonte por métrica;
  - **divergência entre Censo e relato:** vira a posição "divergência com o dado do Censo", que não altera o indicador.
- **Painel de pendências:** lista o que depende do diretor, em ordem de prioridade: ajustar o plano após pedido de ajustes ou reprovação (urgente); registrar obstáculos ou emitir a Declaração; reemitir quando há alterações; fazer o plano; atualizar a base do plano; publicar a Declaração ou o plano aceito.
- **Ações municipais:** o dashboard mostra as ações da última versão confirmada do Plano Estratégico Municipal que atendem a escola (ver `../secretario/plano-estrategico-municipal.md`).
- **Diferenças em relação ao texto:**
  - a versão emitida da Declaração aparece na tela como "Registrada";
  - o atalho por eixo (`/gestao/diretor/declaracao?eixo=`) preserva o eixo, mas não a barreira (DSE-RF-05);
  - matrícula ausente no Censo aparece como 0, não como "indisponível" (DSE-RF-02 e RN-DSE-05 pedem "indisponível").
- Sem a metodologia de barreiras no servidor, a rota responde 503.
