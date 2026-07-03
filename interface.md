# IncluIA — Especificação de Interface (a partir do protótipo `prototipo_inclua.html`)

> Este documento descreve, tela a tela e componente a componente, a interface navegável já prototipada em HTML/CSS/JS estático (dados mockados, mapa e IBGE reais). Serve como a fonte única de verdade da UI para a implementação em Next.js + Tailwind, e como base para os arquivos de requisitos e regras de negócio.

---

## 0. Identidade visual (Design System Gov.br)

**Cores institucionais**
| Token | Cor | Uso |
|---|---|---|
| `--blue` #1351B4 | Azul institucional | Ações primárias, cabeçalho do app, links |
| `--blue-dark` #071D41 | Azul escuro | Header gov.br, barra de contexto do município, modal header |
| `--blue-mid` #0C326F | Azul médio | Hover de botão primário, gradiente do login |
| `--blue-lt` #DBE8FB | Azul claro | Fundo de badges/realces, hover de linha de tabela |
| `--green` #168821 / `--green-lt` #E3F2E5 | Verde | Status "Adequado" / "Conforme" |
| `--orange` #E05C00 / `--orange-lt` #FDF2EA | Laranja | Status "Insuficiente" / "Atenção" / "Parcial" |
| `--red` #E52207 / `--red-lt` #FDE8E5 | Vermelho | Status "Crítico" / "Não conforme" / alertas legais |
| `--yellow` #E6B800 / `--yellow-lt` #FFF8D6 | Amarelo | Status "Em desenvolvimento" |
| Cinzas `--g1`…`--g6` | #f8f8f8 → #333 | Fundos, bordas, texto secundário |

**Tipografia**: Rawline (fonte oficial gov.br), fallback Raleway/sans-serif. Corpo de texto em 14px (13px em painéis, 11–12px em rótulos/legendas).

**Componentes reutilizáveis** (usados em várias telas — devem virar componentes React compartilhados):
- **Header gov.br** (`.gtop`): barra escura fixa no topo com selo tricolor (verde/amarelo/azul), texto "gov.br" e nome do sistema/órgão à direita (`Ministério da Educação · INEP`).
- **Header do app** (`.gmain`): faixa azul com logo "IncluIA" (clicável → volta ao mapa), subtítulo, e no canto direito usuário logado (`👤 Nome — Cargo · Município/UF`) + botão "Sair".
- **Badge** (`.badge`): pílula colorida (verde/amarelo/laranja/vermelho/azul) para status textual (ex.: "Adequado", "Crítico", "Conforme").
- **Painel** (`.panel` / `.ph` / `.pb`): card branco com cabeçalho (título + ação opcional à direita) e corpo com padding.
- **KPI** (`.kpi`): bloco com borda colorida à esquerda, rótulo em caixa alta, valor grande, subtítulo.
- **Semáforo** (`.sem`): card colorido (verde/amarelo/vermelho) com ícone, rótulo do eixo, valor e subtexto — usado na aba Indicadores.
- **Barra de progresso** (`.prog`): rótulo + valor à direita, barra de fundo cinza com preenchimento colorido proporcional ao score (0–10 → 0–100%).
- **Tabela** (`.tbl`): cabeçalho azul com texto branco, linhas com hover azul-claro, variante `.clickable` (cursor pointer, usada na lista de escolas).
- **Modal** (`.modal-bg` / `.modal`): overlay escuro + card centralizado com header azul-escuro e botão de fechar (✕).
- **Botões** (`.btn`): variante primária (`.btn-p`, fundo azul) e outline (`.btn-o`, borda azul).

**Acessibilidade**: WCAG 2.1 é requisito transversal (herdado do Design System Gov.br) — contraste de cores, navegação por teclado e leitura de tela devem ser validados na implementação, ainda que o protótipo estático não os implemente explicitamente.

---

## 1. Fluxo geral de navegação

```
Tela de Login
     │ (Entrar)
     ▼
App (header gov.br + header IncluIA sempre visíveis)
     │
     ▼
Tela "Mapa da Inclusão"  ←───────────────┐
     │ (clique em município no mapa,         │ botão "← Mapa"
     │  no popup, ou no ranking lateral)      │
     ▼                                        │
Tela "Contexto do Município" ───────────────┘
     │
     ├─ Aba 📋 Indicadores   (aba padrão ao entrar)
     ├─ Aba 🏫 Escolas       (clique em linha → Modal de Detalhamento da Escola)
     └─ Aba 🤖 Diagnóstico IA
```

Não existe menu de módulos numerados nem sidebar de navegação — a navegação é 100% contextual: o usuário sempre está "no mapa" ou "dentro de um município", e dentro do município alterna entre as 3 abas sem recarregar a página nem perder o contexto (nome/score do município permanecem fixos na barra superior).

---

## 2. Tela: Login (`#login-page`)

Layout de tela cheia dividida em duas colunas (grid 1fr/1fr), com o header gov.br fixo no topo e um footer institucional.

**Coluna esquerda** (fundo gradiente azul escuro → azul institucional):
- Logo "IncluIA" (48px, branco, bold)
- Tagline: "Dados do Censo Escolar 2025 transformados em decisões de inclusão para gestores públicos."
- Selo/pill: "⚖️ Alinhado à PNEEI (Decreto 12.686/2025)"
- 3 estatísticas de impacto, cada uma com valor grande + descrição:
  - **2,45M** — alunos com deficiência matriculados no Brasil
  - **98.310** — escolas sem nenhum AEE registrado no Censo
  - **5.570** — municípios mapeados com Score IncluIA

**Coluna direita** (fundo branco), formulário de acesso:
- Título "Entrar no IncluIA" + subtítulo "Acesso a gestores de secretarias de educação."
- Botão "Entrar com gov.br" — **desabilitado**, com badge "Fase 2" (visualmente presente mas não funcional no MVP)
- Divisor "acesso MVP"
- Campo "E-mail institucional" (pré-preenchido no protótipo: `joao.silva@niteroi.rj.gov.br`)
- Campo "Senha" (pré-preenchido: `demo1234`)
- Botão "Entrar" — ao clicar, mostra estado de carregamento ("⏳ Entrando…", desabilitado) por ~800ms e então revela o app
- Nota informativa: "Na Fase 2, o acesso via gov.br identificará automaticamente o perfil e o município do gestor."

Não há tela de "esqueci minha senha", cadastro ou recuperação de conta no MVP — o login é uma simulação de autenticação (ver `docs/business-rules/login.md`).

---

## 3. Tela: Mapa da Inclusão (`#screen-mapa`)

Primeira tela após o login. Estrutura vertical: faixa de KPIs → área principal (mapa + ranking) dividida em grid `1fr / 300px`.

### 3.1 Faixa de KPIs nacionais (topo, 5 colunas)
| KPI | Valor exemplo | Subtexto |
|---|---|---|
| Municípios Críticos | 1.843 (vermelho) | "Score < 3,0 · Brasil" |
| Escolas sem AEE | 98.310 (laranja) | "+1 mi de alunos sem suporte" |
| Score Médio Nacional | 3,8 (neutro) | "Escala 0–10 · IncluIA 2025" |
| Score Desejado | 7,0 (azul) | "Limiar da faixa Adequado" — ver `docs/business-rules/mapa.md` RN-07 |
| Municípios Mapeados | 5.570 (verde) | "214 mil escolas analisadas" |

### 3.2 Painel do mapa (coluna esquerda, `flex: 1`)
- **Toolbar**: select de UF (`RJ`, `SP`, `MG`, `BA` no protótipo — deve cobrir os 26 estados + DF na versão real) e select de Município da UF selecionada (busca/seleção direta, alternativa a clicar no mapa); texto de apoio "ou clique no mapa". Ao lado do select de município, uma **legenda de score** (badge colorido com o score do município atualmente focado) aparece assim que algum município é focado — via clique no mapa, no ranking lateral (§3.3) ou seleção neste próprio combo; fica oculta enquanto nenhum município estiver focado (RF-11 de `docs/requirements/mapa.md`).
- **Mapa Leaflet** ocupando o espaço restante:
  - Tiles OpenStreetMap.
  - Camada coroplética (GeoJSON de municípios da UF via API IBGE), cor de preenchimento por Score IncluIA usando a escala de 5 cores (ver §6 de `context.md`).
  - Estado de carregamento: overlay central com spinner + texto "Carregando mapa IBGE…" enquanto os dados do IBGE não retornam; mensagem de erro "⚠️ Erro ao carregar mapa IBGE." se a requisição falhar.
  - Interações por município: `hover` (destaca borda escura e aumenta opacidade), `click` (abre popup Leaflet com nome, UF, score, badge de status e botão "Ver indicadores do município →").
  - Ao trocar de UF, o mapa recarrega o GeoJSON, reajusta o zoom (`fitBounds`) e repopula o combo de municípios.
  - **Legenda do Score IncluIA**: card fixo no canto inferior esquerdo do mapa, com um quadrado colorido + nome para cada uma das 5 faixas (Crítico → Referência) — explica as cores do mapa coroplético sem precisar clicar em nenhum município (RF-12 de `docs/requirements/mapa.md`).

### 3.3 Painel de Ranking (coluna direita, 300px fixo)
- Título dinâmico: "Ranking — {Nome da UF}"
- Lista rolável dividida em 2 seções:
  - **🏆 Melhores**: top 5 municípios da UF por score, numerados 1–5, cada item com nome, mini barra de progresso colorida e score.
  - **⚠️ Críticos (Score < 3,0)**: últimos municípios da UF nessa faixa, numerados pela posição real no ranking (ex.: "90", "91", "92" de 92 municípios).
- Clique em um item do ranking foca o município no mapa (`fitBounds` + abre o popup) e marca o item como `active` (fundo azul claro).
- Clique em um município no mapa também sincroniza o destaque no item correspondente do ranking.

---

## 4. Barra de Contexto do Município (`.ctx-bar`)

Aparece fixa no topo assim que um município é aberto, substituindo a tela de mapa. Contém, da esquerda para a direita:
1. Botão "← Mapa" — retorna à tela do mapa (mantendo a UF selecionada).
2. Nome do município (destaque) + "Nome do Estado — UF" (subtítulo).
3. **Score geral do município**, alinhado à direita: valor numérico grande colorido conforme a faixa, rótulo "Score IncluIA" e badge de status (ex.: "Adequado").
4. **3 abas de navegação**, sempre visíveis, com indicador de aba ativa (sublinhado amarelo `#FFCD07`):
   - `📋 Indicadores` (aba padrão ao abrir um município)
   - `🏫 Escolas`
   - `🤖 Diagnóstico IA` — única aba que exige login (RN-06 de `docs/business-rules/login.md`); sem sessão ativa, clicar nela redireciona para `/login` e volta para esta mesma aba/município após autenticar, em vez de trocar de aba localmente.

Trocar de aba não recarrega a barra de contexto nem perde a posição de rolagem entre abas diferentes — cada aba é um painel independente que é mostrado/ocultado.

---

## 5. Aba: 📋 Indicadores

Texto de apoio no topo: "Situação em relação aos **4 eixos da PNEEI (Decreto 12.686/2025)**."

### 5.1 Grade de Semáforos (4 cards, um por eixo)
Cada card exibe: ícone de status (✅/⚠️/❌), rótulo do eixo, um valor-resumo (ex.: "68%", "Parcial", "Déficit") e um subtexto explicativo curto (ex.: "das escolas ofertam", "piso tátil pendente"). A cor de fundo do card (verde/laranja/vermelho claro) reflete o status.

### 5.2 Painel "Score por Eixo"
Uma barra de progresso por eixo (0–10), com rótulo incluindo o peso do eixo (ex.: "Eixo I — AEE (30%)"), valor numérico colorido à direita e barra preenchida proporcionalmente, na cor correspondente à faixa de classificação daquele eixo especificamente (não necessariamente a mesma faixa do score geral do município).

### 5.3 Painel "Dados Gerais"
Tabela chave/valor simples (sem cabeçalho, linhas com separador), com pares como:
Total de alunos ESP · Escolas com AEE (% e fração) · % em classe comum · Score médio estadual (comparativo) · Professores LIBRAS (contagem) · Revisores Braille (contagem) · % escolas com rampa · % piso tátil · % banheiro PNE · Ranking do município no estado (ex.: "#1 de 92").

### 5.4 Painel "Detalhamento — PNEEI (Decreto 12.686/2025)"
Tabela expandida mapeando cada critério legal à variável do Censo correspondente, com aviso fixo no cabeçalho do painel: **"⚠️ Em validação jurídica"**. Colunas: Eixo (com `rowspan` agrupando critérios do mesmo eixo) · Critério do Decreto · Variável Censo 2025 (nome técnico, ex.: `TP_AEE`, `IN_ACESSIBILIDADE_RAMPAS`) · Resultado (valor observado) · Conformidade (badge: ✅ Conforme / ⚠️ Parcial / ❌ Não conforme / 🔵 Em apuração).

Linhas do protótipo (referência de granularidade esperada):
- **I — AEE**: Oferta de AEE na escola (`TP_AEE ≠ 0`); Sala de recursos multifuncional (`IN_SALA_ATENDIMENTO_ESPECIAL`)
- **II — Acessibilidade**: Rampa de acesso; Banheiro adaptado PNE; Piso tátil; Corrimão e guarda-corpo
- **III — Profissionais**: Tradutor/intérprete de LIBRAS (`QT_PROF_TRAD_LIBRAS > 0`); Revisor de Braille (`QT_PROF_REVISOR_BRAILLE > 0`)
- **IV — Inclusão CC**: Taxa de matrícula em classe comum (`QT_MAT_ESP_CC / QT_MAT_ESP`)

---

## 6. Aba: 🏫 Escolas

Texto de apoio: "Score e situação de cada escola nos eixos da PNEEI (Decreto 12.686/2025)."

**Barra de ações** (acima da tabela): select de filtro (`Todas as escolas` / `Situação crítica` / `Sem AEE`) e botão "📄 Exportar" (sem lógica real no protótipo — ver requisitos).

**Tabela de escolas** (clicável, linha inteira aciona o modal):
| Coluna | Conteúdo |
|---|---|
| Escola | Nome em negrito + bairro em cinza abaixo |
| Rede | Badge azul: Municipal / Estadual / Privada |
| Alunos ESP | Contagem, centralizado |
| Eixo I AEE | Ícone ✅/⚠️/❌ |
| Eixo II Acessib. | Ícone ✅/⚠️/❌ |
| Eixo III Prof. | Ícone ✅/⚠️/❌ |
| Eixo IV CC | Ícone ✅/⚠️/❌ |
| Score | Badge colorido 0–10 (1 casa decimal, vírgula) |

O filtro "Situação crítica" mostra escolas com `score < 3`; o filtro "Sem AEE" mostra escolas com ícone de AEE = ❌. Sem seleção, mostra todas.

### 6.1 Modal de Detalhamento da Escola
Aberto ao clicar em qualquer linha da tabela. Header azul-escuro com nome da escola e subtítulo "{Município} — {UF} · Rede {rede} · {bairro}", botão de fechar (✕).

Corpo do modal:
- 4 mini-cards em grade (um por eixo), cada um mostrando apenas o ícone grande (✅/⚠️/❌) e o rótulo do eixo — visão rápida de conformidade.
- Tabela chave/valor: Alunos com deficiência (ESP) · Bairro/Região · Rede de ensino · **Score IncluIA** (destaque, número grande colorido).
- Botão "Fechar" (largura total) ao final.

> No protótipo o modal não exibe endereço, código INEP nem posição no ranking municipal, apesar de a documentação MVP5 prever esses campos — isso deve ser resolvido no requisito da funcionalidade (ver `docs/requirements/escolas.md`).

---

## 7. Aba: 🤖 Diagnóstico IA

Texto de apoio: "Análise gerada por **Gemini 2.0 Flash** com base nos dados do Censo Escolar 2025 · Cache de 24h."

**Ações no topo**: botão primário "🔄 Regenerar" (mostra estado "⏳ Gerando…" desabilitado por ~2s no protótipo) e botão outline "📄 Exportar PDF" (sem lógica real — funcionalidade de Fase 2).

**Painel único** com cabeçalho "Diagnóstico por Eixo do Decreto" e metadado à direita: "Gerado em {X}s · atualizado há {Y}h" (rastreabilidade de quando/como o diagnóstico foi gerado).

**Corpo do diagnóstico**, repetido para cada um dos 4 eixos, nesta ordem fixa (I → II → III → IV):
1. Título da seção do eixo (ícone temático + nome do eixo, ex.: "⚖️ Eixo I — Oferta de Atendimento Educacional Especializado (AEE)")
2. Um ou dois parágrafos de análise em linguagem natural, com termos-chave em negrito (percentuais, contagens críticas)
3. (Opcional, quando há risco legal) Bloco de **alerta** (fundo vermelho claro, borda vermelha): "🚨 Alerta:" ou "🚨 Risco legal:" citando a base legal validada para aquele eixo (Decreto 12.686/2025 ou Lei 13.146/2015 — LBI, conforme `docs/legislacao.md`) em risco de descumprimento
4. Bloco de **recomendação** (fundo azul claro, borda azul): "💡 Recomendação:" ou "💡 Ação urgente:" com ação concreta, estimativa de custo (R$), prazo e, quando aplicável, fonte de financiamento (PDDE, FNDE, PAR) — se a recomendação já foi ajustada pelo secretário via chat, exibir a etiqueta "✏️ Recomendação ajustada em {data}" acima dela
5. Toggle "💬 Conversar sobre este eixo": expande um painel de chat inline (histórico persistido), onde o secretário tira dúvidas ou pede o ajuste da recomendação — ver `docs/business-rules/diagnostico-ia.md` RN-09

Não há paginação nem "carregar mais" — os 4 eixos são exibidos em sequência dentro de um único painel rolável; cada chat expandido, por sua vez, tem sua própria área rolável de mensagens.

---

## 8. Estados e comportamentos transversais

- **Carregamento do mapa**: overlay com spinner (ver §3.2); nenhuma outra tela do MVP tem estado de loading assíncrono no protótipo (dados de indicadores/escolas/IA são preenchidos de mock local, instantâneos) — na implementação real, os 3 painéis do município (Indicadores, Escolas, Diagnóstico IA) e a lista de municípios/ranking dependerão de chamadas à API e precisarão de estados de loading/erro próprios.
- **Persistência de contexto**: nome, UF e score do município selecionado ficam fixos na barra de contexto ao trocar de aba; o filtro de escolas e o scroll de cada aba não são persistidos entre trocas de aba no protótipo (não testado, assumir reset).
- **Logout**: botão "Sair" no header do app volta para a tela de login e reseta a tela ativa para o mapa (não preserva UF/município selecionados).
- **Responsividade**: o protótipo é fixo para desktop (`overflow:hidden`, `height:100vh`, grids fixos) — não há layout mobile/tablet definido; isso é uma lacuna a ser tratada no design da implementação real caso haja requisito de uso em campo/tablet.

---

## 9. Estruturas de dados de referência (extraídas do mock do protótipo)

Estas estruturas descrevem o *shape* de dados que a interface consome — usadas como base para os contratos de API e modelos em `docs/requirements/` e `docs/business-rules/`.

**Município (resumo, usado no mapa/ranking)**
```
{ codigoIbge, nome, uf, score }
```

**Município (detalhe, usado nas abas Indicadores/IA)**
```
{
  eixos: [ { status: 'ok'|'warn'|'nok', icone, label, valor, subtexto } ]   // 4 itens, eixos I–IV
  scoreEixos: [ { label, percentual, valor, cor } ]                        // 4 itens, score 0–10 por eixo
  dados: [ [rótulo, valor] ]                                               // pares chave/valor livres
  diagnosticoIA: string (HTML/markdown estruturado por eixo)
}
```

**Escola (linha da lista)**
```
{ nome, bairro, rede: 'Municipal'|'Estadual'|'Privada', alunosEsp,
  statusEixoI, statusEixoII, statusEixoIII, statusEixoIV,  // ✅ | ⚠️ | ❌
  score }
```

Nenhum código INEP, endereço completo ou posição individual no ranking municipal está presente no objeto de escola do protótipo — avaliar inclusão no modelo real (ver `docs/requirements/escolas.md`).
