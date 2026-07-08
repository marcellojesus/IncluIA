# Requisitos — Mapa da Inclusão (Módulo 1)

Fonte de interface: `interface.md` §3. Fonte de contexto: `context.md` (Módulo 1).

> **Status atual (rastreabilidade)**: a tela dedicada de Mapa descrita abaixo não existe mais como rota própria do produto — ver RN-00 de `docs/business-rules/mapa.md`. RF-01 a RF-12 documentam a especificação original e ficam mantidos por histórico. Hoje a navegação por UF/município é o filtro em cascata do cabeçalho (`GeoFiltroBar.tsx`), e o ranking passou a viver na Início do município e na tela `/comparar` (ver [[indicadores-municipio]] e [[comparar]]). O ranking nacional de estados (RF-13) é a única funcionalidade deste módulo que é genuinamente nova desde a redação original.

## Objetivo

Dar ao gestor uma visão territorial imediata do estado (ou do seu município, se perfil Municipal), com KPIs nacionais, mapa coroplético por Score Escola Sem Barreiras e ranking dos melhores/piores municípios.

## Atores

Secretário Estadual (visão completa da UF) e Secretário Municipal (visão da UF com o próprio município em destaque, conforme `docs/business-rules/login.md` RN-03).

## Pré-condições

- Usuário autenticado.
- Score Escola Sem Barreiras já calculado para todos os municípios da UF (depende de [[score-incluia]]).

## Requisitos Funcionais

- **RF-01**: Exibir 5 KPIs nacionais no topo: Municípios Críticos (score < 3,0), Escolas sem AEE, Score Médio Nacional, Score Desejado (ver `docs/business-rules/mapa.md` RN-07), Municípios Mapeados — com contagens/valores atualizados a partir do dataset vigente.
- **RF-02**: Exibir um seletor de UF cobrindo os 26 estados + Distrito Federal (o protótipo cobre apenas RJ/SP/MG/BA como amostra — a implementação real deve suportar todas as UFs).
- **RF-03**: Exibir um seletor de município (busca/seleção direta) que lista os municípios da UF selecionada, como alternativa a clicar no mapa.
- **RF-04**: Renderizar um mapa coroplético dos municípios da UF selecionada, usando polígonos GeoJSON reais da API do IBGE, coloridos conforme a faixa de Score Escola Sem Barreiras de cada município (ver [[score-incluia]] para as faixas/cores).
- **RF-05**: Ao passar o cursor sobre um município no mapa, destacar visualmente o polígono (borda e opacidade).
- **RF-06**: Ao clicar em um município (no mapa, no popup, ou no ranking lateral), abrir a tela de Contexto do Município correspondente (ver [[indicadores-municipio]]).
- **RF-07**: Exibir um painel de ranking lateral com os 5 melhores e os municípios em situação crítica (score < 3,0) da UF selecionada, cada um com posição, nome, barra de progresso do score e valor do score.
- **RF-08**: Ao trocar a UF selecionada, recarregar o mapa (novo GeoJSON), o ranking e o seletor de municípios para a nova UF.
- **RF-09**: Exibir estado de carregamento explícito enquanto os polígonos do IBGE são buscados, e uma mensagem de erro clara caso a API do IBGE esteja indisponível.
- **RF-10**: Para perfil Secretário Municipal, restringir a navegação de forma que o clique em qualquer município leve sempre ao seu próprio município (ou, alternativamente, desabilitar/ocultar municípios que não são o seu — decisão de produto a confirmar, ver RN correspondente).
- **RF-11**: Exibir, ao lado do seletor de município na toolbar, uma legenda com o score do município atualmente focado (via clique no mapa, no ranking, ou seleção no próprio combo) — oculta/vazia quando nenhum município está focado (ex.: acabou de trocar de UF).
- **RF-12**: Exibir permanentemente sobre o mapa uma legenda com as 5 faixas de classificação do Score Escola Sem Barreiras (Crítico, Insuficiente, Em desenvolvimento, Adequado, Referência) e suas cores correspondentes — visível independente de qualquer interação, para o gestor entender as cores do mapa sem precisar clicar em nada.
- **RF-13** (novo): Expor um ranking nacional de estados (`GET /ranking-nacional`) com sigla, código IBGE, quantidade de municípios, total de alunos ESP, score, faixa e cor por UF, ordenado por score decrescente — consumido pela seção "Como [estado] se compara" da Início do município (ver [[indicadores-municipio]]) e pela tela `/comparar` (ver [[comparar]]).

## Requisitos Não Funcionais

- **RNF-01**: O carregamento do GeoJSON de uma UF não deve travar a interação com o restante da tela (KPIs e ranking devem estar disponíveis antes do mapa terminar de carregar).
- **RNF-02**: Cache do GeoJSON por UF no cliente ou borda (CDN/backend) para evitar repetir a mesma chamada à API do IBGE a cada troca de UF pelo mesmo usuário na sessão.
- **RNF-03**: O endpoint de ranking/score por UF deve responder rapidamente mesmo para UFs com muitos municípios (ex.: Minas Gerais, 853 municípios) — paginação ou agregação no backend deve ser considerada para o ranking completo, embora a UI só exiba um recorte (top 5 / críticos).

## Dados de entrada/saída

**Entrada**: UF selecionada (código IBGE de 2 dígitos), opcionalmente município selecionado.
**Saída**: lista de `{ codigoIbge, nome, score }` por município da UF (para colorir o mapa e montar o ranking) + os 4 KPIs nacionais.

## Fluxo principal

1. Usuário chega à tela de Mapa (pós-login ou ao clicar "← Mapa").
2. Sistema carrega KPIs nacionais, GeoJSON da UF padrão (a do usuário) e lista de scores dos municípios dessa UF.
3. Mapa é colorido e ranking é montado.
4. Usuário troca UF e/ou clica em um município → navega para o Contexto do Município.

## Fluxos alternativos

- **Falha ao carregar GeoJSON do IBGE**: exibir mensagem de erro no lugar do spinner, sem quebrar o restante da tela (KPIs/ranking continuam visíveis se disponíveis).
- **UF sem nenhum município crítico**: seção "⚠️ Críticos" do ranking fica vazia ou oculta (não exibir lista vazia com título).

## Critérios de aceite

- [ ] Selecionar qualquer uma das 27 UFs carrega o mapa e o ranking corretos.
- [ ] Cor de cada município no mapa corresponde exatamente à faixa de score definida em [[score-incluia]].
- [ ] Clicar em um item do ranking foca o município correspondente no mapa.
- [ ] Falha simulada da API do IBGE exibe mensagem de erro sem quebrar a tela.
- [ ] A faixa de KPIs mostra exatamente 5 cartões, incluindo "Score Desejado".
- [ ] A legenda de score do município só aparece depois de focar algum município, e desaparece/não aparece antes disso.
- [ ] A legenda das 5 faixas de score está sempre visível sobre o mapa, com as mesmas cores usadas para colorir os municípios.
