# Requisitos — Secretário | Dashboard Municipal

**Status:** Implementado · notas de implementação até 2026-10-26  
**PRD:** RF-01, RF-02, RF-18, RF-34, RF-36 a RF-38  
**Dependência:** acesso aprovado à rede municipal

## Objetivo

Ser a tela inicial própria do secretário na Gestão Ativa, oferecendo uma visão de gestão da rede municipal distinta da área pública e servindo de ponto de entrada para prioridades, revisão de planos, analítico e plano municipal.

## Conteúdo proposto

- Score municipal e contexto da edição dos dados.
- Situação dos quatro eixos, ordenados do mais crítico ao mais adequado, com valores/fontes que expliquem a ordenação.
- Lista de escolas prioritárias, ordenada por critérios reproduzíveis que indiquem sua contribuição para o score municipal baixo.
- Indicadores de cobertura: escolas com barreiras elegíveis, escolas com obstáculos registrados, escolas com Plano de Ação submetido e fila aguardando análise.
- Atalhos para abrir a fila de revisão, o Analítico de Barreiras e o Plano Estratégico Municipal.

## Requisitos funcionais

- **DMS-RF-01:** abrir este dashboard como tela inicial do secretário após autenticação e autorização.
  - **Aceite:** o secretário vê somente o município/rede associado ao seu vínculo ativo.
- **DMS-RF-02:** exibir score municipal, edição dos dados, situação por eixo e indicadores agregados da rede.
  - **Aceite:** valores não são inventados; dados ausentes e cobertura são explicitados.
- **DMS-RF-03:** ordenar visualmente os eixos do mais crítico ao mais adequado segundo status/score determinístico do produto.
  - **Aceite:** a regra e o valor de ordenação são visíveis ou acessíveis; IA não escolhe a classificação.
- **DMS-RF-04:** listar escolas prioritárias e explicar o critério pelo qual cada uma contribui para a situação municipal.
  - **Aceite:** o ranking usa métricas determinísticas acordadas, explicita edição/fonte e não atribui causalidade não demonstrada.
- **DMS-RF-05:** mostrar indicadores separados para escolas com barreiras detectadas, escolas com Declaração emitida, planos submetidos e planos aguardando análise.
  - **Aceite:** ausência de submissão não é interpretada como ausência de dificuldade; filtros e denominadores são apresentados.
- **DMS-RF-06:** mostrar a quantidade/lista de escolas com plano pendente e permitir abrir diretamente a fila de revisão.
- **DMS-RF-07:** oferecer navegação às features de Analítico de Barreiras e Plano Estratégico Municipal.
- **DMS-RF-08:** limitar os dados exibidos à rede autorizada, inclusive em chamadas diretas às rotas do servidor.
- **DMS-RF-09:** manter o dashboard privado separado da página pública municipal, que continua sem dados administrativos de submissões e decisões.

## Decisões tomadas (2026-10-26)

- **Score da rede:** o número principal é o score da **rede municipal** (só as escolas da rede do secretário), com a mesma ponderação por alunos da educação especial do score público (RN-03 de `docs/business-rules/score-incluia.md`). O score do município com todas as redes, igual ao da página pública, aparece como referência.
- **Eixos:** score de cada eixo na rede, com a mesma ponderação, ordenado do menor para o maior; empate mantém a ordem I–IV.
- **Contribuição escolar (DMS-RF-04):** peso = (10 − score da escola) × alunos ESP da escola ÷ alunos ESP da rede. A soma dos pesos de todas as escolas é 10 − score da rede. Ranking pelo maior peso; empate pelo menor score. Mostra as 10 primeiras.
- **Escolas sem aluno ESP:** ficam fora do ranking (não pesam no score da rede) e a tela informa quantas são. Se nenhuma escola da rede tiver aluno ESP, vale o fallback da RN-03: média simples e peso igual para todas.
- **Poucos alunos:** contagem abaixo de 5 aparece como "menos de 5" (`LIMIAR_CELULA_PEQUENA`).
- **Escolas sem submissão:** entram no ranking. Gravidade e andamento (Declaração emitida, estado do último plano enviado) aparecem separados.
- **Primeiro viewport:** score da rede e atalhos para a fila e o Plano Estratégico Municipal; o Analítico de Barreiras aparece como "em breve" até ser entregue.

Implementação: `backend/app/features/dashboard_municipal/`, rota `GET /gestao/secretario/dashboard`, aba "Visão da rede" (tela inicial) do painel do secretário.

## Decisões pendentes

Atualização e defasagem dos dados entre edições do Censo.
