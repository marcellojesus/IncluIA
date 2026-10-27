# Escola Sem Barreiras — Stack Tecnológica

## Frontend

| Camada | Tecnologia | Por quê |
|---|---|---|
| Framework | Next.js 16 (App Router) | React com roteamento, SSR e deploy trivial no Vercel |
| Linguagem | TypeScript | Tipagem evita bugs, essencial em projeto com muitos dados |
| Estilo | Tailwind CSS | Utilitário, rápido, sem conflito com Design System Gov.br |
| Mapa | React-Leaflet | Wrapper React do Leaflet.js — gratuito, sem API key |
| Gráficos | Recharts | Gráfico de barras de progresso dos eixos — gratuito |
| Estado global | Zustand | Leve, simples — guarda município selecionado, perfil do usuário |

> **Nota**: a versão original desta stack citava Next.js 14. Ao rodar `create-next-app` (etapa de scaffolding do frontend), a versão estável mais recente já era a 16 (com React 19) — optamos por seguir a versão mais atual em vez de fixar a 14, já defasada. React-Leaflet instalado na v5 (compatível com React 19) e Recharts na v3.

## Backend

| Camada | Tecnologia | Por quê |
|---|---|---|
| Framework | FastAPI | Moderno, assíncrono, tipado, gera docs automáticas |
| Linguagem | Python 3.11+ | Ecossistema de dados e IA superior |
| Dados do Censo | Pandas | Processamento dos microdados CSV do INEP |
| IA primária | Gemini 2.0 Flash | Free tier: 1.500 req/dia, 1M tokens contexto |
| IA fallback 1 | Groq LLaMA 3.3 70B | Free tier generoso, muito rápido |
| IA fallback 2 | Mistral Small | Terceira linha de segurança |
| Cache | SQLite | Diagnósticos de IA por 24h, sem custo |
| Servidor | Uvicorn | ASGI, roda o FastAPI |

## Transformação dos Dados do Censo (ETL do Score Escola Sem Barreiras)

### Onde este processo se encaixa

O Score Escola Sem Barreiras não é calculado em tempo real a cada requisição — ele é um **processo em lote (batch)**, executado uma vez por versão do Censo, que lê os microdados brutos do INEP e grava o resultado já pronto (escola, município e UF) em SQLite. A API (`backend/app/`) só lê esse resultado; toda a lógica de cálculo mora em `backend/etl/`, isolada da camada de API. Isso segue a metodologia oficial documentada em `metodologia_score.md` — o ETL é a implementação executável dela, não uma reinterpretação.

### Pipeline (`backend/etl/run_etl.py`, 4 etapas sequenciais)

| Etapa | Módulo | O que faz |
|---|---|---|
| 1. Carga | `load.py` | Lê `Tabela_Escola_2025.csv` e `Tabela_Matricula_2025.csv` (`base/microdados_censo_escolar_2025/dados/`) com Pandas — separador `;`, encoding `cp1252` (padrão dos microdados do INEP); filtra apenas escolas com `TP_SITUACAO_FUNCIONAMENTO = 1` ("Em Atividade"); faz `merge` das duas tabelas por `CO_ENTIDADE` (left join, matrícula ausente vira 0) |
| 2. Cálculo do score | `score.py` | Para cada escola, converte as variáveis brutas do Censo em 11 variáveis normalizadas (0 a 1) conforme `metodologia_score.md` §3–4, aplica os pesos oficiais (AEE 30%, taxa de inclusão em classe comum 15%, LIBRAS 15%, Braille 10%, rampa 8%, banheiro PNE 7%, corrimão 6%, piso tátil 4%, sinalização visual 2%, sinalização sonora 2%, elevador 1%) e soma para obter o score 0–10 de cada escola; classifica a escola em uma das 5 faixas (Crítico/Insuficiente/Em desenvolvimento/Adequado/Referência) |
| 3. Agregação | `aggregate.py` | Agrega o score das escolas para nível **município** e depois **UF**, por média ponderada pelo número de alunos com deficiência matriculados (`QT_MAT_ESP`) — não é uma média simples entre escolas, para que uma escola grande pese mais que uma escola de 3 alunos; também calcula o ranking de cada escola dentro do seu município |
| 4. Persistência | `persist.py` | Grava os 3 DataFrames resultantes (`escolas`, `municipios`, `uf_agregado`) em `data/incluia.db` (SQLite), com as colunas já renomeadas de `MAIUSCULO_CENSO` para `snake_case` — a API nunca lê o CSV bruto, só essas tabelas já processadas |

### Tecnologia

| Camada | Tecnologia | Por quê |
|---|---|---|
| Leitura/transformação | Pandas | Padrão de fato para processar CSVs de centenas de milhares de linhas (≈214 mil escolas) com filtros, merges e agregações vetorizadas |
| Formato de entrada | CSV oficial do INEP (`;`, `cp1252`) | Formato de distribuição original dos microdados do Censo Escolar — nenhuma conversão manual antes da leitura |
| Regra de cálculo | Funções puras em `score.py` (`calcular_variaveis`, `calcular_score_escola`, `classificar_faixa`), com os pesos e limiares como constantes no topo do módulo | Auditável e testável isoladamente — qualquer pessoa consegue conferir o cálculo de uma escola específica sem rodar o pipeline inteiro |
| Agregação ponderada | `numpy`/Pandas (`(score * QT_MAT_ESP).sum() / QT_MAT_ESP.sum()`), com *fallback* para média simples quando a soma de matrículas é zero | Reflete a metodologia (§6 de `metodologia_score.md`): município com mais alunos especiais matriculados numa escola pesa mais no score municipal daquela escola |
| Persistência | SQLite (mesmo arquivo `data/incluia.db` usado pela API) | Evita um banco separado só para o ETL — a API já sabe ler essas tabelas; reprocessar o Censo é só rodar `run_etl.py` de novo, que sobrescreve as tabelas |
| Verificação | *Sanity check* automático ao final do ETL (`run_etl.py`): recalcula manualmente o score de um município a partir das escolas e compara com o valor agregado, com `assert` de tolerância `1e-6` | Garante que a agregação em Pandas não diverge do cálculo linha a linha antes de considerar o resultado confiável para publicar |

### Quando reprocessar

O ETL é reexecutado manualmente (`python run_etl.py` dentro de `backend/`) sempre que uma nova versão dos microdados do Censo Escolar é publicada pelo INEP, ou se a metodologia (`metodologia_score.md`) mudar pesos/variáveis — nunca automaticamente a cada deploy, para não recalcular um dataset de ~214 mil escolas sem necessidade.

## Inteligência Artificial

### Onde o projeto usa IA (e onde não usa)

> **Atualização de 2026-10-27:** na área pública, a IA só escreve a leitura pública de cada município (`GET /municipios/{codigo}/narrativa`), guardada por edição do Censo, sem login, chat nem recomendações; o login da Fase 1 saiu do ar. Na Gestão Ativa, a IA apoia a Declaração de Obstáculos, o Plano de Ação e o Plano Estratégico Municipal — ver `docs/sdd/fase-2/arquitetura.md` (AD-05 e AD-08). O texto abaixo descreve a versão anterior.

A IA generativa é usada em **um único lugar do produto**: a feature `diagnostico-ia` (aba "🤖 Diagnóstico IA" da tela de município). Ela transforma os indicadores já calculados de cada eixo da PNEEI (Decreto 12.686/2025) em texto explicativo, alertas legais e recomendações com custo/prazo, em linguagem natural — e, a partir desta versão, também conversa com o gestor sobre esse diagnóstico via um chat por eixo (ver "Chat de ajuste de recomendações" abaixo).

**A IA nunca decide números ou status** — isso é uma regra de negócio explícita (RN-03 de `docs/business-rules/diagnostico-ia.md`): o Score Escola Sem Barreiras, as faixas de classificação (Crítico/Insuficiente/Em desenvolvimento/Adequado/Referência) e os semáforos ✅/⚠️/❌ de cada eixo são 100% calculados deterministicamente pelo ETL (`backend/etl/score.py`), a partir da metodologia em `metodologia_score.md`. A IA só recebe esse resultado já pronto como contexto e o explica — nunca o contrário. Isso evita que uma alucinação de modelo altere o "resultado oficial" de conformidade exibido ao gestor.

### Como está implementado

| Camada | Tecnologia | Por quê |
|---|---|---|
| Chamada às APIs | `httpx` (REST assíncrono direto) | Gemini, Groq e Mistral são todos acessíveis por REST simples (Groq/Mistral são compatíveis com o formato `chat/completions` da OpenAI) — evita instalar 3 SDKs pesados só para chamadas HTTP com JSON |
| Saída estruturada | JSON mode nativo de cada provedor (`responseMimeType`/`response_format`) | O modelo é obrigado a responder no formato exato de `DiagnosticoEixo`/`RecomendacaoIA`, validado com Pydantic (`app/features/diagnostico_ia/schemas.py`) — se o JSON vier inválido, é tratado como falha desse provedor |
| Cadeia de fallback | Gemini 2.0 Flash → Groq LLaMA 3.3 70B → Mistral Small → dados brutos sem IA | Ordem fixa (RN-01), 8s de timeout por provedor; qualquer falha (sem chave, timeout, erro HTTP, JSON inválido) cai pro próximo nível sem erro visível ao gestor (RN-02) — testado em produção real: o Gemini já caiu por rate-limit (429) e o sistema seguiu para o Groq automaticamente |
| Segredos | `python-dotenv` carrega `backend/.env` (`GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`) | Nunca commitado (`.gitignore`); `backend/.env.example` documenta as variáveis esperadas sem os valores reais |
| Cache | Tabela `cache_diagnosticos` em SQLite, TTL 24h, chave `SHA256(codigoIbge + eixo + versaoCenso)` | Evita chamar a IA de novo para o mesmo eixo/município no mesmo dia — reduz custo e latência; botão "Regenerar" (`?forcar=true`) ignora o cache quando o gestor quer atualizar |
| Privacidade | Só dados agregados e públicos do Censo entram no prompt (RN-04) | Nenhum dado pessoal de aluno/professor trafega para Gemini/Groq/Mistral — apenas contagens, percentuais e médias já calculados |

### Base legal validada contra o texto oficial

O prompt só permite citar uma base legal específica quando ela vier pré-validada no código (`_ARTIGO_VALIDADO_POR_EIXO` em `diagnostico_ia/service.py`); fora dessa lista, a IA só pode se referir à "PNEEI (Decreto 12.686/2025)" de forma geral, nunca inventar um artigo. Essa lista é validada contra o texto oficial de 3 fontes legais salvas em `base/legislacao/` (Decreto 12.686/2025, Decreto 12.773/2025 e o recorte educacional da Lei 13.146/2015 — LBI), com o mapeamento completo eixo → artigo em `docs/legislacao.md`. Ver RN-06 (revisada) em `docs/business-rules/diagnostico-ia.md`. Mesmo com citações validadas, o produto mantém o aviso permanente "⚠️ Em validação jurídica" (RN-02 de `docs/business-rules/indicadores-municipio.md`) — o mapeamento score↔lei continua sendo uma aproximação metodológica do produto, não uma certificação jurídica formal.

### Chat de ajuste de recomendações

Cada eixo do diagnóstico tem um chat próprio, para o gestor tirar dúvidas ou pedir o ajuste de uma recomendação (RN-09 de `docs/business-rules/diagnostico-ia.md`):

| Camada | Tecnologia | Por quê |
|---|---|---|
| Multi-turno | `ai_client.py::gerar_resposta` (generalização de `gerar_narrativa`) — mesma cadeia de fallback Gemini → Groq → Mistral, agora aceitando uma lista de mensagens em vez de um único prompt | Reaproveita 100% da infraestrutura de IA já validada em produção, sem duplicar lógica de fallback/timeout |
| Persistência | Tabelas `chat_diagnostico_mensagens` (histórico completo, append-only) e `chat_diagnostico_recomendacoes_ajustadas` (última recomendação ajustada por eixo/município) em SQLite | Histórico e ajuste sobrevivem a reload e a "Regenerar" o diagnóstico automático — a IA nunca decide isso sozinha, é uma ação explícita do gestor no chat |
| Restrição de escopo | O chat só pode citar a base legal listada em `docs/legislacao.md` para aquele eixo, e nunca altera o status/score (RN-03 continua valendo dentro do chat) | Mesmo princípio do diagnóstico automático, estendido a uma superfície interativa nova |

## Infraestrutura

| Camada | Tecnologia | Custo |
|---|---|---|
| Deploy frontend | Vercel | Gratuito |
| Deploy backend | Render | Gratuito (dorme após 15min de inatividade) |
| Banco de dados | SQLite no MVP | Gratuito |
| Polígonos do mapa | IBGE API pública | Gratuito |
| Repositório | GitHub | Gratuito |
