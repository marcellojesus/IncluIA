# Impacto da Fase 2 sobre a Fase 1

**Status:** Proposta para validação · 2026-10-18  
**Base:** [PRD da Fase 1](../fase-1/prd.md) (rotas observadas no código local) e [PRD da Fase 2](prd.md)

## Objetivo

Registrar, rota por rota, o que acontece com o produto em produção (Fase 1) quando a Gestão Ativa (Fase 2) entrar. A abordagem acordada é prototipar **somente as telas da Fase 1 que mudam**, antes do desenvolvimento, para que os pontos de contato entre as fases sejam decididos no protótipo e não durante a programação.

## Decisão por rota

| Rota da Fase 1 | Decisão | O que muda | Prototipar |
|---|---|---|---|
| `/municipio/{codigoIbge}` (dashboard público) | Ajusta | Acrescenta cobertura pública da Gestão Ativa: quantas escolas do município publicaram Declaração de Obstáculos, com acesso à lista | Sim, só o trecho novo |
| `/municipio/{codigoIbge}/escolas` (lista e ficha) | Ajusta | Lista: selo "Declaração publicada" e filtro correspondente. Ficha: barreiras da escola (conforme [metodologia de barreiras](../../../metodologia_barreiras.md)) e botão para ler a Declaração publicada, com data e versão | Sim |
| `/participar` (página em construção) | Substitui | Vira a porta de entrada da Gestão Ativa: o que é, para quem é, solicitação de acesso de diretor e acesso de secretário por convite | Sim |
| `/login` (login e autocadastro aberto) | Substitui | O autocadastro aberto não atende a Fase 2, que exige vínculo validado com escola ou rede. O login passa a ser só da Gestão Ativa | Já prototipado |
| `/municipio/{codigoIbge}/diagnostico` (Diagnóstico IA, área logada) | Remove como está; reaproveita | **Decisão de 2026-10-18 (opções 3 e 2):** (3) a narrativa por eixo e a infraestrutura de IA passam a ser o ponto de partida do Analítico de Barreiras do secretário; (2) uma narrativa municipal pública, somente leitura, sem chat e sem login, gerada uma vez por edição do Censo | Sim, as duas superfícies |
| `/metodologia` | Ajusta | Passa a exibir também a metodologia de barreiras | Não (conteúdo) |
| `/comparar`, `/sobre`, `/dados-abertos` | Mantém | Sem mudança funcional; textos de "Sobre" mencionam a Gestão Ativa | Não |
| Botões "Registrar uma barreira" (`BotaoRegistrarBarreira`) | Ajusta | Deixam de avisar "função futura" e levam a `/participar` | Não |

## Consequências da decisão sobre o Diagnóstico IA

- **Contas e histórico existentes:** a Fase 1 tem contas com autocadastro e histórico de conversas do chat por eixo. É preciso decidir se serão migradas, arquivadas ou excluídas, com aviso aos usuários (tratamento de dados pessoais).
- **Narrativa pública (opção 2):** gerada em lote, uma vez por edição do Censo e por município, e armazenada. Não chama IA em tempo real para visitantes, o que elimina custo e risco de abuso na área pública. Mantém as regras atuais: IA não decide números nem status, e só cita a base legal validada.
- **Analítico do secretário (opção 3):** reaproveita a cadeia de provedores, os prompts por eixo e a validação de base legal, agora com acesso restrito à rede do secretário e alimentado por Declarações emitidas e planos submetidos.
- **Chat de ajuste de recomendações:** não continua na área pública. A conversa com IA passa a existir só dentro da Gestão Ativa (Declaração, Plano de Ação e Analítico).

## Requisitos novos na área pública (a detalhar após o protótipo)

- **PUB-01:** a ficha pública da escola mostra as barreiras identificadas, com o texto e o campo do Censo de cada uma.
- **PUB-02:** a ficha pública da escola oferece acesso à Declaração de Obstáculos publicada mais recente, com data e versão; sem declaração publicada, informa que a escola ainda não publicou.
- **PUB-03:** a lista de escolas permite identificar e filtrar escolas com Declaração publicada.
- **PUB-04:** o dashboard municipal público mostra quantas escolas publicaram Declaração, sem expor dados privados da Gestão Ativa (planos, decisões, comentários).
- **PUB-05:** a narrativa municipal pública gerada por IA identifica a edição do Censo e a data de geração, e é rotulada como texto gerado por IA.

## Pendências

- Destino das contas e do histórico de chat da Fase 1.
- Se a narrativa municipal pública substitui o atual conteúdo da aba Diagnóstico na mesma rota ou ganha rota nova.
- Arquitetura da Fase 2 (persistência, autenticação, IA e hospedagem): ver discussão de arquitetura.
