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

## Decisões pendentes

Definir aprovação/assinatura do plano; critérios de orçamento e fonte; rastreamento de ação parcial; responsáveis por atualizar progresso; sincronização com LOA/PPA e forma de distribuição às escolas.
