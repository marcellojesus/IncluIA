# Gestão Ativa — Visão Geral do Produto

**Escola Sem Barreiras · Proposta da Fase 2**  
**Status:** material explicativo para discussão; escopo ainda sujeito a validação

**Versão HTML navegável:** [Abrir guia no navegador](guia_gestao_ativa.html)

> Este guia acompanha o [protótipo navegável da Gestão Ativa](prototipo_gestao_ativa.html). O protótipo demonstra fluxos e telas com dados fictícios: não autentica usuários, não consulta dados reais e não salva decisões em um servidor.

## O que é a Gestão Ativa

A Gestão Ativa é o módulo proposto para transformar os indicadores públicos da Escola Sem Barreiras em um processo de trabalho entre a escola e a secretaria municipal.

Na área pública, qualquer visitante pode consultar os indicadores disponíveis. A Gestão Ativa será uma área restrita a diretores de escola e secretários municipais com vínculo institucional validado. Cada perfil terá seu próprio ponto de entrada, suas informações e suas ações.

A proposta não substitui o Censo Escolar, não altera o score publicado e não significa, por si só, que uma necessidade recebeu orçamento ou foi atendida.

## Como as duas jornadas se conectam

```text
Diretor
Dashboard da escola
  → Declaração de Obstáculos
  → Plano de Ação Escolar
  → Submissão à secretaria

Secretário municipal
Dashboard municipal
  → Fila e revisão dos planos escolares
  → Analítico de Barreiras
  → Plano Estratégico Municipal
  → Ações relacionadas às escolas
```

A Declaração de Obstáculos e o Plano de Ação são funcionalidades diferentes. A declaração registra o contexto da escola e alimenta a construção do plano; não é, por si só, um plano ou uma decisão orçamentária.

## Jornada do diretor

### 1. Dashboard da Situação Atual da Escola

Após entrar na Gestão Ativa, o diretor vê uma leitura ampliada da escola vinculada ao seu perfil: score e faixa, situação nos quatro eixos, barreiras identificadas nos dados, obstáculos já registrados, pendências e estado dos planos enviados à secretaria.

O dashboard é privado e serve de ponto de partida. A página pública da escola continua sendo uma experiência diferente, voltada à consulta dos dados abertos.

### 2. Declaração de Obstáculos

O diretor percorre as barreiras identificadas para a escola. Para cada uma, uma conversa com inteligência artificial (IA) ajuda a relatar o obstáculo, faz perguntas para compreender melhor o contexto e organiza uma proposta de texto.

O diretor revisa e confirma cada registro. Ao final, os obstáculos confirmados podem ser reunidos em uma Declaração de Obstáculos, mantendo a ligação entre cada obstáculo, a barreira correspondente, a escola e sua autoria.

A IA ajuda a estruturar o relato; não altera os dados do Censo nem confirma o conteúdo em nome do diretor.

### 3. Plano de Ação Escolar

Em um fluxo separado, a IA cruza cada barreira com o obstáculo registrado e propõe uma ou mais ações. O diretor conversa sobre a pertinência de cada proposta, pede esclarecimentos, solicita ajustes ou descarta o que não se aplica.

O plano contém somente ações escolhidas pelo diretor. Ele pode revisar responsáveis, prazos, observações, estimativas e horizonte orçamentário. Quando estiver pronto, submete uma versão à secretaria. Essa versão fica registrada para análise; alterações posteriores devem gerar nova versão.

## Jornada do secretário municipal

### 1. Dashboard Municipal

Após entrar, o secretário vê uma tela própria da rede municipal, diferente da área pública. Ela reúne a situação dos eixos, escolas prioritárias e a fila de planos escolares submetidos que aguardam análise.

Os eixos são ordenados com base em indicadores calculados. A priorização das escolas precisa usar critérios transparentes e reproduzíveis, para que o secretário entenda por que cada unidade aparece em destaque.

### 2. Fila e Revisão dos Planos Escolares

A fila mostra as escolas que enviaram um Plano de Ação, o estado da revisão e a versão submetida. O secretário pode:

- **Aceitar** a versão como base de planejamento, sem recomendação adicional.
- **Solicitar ajustes**, explicando o que a escola precisa revisar.
- **Reprovar**, apresentando uma justificativa.

A decisão se aplica à versão analisada e fica registrada. Aceitar um plano não significa que o orçamento foi aprovado ou que as ações foram executadas.

### 3. Analítico de Barreiras

Com base nas declarações e nos planos disponíveis, uma análise assistida por IA procura padrões entre barreiras, obstáculos e ações: o que aparece com frequência, quais dificuldades parecem compartilhadas e que escolas podem ter necessidades semelhantes.

Contagens e métricas devem ser calculadas por regras verificáveis. As interpretações da IA precisam aparecer como apoio à análise, com evidências e limites visíveis, não como uma decisão automática.

### 4. Plano Estratégico Municipal

O secretário pode selecionar ações sistêmicas e ações propostas pelas escolas para compor um plano municipal. Uma ação municipal pode atender uma necessidade comum ou cobrir somente uma parte do plano de uma escola.

A cobertura municipal deve mostrar quais escolas, barreiras e ações estão incluídas. Selecionar uma parte não aceita, substitui nem encerra o restante do plano escolar. O secretário revisa e confirma o plano municipal; a confirmação não registra automaticamente financiamento ou execução.

## O papel da IA

A IA é assistente de conversa, organização e análise. Ela pode ajudar a:

- Aprofundar o relato do diretor sobre um obstáculo.
- Estruturar uma Declaração de Obstáculos para revisão humana.
- Sugerir ações a partir do vínculo entre barreira e obstáculo.
- Ajudar o secretário a identificar padrões nos registros enviados.
- Apoiar a redação de uma narrativa executiva para o plano municipal.

A IA não confirma obstáculos pelo diretor, não aprova ou reprova planos pelo secretário, não altera score e não transforma estimativas em orçamento aprovado.

## Acesso e validação dos perfis

O protótipo representa uma escolha de perfil para demonstração. No produto, o acesso deverá ser restrito e validado: o diretor fica associado à sua escola; o secretário, à rede municipal autorizada. A confirmação de um e-mail ou telefone demonstra controle daquele canal, mas não prova sozinha o vínculo profissional. O fluxo proposto prevê validação institucional antes de liberar o módulo.

A integração com gov.br não faz parte do produto mínimo viável proposto nesta etapa.

## O que ainda será definido

O fluxo é uma proposta para discussão, não uma especificação aprovada para desenvolvimento. Ainda precisam ser validados, entre outros pontos:

- Quem pode confirmar o vínculo de diretores em cada tipo de rede escolar.
- Se o diretor pode pausar e retomar o registro de obstáculos e como pode retificar uma declaração confirmada.
- Quais documentos, dados orçamentários e históricos poderão ser usados como contexto da IA.
- Prazos e responsáveis pela análise municipal, bem como as regras de reenvio após ajustes ou reprovação.
- Como medir e explicar a prioridade das escolas e a cobertura parcial das ações municipais.
- Requisitos jurídicos, privacidade, retenção de dados e documentos exportáveis.

## Artefatos de trabalho

- [Protótipo navegável da Gestão Ativa](prototipo_gestao_ativa.html)
- [Documento de Requisitos do Produto da Fase 2](../docs/sdd/fase-2/prd.md)
- [Índice das funcionalidades e requisitos](../docs/sdd/fase-2/requirements/planos-de-acao.md)
