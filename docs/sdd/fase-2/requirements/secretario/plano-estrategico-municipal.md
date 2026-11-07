# Requisitos — Secretário | Plano Estratégico Municipal

**Status:** Implementado · notas de implementação até 2026-10-27  
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
  - retenção das sugestões municipais: a descartada perde o conteúdo em 30 dias e a aceita segue a versão ([retencao.md](../../business-rules/retencao.md), definido em 2026-11-03);
  - um texto para as escolas, escrito pelo secretário, se a justificativa precisar chegar aos diretores.
- **Ainda não implementado:**
  - acompanhamento de execução (RN-SPM-05);
  - exportação (RF-31).

## Notas de implementação (2026-10-27): narrativa executiva (RF-30; SPM-RF-05 e 06)

**Decisão do responsável:** entregar sem fonte de custo. Custos e projeções aparecem só como estimativas registradas pela secretaria até as decisões pendentes 12 e 13 do PRD (método de impacto no score; FNDE e SIOPE).

- **Código:**
  - `backend/app/features/plano_municipal/narrativa.py`, rotas `POST` e `PUT /gestao/secretario/plano-municipal/versoes/{n}/narrativa`;
  - tabela `narrativas_plano_municipal` (migração `3bc6efcd2093`);
  - contexto em `contexto_ia/montador.py` (`montar_contexto_plano`);
  - tela `NarrativaExecutiva.tsx`, aberta por "Narrativa executiva" em cada versão confirmada;
  - testes em `tests/test_narrativa_municipal.py`.
- **Escopo:** a narrativa é de uma **versão confirmada**, que é congelada; a numeração [A<n>] das ações não muda. Uma narrativa por versão: gerar de novo substitui o texto (a tela pede confirmação quando o texto foi revisado).
- **Seções:** resumo, situação da rede, estratégia (blocos que agrupam ações e citam quais), fundamentação legal, próximos passos, incertezas; e o que a base normativa entregue não sustenta.
- **Números (SPM-RF-05):** calculados pelo sistema a partir da versão e mostrados ao lado do texto: ações, barreiras, escolas atendidas de quantas, LOA e PPA, prioridade alta, ações com custo estimado, ações com cobertura parcial. O validador recusa texto da IA com valor em reais, percentual ou contagem de escolas, alunos ou profissionais, e o pedido passa ao próximo provedor. A lista de ações mostra o custo como "estimativa registrada pela secretaria (não verificada)" ou "a estimar".
- **O que vai à IA:** a situação da rede do Analítico em faixas ("a maioria das escolas"), as ações da versão com barreiras, horizonte, prioridade, responsável, prazo, alcance em faixa e custo só como "estimativa registrada" ou "a estimar", e os trechos da base normativa (primeiro os já citados pelas ações, depois o mapa de cada barreira).
- **LGPD (revisão do AgLGPD em 2026-10-27, aplicada):**
  - nomes do município e das escolas da rede e códigos INEP saem do texto das ações antes do Guardião, que os trata como nomes públicos; resposta com um deles é recusada;
  - ação ligada a escola pequena numa barreira sensível (classe exclusiva ou poucas escolas), ou a escola com plano da base ou Declaração retirados por motivo LGPD, vai só com a linha estruturada, sem o texto;
  - premissas e justificativa não vão;
  - trilha das gerações sem texto e eventos de auditoria `narrativa_plano_municipal_gerada` e `narrativa_plano_municipal_editada`;
  - só o secretário do município gera, lê e edita; o diretor e a área pública não veem a narrativa.
- **Edição (SPM-RF-06):** o secretário edita cada seção; o texto passa pelo Guardião e a tela marca "Revisada pela secretaria". Desde 2026-11-03 a edição passa também pela checagem de números e de nomes da rede da resposta da IA (`narrativa.problema`) e não é salva se tiver algum (RN-PDF-09).
- **PDF:** a narrativa tem PDF próprio, para quem decide o orçamento (PDF-RF-07).
- **Retenção:** versões e narrativas ficam enquanto durar o programa ([retencao.md](../../business-rules/retencao.md), RN-RET-06).
- **Pendente:** fonte de custo (decisões 12 e 13 do PRD).

## Decisões pendentes

Definir aprovação/assinatura do plano; critérios de orçamento e fonte; rastreamento de ação parcial; responsáveis por atualizar progresso; sincronização com LOA/PPA e forma de distribuição às escolas.
