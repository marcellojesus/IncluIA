# IncluIA — Dashboard de Governança da Inclusão Escolar com IA

> Documento de Defesa do Produto — MVP5
> Mestrado em Governança e Transformação Digital · 2025
> Baseado nos Microdados do Censo Escolar da Educação Básica 2025 — INEP/MEC

## Principais atualizações do MVP5

- ✦ Navegação contextual — sem menu de módulos numerados
- ✦ Mapa interativo real com Leaflet.js + polígonos IBGE GeoJSON
- ✦ Módulos 2, 5 e 6 organizados pelos 4 Eixos da PNEEI (Decreto 12.686/2025)
- ✦ Fluxo Login → Mapa → Município → Abas contextuais

---

## 1. Contexto e Problema

O Brasil possui 2,45 milhões de alunos com deficiência matriculados na educação básica (Censo Escolar 2025 — INEP). Apesar do crescimento significativo nas matrículas, os dados revelam gaps críticos de governança que nenhuma ferramenta existente monitora de forma integrada e inteligente.

**📊 Dados críticos extraídos do Censo Escolar 2025**

- 98.310 escolas com alunos com deficiência não oferecem AEE → 1 milhão de alunos sem suporte
- 25.336 escolas com alunos ESP não possuem nenhum recurso de acessibilidade → 227 mil alunos afetados
- Apenas 1,9% das escolas têm professor de LIBRAS
- Apenas 0,3% têm revisor de Braille
- Score de acessibilidade varia de 1,2 (AM) a 4,4 (DF) — desigualdade invisível aos gestores

Em outubro de 2025, o Governo Federal publicou o Decreto 12.686/2025, que instituiu a Política Nacional de Educação Especial Inclusiva (PNEEI) — posteriormente alterado pontualmente pelo Decreto 12.773/2025, de dezembro de 2025 (formação de professores de AEE e de profissionais de apoio, PAEE/PEI, Fundeb; ver `docs/legislacao.md`). O decreto estabelece critérios objetivos de conformidade e exige que municípios e estados demonstrem seu cumprimento. Até junho de 2026, 5.512 municípios já aderiram à política. Nenhum possui ferramenta para mapear seus próprios gaps de desconformidade.

**O problema central**: para cumprir o decreto, gestores precisam tomar decisões concretas de alocação de recursos. Essas decisões exigem visibilidade sobre os gaps escola a escola — algo que o IncluIA oferece de forma inédita.

---

## 2. Por que o IncluIA é Inovador

### 2.1 Análise do Mercado Atual

| Capacidade | IRM Painel | Vínculo / INEP Data | IncluIA |
|---|---|---|---|
| Dados do Censo Escolar 2025 | ✅ | ✅ | ✅ |
| Granularidade por escola | ❌ | ❌ | ✅ |
| Score composto de inclusão | ❌ | ❌ | ✅ |
| Mapa coroplético interativo | ❌ | ❌ | ✅ |
| Conformidade com 4 Eixos da PNEEI | ❌ | Parcial | ✅ |
| IA generativa com diagnóstico por eixo | ❌ | Parcial | ✅ |
| Recomendações com estimativa de custo | ❌ | ❌ | ✅ |
| Benchmarking entre municípios | ❌ | ❌ | ✅ |

### 2.2 Os Três Diferenciais Inovadores

**🔬 Inovação 1 — Score IncluIA: Índice Inédito de Governança da Inclusão**
Calculado a partir de 11 variáveis do Censo Escolar (AEE, acessibilidade física, recursos humanos, taxa de inclusão em classe comum) organizadas em 3 dimensões e 4 eixos da PNEEI (Decreto 12.686/2025). Aplicado a 214 mil escolas e 5.570 municípios — inédito no setor público brasileiro.

**🤖 Inovação 2 — IA Generativa para Diagnóstico por Eixo de Política Pública**
Gemini 2.0 Flash (primário) com fallback para Groq LLaMA 3.3 70B e Mistral Small. Cache de 24h em SQLite para uso eficiente da API. Diagnósticos estruturados por Eixo I–IV, com análise de problemas, alertas legais e recomendações com estimativa de custo.

**⚖️ Inovação 3 — Conformidade com a PNEEI (Decreto 12.686/2025) como Produto**
Os 4 eixos da PNEEI são a espinha dorsal de todo o sistema: organizam o Score, os indicadores do município, o diagnóstico por escola e as recomendações da IA. O IncluIA traduz obrigações regulatórias em métricas automatizadas e acionáveis.

---

## 3. O Produto — IncluIA MVP5

O IncluIA é um dashboard de governança com IA que transforma os microdados do Censo Escolar em inteligência acionável para gestores de educação especial em secretarias municipais e estaduais.

### 3.1 Fluxo de Navegação

A navegação do MVP5 é inteiramente contextual — não há menu de módulos numerado. O fluxo é progressivo e lógico:

```
Login  →  Mapa do Estado  →  Clique no Município  →  Contexto do Município
                                    [ Aba: 📋 Indicadores ]  [ Aba: 🏫 Escolas ]  [ Aba: 🤖 Diagnóstico IA ]
```

O gestor entra no sistema e é imediatamente direcionado ao mapa do seu estado. Não há tela de menu ou lista de módulos. Ao clicar em um município (no mapa ou via combo box), uma barra de contexto persiste no topo da tela com 3 abas. O botão "← Mapa" retorna à visão territorial.

### 3.2 Perfis de Acesso

| Perfil | Tela inicial | Acesso a municípios | Funcionalidades |
|---|---|---|---|
| Secretário Estadual | Mapa do estado completo | Todos os municípios do estado | Ranking, comparativo, alertas estaduais |
| Secretário Municipal | Mapa do estado (município destacado) | Apenas seu município | Indicadores, escolas, diagnóstico IA |

O MVP5 prioriza o Secretário Municipal — perfil que tem responsabilidade direta sobre o cumprimento da PNEEI (Decreto 12.686/2025) e necessita de ação concreta escola a escola.

---

## 4. Módulos Funcionais

### Módulo 1 — Mapa da Inclusão + Score IncluIA por Município

**🎯 Gap que resolve**: o gestor não tem visão territorial do problema nem uma referência objetiva para comparar seu município. O Módulo 1 oferece leitura geográfica imediata via mapa coroplético interativo com polígonos reais (IBGE GeoJSON) e ranking lateral com melhores e piores municípios do estado.

**Tela 1: Mapa + KPIs Nacionais** — logo após o login, o gestor vê:

- Faixa de KPIs nacionais no topo: Municípios Críticos (score < 3), Escolas sem AEE, Score Nacional Médio, Municípios Mapeados
- Mapa interativo Leaflet.js com polígonos dos municípios do estado, coloridos pelo Score IncluIA
- Escala de cores: Crítico (vermelho #E52207), Insuficiente (laranja #E05C00), Em desenvolvimento (amarelo #E6B800), Adequado (verde #168821), Referência (azul #1351B4)
- Ranking lateral: 5 melhores e 5 piores municípios do estado com score e badge de status
- Tooltip ao passar o cursor: nome do município, score, status e botão "Ver detalhes"
- Combo box para busca/seleção direta do município

**Tecnologia do Mapa**

| Componente | Tecnologia | Custo |
|---|---|---|
| Biblioteca de mapas | Leaflet.js 1.9 (open source) | Gratuito |
| Tiles de fundo | OpenStreetMap | Gratuito |
| Polígonos dos municípios | IBGE API GeoJSON (servicodados.ibge.gov.br) | Gratuito |
| Nomes dos municípios | IBGE API localidades | Gratuito |

Nenhuma API key ou conta paga necessária. Os polígonos são carregados diretamente da API pública do IBGE, garantindo dados oficiais e atualizados.

### Módulo 2 — Detalhamento do Município

**🎯 Gap que resolve**: o gestor não tem como saber em quais dos 4 eixos do Decreto seu município está em conformidade. O Módulo 2 traduz os dados do Censo em um diagnóstico estruturado por eixo, com semáforos visuais, scores e detalhamento completo dos critérios legais exigidos.

Ao clicar em um município no mapa, o sistema navega para a tela de detalhe com uma barra de contexto persistente no topo, exibindo o nome do município, score geral com badge de cor, e as 3 abas de navegação.

**Aba 1: 📋 Indicadores**

*Seção 1 — Situação nos 4 Eixos da PNEEI (Decreto 12.686/2025):*

| Status | Eixo | Conformidade |
|---|---|---|
| ✅ | Eixo I — Oferta de Atendimento Educacional Especializado (AEE) | Adequado |
| ⚠️ | Eixo II — Acessibilidade Física e Recursos de Comunicação | Atenção |
| ❌ | Eixo III — Profissionais Especializados (LIBRAS, Braille) | Crítico |
| ✅ | Eixo IV — Inclusão em Classe Comum (taxa de matrícula inclusiva) | Adequado |

*Seção 2 — Score por Eixo (barras de progresso visuais)*: cada eixo exibe uma barra colorida com o valor numérico (0–10) e o status textual. As cores seguem a mesma escala do mapa: vermelho → laranja → amarelo → verde → azul.

*Seção 3 — Dados Gerais do Município (tabela)*: alunos com deficiência (total e por rede), escolas com AEE, taxa de inclusão em classe comum; comparativo com média estadual e média nacional.

*Seção 4 — Detalhamento Completo dos Critérios do Decreto (tabela expandida)*: cada variável do Censo mapeada ao artigo do Decreto correspondente; valor atual do município × meta × gap a fechar; indicador de tendência (melhora/piora vs. Censo 2024).

### Módulo 5 — Lista de Escolas do Município

**🎯 Gap que resolve**: o gestor precisa saber QUAIS escolas específicas priorizar. O Módulo 5 lista todas as escolas do município com seus indicadores por eixo e score individual, permitindo identificar rapidamente as escolas mais críticas e abrir o detalhamento completo de cada uma.

**Aba 2: 🏫 Escolas** — lista de todas as escolas do município com:

- Ícones de status por eixo (✅⚠️❌) — visão rápida da conformidade em cada dimensão do Decreto
- Score badge colorido (0–10) — identifica prioridade de intervenção
- Informações básicas: nome, bairro, rede (municipal/estadual/privada), total de alunos com deficiência
- Clique na escola → modal de detalhamento completo com todas as variáveis do Censo

**Modal de Detalhamento da Escola**: nome, endereço, rede e código INEP; score individual e posição no ranking municipal; tabela de conformidade por eixo do Decreto, com cada variável e seu valor; alertas específicos e recomendações priorizadas para aquela escola.

### Módulo 6 — Diagnóstico de IA por Eixo

**🎯 Gap que resolve**: dados brutos não viram ação. O Módulo 6 usa IA generativa para transformar os indicadores do município em um plano de ação estruturado por eixo do Decreto, com linguagem acessível ao gestor, alertas legais e recomendações com estimativa de custo.

**Aba 3: 🤖 Diagnóstico IA** — para cada um dos 4 Eixos do Decreto, a IA gera:

- **Análise do problema**: interpretação dos indicadores em linguagem natural
- **Alerta legal**: referência à base legal validada da PNEEI em risco de desconformidade (ver `docs/legislacao.md`)
- **Recomendações**: 3–5 ações prioritárias com estimativa de custo e prazo
- **Benchmarking**: comparação com municípios de perfil similar que já superaram o gap

**Estratégia de IA e Fallback**

| Prioridade | Modelo | Uso | Cache |
|---|---|---|---|
| 1 (Primário) | Gemini 2.0 Flash | Diagnóstico principal | SQLite 24h |
| 2 (Fallback) | Groq LLaMA 3.3 70B | Se Gemini indisponível | SQLite 24h |
| 3 (Fallback) | Mistral Small | Último recurso | SQLite 24h |

O cache de 24h em SQLite garante que diagnósticos repetidos não consomem créditos de API. A IA não é treinada nos dados — ela recebe o diagnóstico real do município como contexto e gera um plano de ação específico, auditável e acionável.

---

## 5. Score IncluIA — Metodologia

### 5.1 Visão Geral

O Score IncluIA é um índice composto de 0 a 10 calculado a partir de 11 variáveis do Censo Escolar 2025, organizadas em 3 dimensões alinhadas aos 4 Eixos da PNEEI (Decreto 12.686/2025).

| Eixo do Decreto | Dimensão Score | Variáveis Censo | Peso |
|---|---|---|---|
| Eixo I — Oferta de AEE | Acesso | TP_AEE, IN_SALA_ATENDIMENTO_ESPECIAL | 30% |
| Eixo II — Acessibilidade Física | Estrutura | IN_BANHEIRO_PNE, IN_ACESSIBILIDADE_RAMPAS, CORRIMAO, PISOS_TATEIS, VISUAL, SONORO | 30% |
| Eixo III — Profissionais Especializados | Capital Humano | QT_PROF_TRAD_LIBRAS, QT_PROF_REVISOR_BRAILLE | 25% |
| Eixo IV — Inclusão em Classe Comum | Acesso | QT_MAT_ESP_CC / QT_MAT_ESP (taxa) | 15% |

> **Nota**: pesos corrigidos para 30/30/25/15%, conforme a fonte oficial [`metodologia_score.md`](metodologia_score.md) §8 ("Alinhamento com a PNEEI"). O documento original `IncluIA_MVP5.docx` trazia 30/35/20/15%, uma imprecisão de redação — a Metodologia do Score (3 dimensões, pesos 45/25/30%) reagrupada pelos 4 eixos da PNEEI resulta exatamente em 30/30/25/15%, batendo com o protótipo funcional. Ver `docs/business-rules/score-incluia.md` RN-01 para o detalhamento dessa reconciliação.
>
> **Correção adicional**: a variável de "piso tátil" é `IN_ACESSIBILIDADE_PISOS_TATEIS` (confirmado no dicionário oficial do Censo 2025), não `IN_ACESSIBILIDADE_SINAL_TATIL` como constava antes — ver `metodologia_score.md` para o detalhe completo dessa e de outra correção (semântica de `TP_AEE`).

### 5.2 Cálculo por Nível

- **Score da escola**: média ponderada das 11 variáveis binárias/contínuas normalizadas para 0–10
- **Score do município**: média ponderada dos scores das escolas, ponderada por QT_MAT_ESP (alunos com deficiência)
- **Score do estado**: média ponderada dos scores municipais, ponderada por total de alunos ESP

### 5.3 Classificação dos Scores

| Faixa | Status | Cor | Interpretação |
|---|---|---|---|
| 0,0 – 2,9 | Crítico | #E52207 (vermelho) | Graves lacunas em múltiplos eixos do Decreto |
| 3,0 – 4,9 | Insuficiente | #E05C00 (laranja) | Lacunas severas — risco de não conformidade |
| 5,0 – 6,9 | Em desenvolvimento | #E6B800 (amarelo) | Progressos parciais — conformidade incompleta |
| 7,0 – 8,4 | Adequado | #168821 (verde) | Boa conformidade com o Decreto |
| 8,5 – 10,0 | Referência | #1351B4 (azul) | Referência nacional — práticas a serem replicadas |

---

## 6. Arquitetura Técnica

### 6.1 Stack do MVP5 (documento original)

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Frontend | HTML5 + CSS Gov.br Design System + JavaScript | Padrão Digital de Governo — acessibilidade nativa |
| Mapa | Leaflet.js 1.9 + OpenStreetMap + IBGE API GeoJSON | Open source, gratuito, sem API key |
| IA | Gemini 2.0 Flash / Groq LLaMA 3.3 70B / Mistral Small | Fallback automático com cache 24h |
| Cache | SQLite (diagnósticos IA) | Sem custo adicional, persistência local |
| Dados | Censo Escolar 2025 (INEP/MEC) — microdados públicos | Fonte oficial, atualização anual |
| Autenticação | gov.br SSO (produção) / email+senha (MVP) | Integração nativa para setor público |

> **Nota**: a stack efetivamente adotada para a implementação do projeto substitui o frontend vanilla HTML/JS por **Next.js 14 + TypeScript + Tailwind CSS + React-Leaflet + Recharts + Zustand**, mantendo Leaflet/OpenStreetMap/IBGE para o mapa e a mesma arquitetura de IA e cache. O backend usa **FastAPI + Python 3.11+ + Pandas**, com deploy em Vercel (frontend) e Render (backend).

### 6.2 Design System Gov.br

O IncluIA segue integralmente o Padrão Digital de Governo (design.gov.br), garantindo acessibilidade WCAG 2.1 e consistência visual com outros sistemas públicos federais:

- Cores primárias: Azul institucional #1351B4, Azul escuro #071D41, Amarelo #FFCD07
- Semáforos: Verde #168821 (conforme), Laranja #E05C00 (atenção), Vermelho #E52207 (crítico)
- Tipografia: Rawline (fonte oficial Gov.br)
- Componentes: botões, cards, badges, abas e tabelas seguem o DS Gov.br

---

## 7. Escopo de Entrega — MVP5 vs. Futuro

### 7.1 Entrega do MVP5

| Funcionalidade | Módulo |
|---|---|
| Login gov.br (simulado) com identificação de perfil | — |
| Mapa coroplético real com Leaflet.js + polígonos IBGE | 1 |
| KPIs nacionais no topo (críticos, sem AEE, score médio) | 1 |
| Ranking dos melhores/piores municípios do estado | 1 |
| Navegação contextual (sem menu de módulos) | Nav |
| Semáforos dos 4 Eixos da PNEEI (Decreto 12.686/2025) | 2 |
| Score por eixo com barras de progresso | 2 |
| Detalhamento completo dos critérios do Decreto | 2 |
| Lista de escolas com ícones por eixo e score badge | 5 |
| Modal de detalhamento da escola | 5 |
| Diagnóstico IA por eixo com recomendações e custo | 6 |
| Cache 24h SQLite para diagnósticos IA | 6 |
| Fallback automático entre modelos de IA | 6 |

### 7.2 Backlog — Fase 2

| Funcionalidade | Módulo |
|---|---|
| Série histórica do score (comparativo Censo 2023–2025) | 3 |
| Simulação de impacto de investimentos por escola | 4 |
| Exportação de relatórios PDF por município | 7 |
| Autenticação real via gov.br SSO | — |
| Granularidade nacional (todos os 5.570 municípios) | 1 |
| Perfil Secretário Estadual com visão consolidada | — |
| Alertas automáticos por e-mail/SMS (prazos do Decreto) | — |

---

## 8. Conclusão

O IncluIA MVP5 representa uma evolução significativa em relação ao MVP4:

- A navegação contextual — sem menu de módulos — torna a experiência mais intuitiva para o gestor municipal
- O mapa real com Leaflet.js e polígonos IBGE elimina a dependência de APIs pagas e oferece dados geográficos oficiais
- Os 4 Eixos da PNEEI (Decreto 12.686/2025) são o fio condutor de toda a experiência: do mapa ao diagnóstico da IA, passando pelos indicadores e escolas
- O diagnóstico de IA por eixo fecha o ciclo: dados → indicadores → escolas prioritárias → plano de ação

### 🎯 Proposta de Valor Síntese

O IncluIA responde em segundos às perguntas que hoje demandam semanas de análise manual:

- Meu município está em conformidade com a PNEEI (Decreto 12.686/2025)?
- Quais escolas priorizar para maximizar o impacto?
- Quanto vai custar e quanto tempo vai levar para fechar os gaps?

Nenhuma ferramenta no Brasil faz isso hoje.

O produto está pronto para demonstração com dados simulados do estado do Rio de Janeiro, cobrindo municípios com perfis críticos (Cardoso Moreira, Italva, Trajano de Moraes) e adequados (Niterói, Rio de Janeiro, Petrópolis), permitindo validar toda a experiência de uso do secretário municipal.
