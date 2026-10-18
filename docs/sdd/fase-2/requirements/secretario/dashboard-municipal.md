# Requisitos — Secretário | Dashboard Municipal

**Status:** Proposta para validação  
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

## Decisões pendentes

Definir métricas de contribuição escolar para o score municipal baixo; quais KPIs/cobertura entram no primeiro viewport; política de escolas com poucos alunos; atualização e defasagem dos dados; se o secretário vê escolas sem submissão no ranking de prioridades.
