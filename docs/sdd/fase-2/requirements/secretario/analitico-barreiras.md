# Requisitos — Secretário | Analítico de Barreiras

**Status:** Implementado · notas de implementação em 2026-10-27  
**PRD:** RF-23 a RF-25

## Objetivo

Ajudar o secretário a identificar padrões e dificuldades da rede por meio de uma varredura assistida por IA das Declarações de Obstáculos e dos Planos de Ação submetidos.

## Requisitos funcionais

- **SAB-RF-01:** analisar somente Declarações emitidas e planos submetidos por escolas da rede autorizada, dentro do recorte selecionado. Rascunhos não entram na análise.
- **SAB-RF-02:** cruzar barreiras, obstáculos e ações propostas para apresentar temas recorrentes, dificuldades potencialmente sistêmicas e casos locais.
  - **Aceite:** inferências da IA são rotuladas como análise assistida e vinculadas a exemplos/registros que as sustentam.
- **SAB-RF-03:** calcular frequências, cobertura, quantidade de escolas e métricas numéricas por regras reproduzíveis.
  - **Aceite:** não usar texto livre da IA como fonte de contagens, score ou classificação oficial.
- **SAB-RF-04:** explicitar cobertura e limitações da análise.
  - **Aceite:** escola sem submissão é identificada como sem dados de plano, não como escola sem barreiras.
- **SAB-RF-05:** permitir explorar evidências por escola, barreira, obstáculo e ação dentro do escopo autorizado.
- **SAB-RF-06:** permitir usar achados como insumo para construir Plano Estratégico Municipal, sem converter automaticamente insights em decisões ou ações aprovadas.

## Decisões tomadas (2026-10-27)

- **"Maior dificuldade" (RN-SAB-05):** as barreiras são ordenadas pelos **alunos atingidos**, a soma das matrículas da educação especial das escolas da rede com a barreira no Censo. É a mesma ponderação do score da rede e do Dashboard Municipal. Empate: mais escolas, depois o código. A tela também mostra o % de escolas, e a barreira presente em 90% ou mais das escolas é marcada como de **alta recorrência**.
- **Síntese da IA:** uma síntese da rede inteira, gerada quando o secretário pede ("Gerar/Atualizar análise") e guardada até a próxima. Separa observação, hipótese e recomendação, e cada achado aponta as barreiras e os relatos em que se apoia.
- **Oportunidades de resposta (SAB-RF-06):** o Analítico não propõe ações. Cada barreira tem "Planejar no plano municipal", que abre o Plano Estratégico Municipal nela, onde a IA já propõe ações da rede.
- **Período e fonte:** a última Declaração emitida e a última versão enviada do Plano de Ação de cada escola, e o Censo da edição atual.

## Notas de implementação (2026-10-27)

- **Código:** backend em `backend/app/features/analitico/` (rotas `GET /gestao/secretario/analitico` e `POST /gestao/secretario/analitico/sintese`, migração `1bcf96118a88`); tela `AnaliticoBarreiras.tsx`, aba "Analítico" do painel do secretário, com atalho no Dashboard Municipal; testes em `backend/tests/test_analitico.py`.
- **Números (SAB-RF-01, 03, 04):** recalculados a cada abertura, só sobre escolas da rede do vínculo. Por barreira: escolas e alunos atingidos; posições da última Declaração emitida (obstáculo, divergência, sem relato) e quantas escolas não têm registro emitido; planos enviados com ação para a barreira e quantos foram aceitos. Rascunho nunca entra.
- **Evidências (SAB-RF-05):** por barreira, as escolas com posição emitida ou ação enviada, com o resumo da posição, as ações e o estado do plano. É o mesmo que o secretário já vê nas abas de Declarações e de Planos.
- **IA (SAB-RF-02; RN-SAB-03):** vão à IA as contagens da rede, sem município nem escolas, e até 8 resumos de posição por barreira, cada um com uma referência [R<n>] e passado de novo pelo Guardião (o que bloquear fica de fora e é contado). O validador recusa barreira ou referência fora do contexto e passa ao próximo provedor. As referências saem do texto gravado, e o sistema as traduz em escola e barreira.
- **Atualização:** a síntese guarda uma assinatura das versões de Declaração e de plano usadas. Quando uma escola emite ou envia depois, a tela avisa que a análise está desatualizada.
- **Sem IA:** os números continuam; o pedido de síntese responde 503 com aviso.
- **Privacidade (revisão do AgLGPD de 2026-10-27, aplicada):**
  - à IA não vão contagens exatas nem a edição do Censo, só proporções arredondadas a 5 pontos, e "poucas escolas"/"algumas" abaixo de 3, porque o conjunto de contagens exatas identifica o município nos microdados;
  - ficam fora da IA os relatos de Declarações retiradas por dado pessoal ou pedido de titular, e os de escola com menos de 5 matrículas quando a barreira é de classe exclusiva ou está em menos de 3 escolas da rede; todos entram na contagem de "fora";
  - a síntese guarda a trilha do que foi enviado (Declaração e barreira, sem texto);
  - sem registro novo, um pedido dentro de 1 hora devolve a síntese guardada, sem chamar a IA;
  - ficam guardadas as 5 últimas sínteses por município, cada uma por até 1 ano, até a edição nova do Censo ou até a retirada por LGPD de um relato usado ([retencao.md](../../business-rules/retencao.md), RN-RET-07);
  - bloqueio do Guardião ao juntar os relatos responde 409, sem chamar a IA;
  - relato mascarado na entrada também gera o aviso ao secretário;
  - na tela, contagem de alunos abaixo de 5 aparece como "menos de 5".

## Decisões pendentes

Modelo e métricas de avaliação da análise da IA; frequência mínima de relatos para a IA afirmar um padrão.
