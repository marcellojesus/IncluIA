# Impacto da Fase 2 sobre a Fase 1

**Status:** Implementado em 2026-10-27, salvo os itens marcados como pendentes abaixo · proposta de 2026-10-18  
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

## Situação em 2026-10-27

Decisões do responsável em 2026-10-27: os botões "Registrar barreira" viram entrada da Gestão Ativa; o login da Fase 1 sai do ar já; o Diagnóstico IA vira narrativa pública sem login; PUB-01, PUB-03, PUB-04 e os textos institucionais entram nesta revisão.

| Rota ou elemento | Situação | Onde |
|---|---|---|
| Cabeçalho | "Registrar barreira" e "Entrar/Sair" do login antigo deram lugar a um único botão **Gestão Ativa** (leva a `/participar`). | `shared/components/AppHeader.tsx` |
| `/municipio/{codigoIbge}` (Início) | Bloco "O que as escolas publicaram" com as contagens de Declarações e Planos publicados (PUB-04) e cartão de entrada da Gestão Ativa. No topo, "Sou gestor: Gestão Ativa"; o card "Registrar uma barreira" virou "Entender os números" (leitura com IA). | `indicadores-municipio/components/GestaoAtivaMunicipio.tsx`, `InicioMunicipio.tsx` |
| `/municipio/{codigoIbge}/escolas` | Ficha: barreiras do Censo (PUB-01, rota `GET /escolas/{co}/barreiras`), Declaração e Plano publicados (PUB-02, desde 2026-10-24, exibidos na própria ficha em vez de botão). Lista: selos e filtros por Declaração e por Plano publicados (PUB-03). | `escolas/components/BarreirasEscola.tsx`, `DeclaracaoPublicaEscola.tsx`, `AbaEscolas.tsx` |
| `/participar` | Porta da Gestão Ativa (desde 2026-10-23), com um aviso para quem não é gestor voltar à área pública. | `gestao-ativa/components/ParticiparGestao.tsx` |
| `/login` | Desativado: redireciona para `/gestao/entrar`. Backend `/auth/*`, autocadastro e `INCLUIA_JWT_SECRET` removidos. | `app/login/page.tsx` |
| `/municipio/{codigoIbge}/diagnostico` | Narrativa pública só leitura, sem login e sem chat, guardada por edição do Censo e rotulada como texto de IA (opção 2, PUB-05). Recomendações com custo, chat e "Regenerar" saíram. | `diagnostico_ia/` (backend e frontend), `docs/requirements/diagnostico-ia.md` |
| `/sobre`, `/dados-abertos`, rodapé | Citam a Gestão Ativa e o que dela é público. | `app/(app)/sobre`, `app/(app)/dados-abertos`, `shared/components/Footer.tsx` |
| `/metodologia` | Já exibia a metodologia de barreiras (`/metodologia/barreiras`). | — |

### Pendências que continuam

- **Contas e histórico de chat da Fase 1:** em 2026-10-27 as tabelas `usuarios` e de chat foram apagadas de `data/incluia.db`, e o cache de narrativas foi esvaziado (o arquivo versionado volta a ter só o resultado do ETL). Continuam nos commits antigos publicados no GitHub; apagar de lá exige reescrever o histórico e forçar o envio, junto com a limpeza da chave do Gemini.
- **Analítico do secretário (opção 3):** reaproveitar a IA da narrativa no Analítico de Barreiras, na entrega do Analítico.
- **Exportações** ("Exportar (em breve)" na aba Escolas): continuam fora do escopo.
- **Contagem de alunos na área pública:** corrigida em 2026-10-27 (RN-06 de `docs/business-rules/escolas.md`). Fica o risco residual de recalcular o score real de uma escola pequena a partir do score do município, descrito na RN-06.
- **Limites em memória:** o limite por IP vê o IP do proxy do Render (vale para o site inteiro) e, como o teto diário de 200 gerações da narrativa, é por processo. Pré-gerar as narrativas com `python -m app.features.diagnostico_ia.cli gerar <UF>` a cada edição do Censo.
- **Sessão no cabeçalho:** o botão "Gestão Ativa" leva sempre a `/participar`, mesmo para quem já entrou; a sessão da Gestão Ativa fica só na aba do navegador.
