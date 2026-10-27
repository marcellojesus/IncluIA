# Documento de Requisitos do Produto (PRD) — Escola Sem Barreiras | Fase 1

**Status:** Engenharia reversa do código local concluída; especificação do comportamento observado  
**Versão:** 0.2  
**Data da observação:** 2026-10-11  
**Escopo:** frontend Next.js e backend FastAPI presentes no workspace. Não implica certificação do deploy de produção.

> **Atualização de 2026-10-27 (integração com a Fase 2):** o login e o autocadastro descritos aqui saíram do ar, e a área pública não pede conta. O Diagnóstico IA virou uma leitura pública do município, sem chat e sem recomendações. As fichas das escolas e a Início ganharam os dados públicos da Gestão Ativa. Detalhes em [impacto-fase-1.md](../fase-2/impacto-fase-1.md). O texto abaixo descreve a Fase 1 como observada em 2026-10-11.

## Resumo

A Fase 1 apresenta publicamente indicadores agregados do Censo Escolar sobre educação especial inclusiva, com referência à Política Nacional de Educação Especial Inclusiva (PNEEI). Visitantes podem navegar entre municípios, consultar scores e indicadores por eixo, consultar escolas e comparar rankings. Usuários com conta podem acessar o Diagnóstico com inteligência artificial (IA), que explica os indicadores por eixo e oferece chat de acompanhamento.

O produto informa que se trata de protótipo acadêmico e que a metodologia necessita revisão especializada. Score, semáforos e conformidade apresentados não são certificação jurídica.

## Problema e públicos

Os dados do Censo exigem processamento e contexto para serem compreensíveis em recortes territoriais e escolares. O produto atende:

- **Visitantes públicos:** pessoas interessadas em consultar, comparar e entender os dados exibidos.
- **Usuários autenticados:** pessoas com conta válida, que podem consultar o Diagnóstico IA de qualquer município.

Embora o login carregue um perfil, a autorização atual não restringe o município por papel nem implementa espaços de gestão distintos para secretário ou diretor. Esses perfis de Gestão Ativa pertencem à proposta da Fase 2.

## Jornadas e funcionalidades observadas

### Entrada e navegação municipal

- `GET /` busca municípios do Distrito Federal (DF) e encaminha para o painel (dashboard) de Brasília; se não houver município disponível, encaminha para `/sobre`.
- A estrutura pública inclui barra de acessibilidade, cabeçalho, seletor geográfico Região → unidade da Federação (UF) → Município e rodapé.
- O seletor navega para outro município mantendo a subtela Escolas ou Diagnóstico quando aplicável.
- A rota inexistente ou sem dados para um código municipal exibe “Município não encontrado”.

### Dashboard do município

Rota `/municipio/{codigoIbge}`, pública. Exibe título/contexto do município, score geral e faixa, situação nos quatro eixos, score por eixo, dados gerais da rede, atalhos para escolas/comparação/registro de barreira e ranking nacional de estados com o estado atual destacado.

### Escolas

Rota `/municipio/{codigoIbge}/escolas`, pública. Busca as escolas do município, permite filtrar “Todas”, “Situação crítica” ou “Sem Atendimento Educacional Especializado (AEE)”, abre uma ficha/modal ao selecionar escola e apresenta estados de carregamento/erro. Exportação permanece desabilitada, identificada como “em breve”.

### Comparação territorial

Rota `/comparar`, pública. Exibe ranking nacional de unidades da Federação (UFs) e ranking de municípios dentro de uma UF. Os rankings usam resultados calculados e disponibilizados pelo servidor de aplicação (backend).

### Diagnóstico IA

Rota `/municipio/{codigoIbge}/diagnostico`; o acesso à tela e, principalmente, a todas as rotas da interface de programação de aplicações (API) de diagnóstico requer token Bearer válido. Sem sessão, a interface encaminha ao login e preserva a rota de retorno. Qualquer conta autenticada pode consultar qualquer município; não há autorização por papel, escola, município ou UF.

O diagnóstico apresenta quatro eixos com narrativa, alerta legal, recomendações e referência comparativa; oferece regeneração, chat persistido por eixo, possível substituição de recomendações e ação explícita para reprocessar o diagnóstico com a conversa. A API tenta Gemini 2.0 Flash, Groq LLaMA 3.3 70B e Mistral Small em sequência, com tempo limite (timeout) de 8 segundos por provedor. A geração inicial pode recorrer a dados já calculados sem narrativa se os provedores falharem; erros da API podem ser apresentados como mensagem de tentativa posterior. O armazenamento temporário em cache e o histórico são persistidos em SQLite.

### Login e cadastro

Rota `/login`. Há autenticação por e-mail/senha, autocadastro público disponível na tela contextual do Diagnóstico IA e token JWT (JSON Web Token, “token web JSON”) codificado em JSON (JavaScript Object Notation, “notação de objeto JavaScript”), com expiração fixa de oito horas e senha armazenada com bcrypt. As contas de demonstração incluem João Silva e Maria Souza. “Sair” descarta a sessão no cliente; o ponto de acesso (endpoint) de logout não mantém estado de sessão no servidor. A autenticação única pelo gov.br (SSO, do inglês Single Sign-On) não está implementada.

### Informação, transparência e participação

- `/sobre`: explica o produto, mantém avisos de protótipo acadêmico e metodologia em construção, créditos acadêmicos e link do repositório.
- `/dados-abertos`: aponta para microdados oficiais, documentação da API e metodologia; declara que a plataforma não oferece exportação própria de conjuntos de dados (datasets).
- `/metodologia`: renderiza `metodologia_score.md`, sincronizado para o conteúdo do frontend antes de `dev` e `build`.
- `/participar`: página em construção para registro de barreiras. Botões visíveis na interface apenas informam que o recurso é futuro; não criam ou encaminham registros.
- Exportar escola/diagnóstico em Formato de Documento Portátil (PDF) não está implementado; os controles relevantes são desabilitados.

## Dados, cálculo e arquitetura observados

- A fonte processada é o Censo Escolar 2025, carregado em arquivo de valores separados por vírgula (CSV, do inglês Comma-Separated Values) pelo processo de extração, transformação e carga (ETL, do inglês Extract, Transform, Load) com Pandas em `backend/etl/`. O processo calcula score por escola e agrega escolas, municípios e unidades da Federação; os resultados são persistidos em SQLite.
- A API FastAPI lê os resultados preparados e expõe os pontos de acesso (endpoints) públicos de indicadores-chave de desempenho (KPIs, do inglês Key Performance Indicators), municípios por UF, rankings, detalhe municipal e escolas.
- Score total, faixas e indicadores determinísticos não são gerados pelo modelo de linguagem de grande escala (LLM, do inglês Large Language Model). O diagnóstico recebe dados agregados prontos; as citações legais específicas são limitadas ao mapeamento validado no serviço.
- Dados de autenticação, cache e chats também usam o SQLite local. O histórico do chat é persistido; ajustes de recomendação guardam o estado mais recente por município/eixo.

## Rotas e acesso

| Rota | Acesso observado | Capacidade |
|---|---|---|
| `/` | Público | Redireciona ao município padrão do DF |
| `/municipio/{codigoIbge}` | Público | Dashboard municipal |
| `/municipio/{codigoIbge}/escolas` | Público | Lista e ficha de escolas |
| `/comparar` | Público | Rankings de estados e municípios |
| `/municipio/{codigoIbge}/diagnostico` | Autenticado | Diagnóstico e conversa com IA |
| `/login` | Público | Login e cadastro contextual |
| `/sobre` | Público | Contexto, transparência e créditos |
| `/dados-abertos` | Público | Links para fonte, API e metodologia |
| `/metodologia` | Público | Metodologia do score |
| `/participar` | Público, placeholder | Funcionalidade de registro ainda ausente |

## Limites e itens não implementados

- Não existe fluxo funcional para diretores registrarem obstáculos nem workflow de gestão escolar.
- Não existem painel de secretário, analítico municipal de obstáculos, planos escolares/municipais LOA/PPA ou distribuição de metas.
- O registro público de barreiras, protocolo/encaminhamento e acompanhamento ainda não funcionam.
- Não há integração de autenticação única (SSO) pelo gov.br, aprovação de contas, segregação por papel/unidade, assinatura digital ou exportação em Formato de Documento Portátil (PDF) operacional.
- Não há integração de escrita com Educacenso nem série histórica implementada neste escopo.
- A aplicação local não comprova comportamento, disponibilidade ou configuração do deploy publicado.

## Critério de manutenção

Este documento descreve o comportamento encontrado no código local em 2026-10-11. Requisitos detalhados em `docs/requirements/` e regras em `docs/business-rules/` mantêm histórico e referências usadas pelo código; divergências devem ser reconciliadas em etapa documental própria para evitar mudar caminhos ou semântica em uso. A Fase 2 é descrita separadamente e não é considerada implementada.

## Referências para auditoria da engenharia reversa

| Área | Referências principais |
|---|---|
| Rotas e composição visual | `frontend/src/app/page.tsx`, `frontend/src/app/(app)/layout.tsx`, `frontend/src/shared/components/AppHeader.tsx`, `frontend/src/shared/components/GeoFiltroBar.tsx` |
| Dashboard e comparação | `frontend/src/features/indicadores-municipio/components/InicioMunicipio.tsx`, `frontend/src/features/comparar/`, `frontend/src/app/(app)/comparar/page.tsx` |
| Escolas | `frontend/src/app/(app)/municipio/[codigoIbge]/escolas/page.tsx`, `frontend/src/features/escolas/` |
| Diagnóstico, chat e autenticação | `frontend/src/features/diagnostico-ia/`, `frontend/src/features/login/`, `backend/app/features/diagnostico_ia/router.py`, `backend/app/shared/auth.py`, `backend/app/features/login/` |
| Contratos de API | `backend/app/main.py`, `backend/app/features/mapa/router.py`, `backend/app/features/indicadores_municipio/router.py`, `backend/app/features/escolas/router.py` |
| Dados e score | `backend/etl/run_etl.py`, `backend/etl/score.py`, `backend/etl/aggregate.py`, `backend/etl/persist.py`, `metodologia_score.md` |
| Páginas informativas e funções futuras | `frontend/src/app/(app)/sobre/page.tsx`, `frontend/src/app/(app)/dados-abertos/page.tsx`, `frontend/src/app/(app)/participar/page.tsx`, `frontend/src/shared/components/BotaoRegistrarBarreira.tsx` |

As referências identificam os pontos de implementação que fundamentaram este PRD. A presença de código no repositório, isoladamente, não significa que uma funcionalidade esteja alcançável na navegação ou ativa no produto; por isso o estado de cada capacidade foi descrito conforme as rotas e componentes efetivamente ligados.
