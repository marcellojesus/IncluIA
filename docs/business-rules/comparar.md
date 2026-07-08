# Regras de Negócio — Comparar (Módulo novo)

## RN-01 — Tela pública, sem escopo de município obrigatório

`/comparar` é acessível sem login (mesma regra geral de RN-06 de `docs/business-rules/login.md` — só o Diagnóstico IA exige conta) e sem exigir um município previamente selecionado no filtro geográfico. Se houver um município selecionado (`useAppStore.municipioSelecionado`), a UF dele é usada como UF inicial do modo "Ranking de Municípios" e é destacada no modo "Ranking de Estados" — mas nenhum dos dois modos trava se não houver seleção prévia (o modo Municípios cai para "DF" como UF inicial).

## RN-02 — Dois rankings independentes, nunca misturados na mesma tabela

A tela alterna entre **Ranking de Estados** (nacional, todas as 27 UFs, `GET /ranking-nacional`) e **Ranking de Municípios** (dentro de uma UF escolhida via `<select>`, `GET /uf/{sigla}/municipios`) — nunca uma tabela combinando as duas granularidades. O ranking de municípios é ordenado no cliente por score decrescente (o endpoint em si não garante ordenação); o ranking de estados já vem ordenado do backend (ver RN-10 de `docs/business-rules/mapa.md`).

**Por quê**: comparar estados e municípios na mesma lista não faz sentido estatístico (escalas de score não são diretamente comparáveis entre agregações de tamanhos tão diferentes) e confundiria o usuário sobre o que está sendo rankeado.

## RN-03 — O ranking nacional de estados é a mesma fonte usada na Início do município

`RankingEstadosTabela` (dentro de `/comparar`) e `RankingEstados` (seção "Como [estado] se compara" da Início do município, ver RN-06 de `docs/business-rules/indicadores-municipio.md`) chamam o mesmo endpoint (`GET /ranking-nacional`) e aplicam a mesma lógica de destaque da UF atual — não há dois cálculos de ranking nacional divergentes no produto.
