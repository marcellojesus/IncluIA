# Requisitos — Comparar (Módulo novo)

Fonte de código: `frontend/src/features/comparar/components/CompararView.tsx`, `frontend/src/app/(app)/comparar/page.tsx`. Antes desta funcionalidade, `/comparar` era um placeholder (`PaginaEmConstrucao`).

## Objetivo

Permitir que qualquer visitante compare o Índice de Inclusão entre estados de todo o Brasil, ou entre municípios dentro de um estado escolhido — sem precisar abrir um município específico primeiro.

## Atores

Qualquer visitante, sem login.

## Pré-condições

Nenhuma. Se houver um município selecionado no filtro geográfico do cabeçalho, sua UF é usada como contexto inicial (ver RN-01 de `docs/business-rules/comparar.md`).

## Requisitos Funcionais

- **RF-01**: Exibir um alternador com dois modos: "Ranking de Estados" (padrão) e "Ranking de Municípios".
- **RF-02**: No modo "Ranking de Estados", listar as 27 UFs ordenadas por score decrescente, com posição, nome do estado, quantidade de municípios e o índice (barra + valor); destacar a UF do município atualmente selecionado, se houver.
- **RF-03**: No modo "Ranking de Municípios", exibir um seletor de UF (padrão: a do município selecionado, ou "DF" se nenhum) e listar os municípios dessa UF ordenados por score decrescente, com posição, nome e índice; destacar o município atualmente selecionado, se pertencer à UF exibida.
- **RF-04**: Trocar de UF no modo "Ranking de Municípios" deve recarregar a lista para a nova UF sem exigir navegação para outra tela.

## Dados de entrada/saída

**Entrada**: modo selecionado (estados/municípios); no modo municípios, a UF escolhida.
**Saída (estados)**: lista de `{ sigla, codigoUf, qtdMunicipios, totalAlunosEsp, score, faixa, cor, rankingNacional }` — `GET /ranking-nacional`.
**Saída (municípios)**: lista de `{ codigoIbge, nome, uf, score, faixa, cor }` por UF — `GET /uf/{sigla}/municipios` (mesmo endpoint já usado por `GeoFiltroBar.tsx`).

## Fluxo principal

1. Usuário acessa `/comparar` (via nav do cabeçalho, ou link "Ver ranking completo"/"Comparar redes" a partir da Início de um município).
2. Sistema carrega o Ranking de Estados por padrão.
3. Usuário alterna para "Ranking de Municípios" → sistema carrega os municípios da UF inicial (a do seu município selecionado, ou DF).
4. Usuário troca a UF no seletor → lista de municípios é recarregada para a nova UF.

## Critérios de aceite

- [ ] `/comparar` abre sem exigir login.
- [ ] O modo "Ranking de Estados" lista as 27 UFs, ordenadas por score decrescente.
- [ ] Se houver município selecionado, sua UF aparece destacada no ranking de estados e pré-selecionada no ranking de municípios.
- [ ] Trocar de UF no ranking de municípios atualiza a lista sem recarregar a página.
