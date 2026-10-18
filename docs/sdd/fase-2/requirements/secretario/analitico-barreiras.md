# Requisitos — Secretário | Analítico de Barreiras

**Status:** Proposta para validação  
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

## Decisões pendentes

Critérios transparentes para severidade e “maior dificuldade”; frequências mínimas para proteger casos identificáveis; período e fonte de dados; modelo e métricas de avaliação da análise da IA.
