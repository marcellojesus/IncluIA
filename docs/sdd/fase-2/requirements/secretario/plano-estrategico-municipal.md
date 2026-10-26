# Requisitos — Secretário | Plano Estratégico Municipal

**Status:** Proposta para validação  
**PRD:** RF-26 a RF-30

## Objetivo

Permitir ao secretário compor um plano municipal a partir de padrões da rede, ações sistêmicas e partes selecionadas dos Planos de Ação das escolas.

## Requisitos funcionais

- **SPM-RF-01:** permitir criar proposta municipal usando resultados do analítico e planos escolares visíveis ao secretário.
- **SPM-RF-02:** permitir incluir uma ação sistêmica nova ou selecionar uma ação/parte identificável de uma ou mais propostas escolares.
  - **Aceite:** cada ação identifica barreiras, escolas e itens escolares que pretende atender e indica explicitamente cobertura parcial quando aplicável.
- **SPM-RF-03:** não alterar automaticamente estado, aprovação ou restante dos Planos de Ação escolares ao incluir uma ação municipal.
- **SPM-RF-04:** permitir revisar escolas beneficiadas, prioridade, responsável, prazo, horizonte LOA/PPA, estimativas, premissas e fontes.
- **SPM-RF-05:** apoiar a elaboração por IA de análise e narrativa executiva, com fontes e incertezas visíveis.
  - **Aceite:** números de impacto, custos e abrangência são calculados/validados por métodos determinísticos ou aparecem claramente como estimativas humanas, nunca como fato inventado pelo texto da IA.
- **SPM-RF-06:** permitir que o secretário edite, confirme e versione o plano municipal.
- **SPM-RF-07:** após confirmação, disponibilizar a cada diretor apenas ações municipais associadas à sua escola.
- **SPM-RF-08:** distinguir proposta, confirmação do plano, aprovação orçamentária, financiamento, execução e conclusão.
  - **Aceite:** confirmação do plano não altera estado para financiado ou executado.

## Notas de implementação (2026-10-26)

**Decisões do responsável:**
- a base usa só os Planos de Ação **aceitos** (a última versão aceita de cada escola);
- a primeira entrega cobre proposta pela IA, edição, confirmação com versões e visão do diretor.

- **Código:**
  - backend em `backend/app/features/plano_municipal/` (rotas `/gestao/secretario/plano-municipal` e `/gestao/diretor/acoes-municipais`, migração `320f5f825535`);
  - contexto da rede em `contexto_ia/montador.py` (`montar_contexto_rede`);
  - tela `PlanoMunicipal.tsx`, na aba "Plano municipal" do painel do secretário;
  - testes em `tests/test_plano_municipal.py`.
- **Base da rede (SPM-RF-01), calculada pelo sistema:**
  - para cada barreira, quantas escolas municipais a têm no Censo e as ações dos planos aceitos;
  - cada ação escolar recebe uma referência `[E<n>-A<m>]`, que é o que vai à IA no lugar do nome da escola.
- **IA (SPM-RF-02, 05; RN-SPM-04):**
  - por barreira, a IA propõe de 1 a 3 ações municipais que juntam necessidades comuns e indica quais ações escolares cada uma atende, com cobertura total ou parcial;
  - o validador recusa referência inexistente e fonte fora do contexto, e o pedido passa ao próximo provedor;
  - o sistema traduz as referências para escolas e itens e conta as escolas atendidas;
  - as referências saem do texto gravado, porque a numeração muda quando novos planos são aceitos.
- **Secretário (SPM-RF-04, 06):**
  - inclui, edita (barreiras, ação, justificativa, responsável, prazo, LOA/PPA, custo, premissas, prioridade, escolas e cobertura), descarta ou escreve ações;
  - confirma versões congeladas;
  - o texto livre passa pelo Guardião, e escola e item são validados contra a rede do vínculo.
- **Diretor (SPM-RF-07; RN-SPM-03):** o dashboard mostra as ações da última versão confirmada que atendem a escola, com a cobertura da própria escola e a contagem de escolas atendidas na rede, sem os nomes das outras escolas.
- **SPM-RF-03, 08:** nada altera os planos das escolas; a tela e a confirmação dizem que confirmar não é aprovação orçamentária, financiamento nem execução.
- **LGPD (revisão do AgLGPD em 2026-10-26, aplicada):**
  - o diretor **não** recebe a justificativa da ação municipal, porque ela é escrita a partir dos planos de todas as escolas, que são privados (RN-PAE-03), e pode citar outras escolas;
  - à IA vão só contagens da rede e a regra da barreira, sem o nome do município: com ele, E1..En poderiam ser cruzados com o Censo;
  - as referências [E<n>-A<m>] saem de todos os campos gravados;
  - o secretário é avisado quando o Guardião mascara trechos das ações escolares que vão à IA;
  - ao aceitar uma sugestão, as escolas e ações são conferidas de novo contra a base atual;
  - testes de isolamento entre municípios.
- **Pendente (decisão):**
  - auditoria de aceitar, descartar, editar e remover no rascunho (hoje só a confirmação gera evento);
  - retenção das sugestões municipais aceitas ou descartadas;
  - um texto para as escolas, escrito pelo secretário, se a justificativa precisar chegar aos diretores.
- **Ainda não implementado:**
  - narrativa executiva escrita pela IA (hoje há o resumo calculado);
  - acompanhamento de execução (RN-SPM-05);
  - exportação.

## Decisões pendentes

Definir aprovação/assinatura do plano; critérios de orçamento e fonte; rastreamento de ação parcial; responsáveis por atualizar progresso; sincronização com LOA/PPA e forma de distribuição às escolas.
