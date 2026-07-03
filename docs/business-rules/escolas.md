# Regras de Negócio — Lista de Escolas do Município (Módulo 5)

## RN-01 — Score e status de escola usam a mesma metodologia do score municipal, sem ajuste local

O score de cada escola e o status por eixo exibidos nesta tela vêm diretamente do cálculo descrito em [[score-incluia]] — a tela de Escolas não recalcula nem reinterpreta esses valores, apenas os lista e permite filtrar/ordenar.

## RN-02 — Classificação de cor do score de escola deve seguir a mesma escala de 5 faixas do score municipal

O protótipo (`prototipo_inclua.html`, função `renderEscolas`/`abrirEscola`) usa apenas 4 faixas de cor para o score da escola (verde ≥7, amarelo ≥5, laranja ≥3, vermelho <3), **omitindo a faixa "Referência" (azul, ≥8,5)** que existe para municípios.

**Decisão de negócio necessária**: definir se escolas também têm uma 5ª faixa "Referência" (consistência com a metodologia) ou se, deliberadamente, o nível de escola usa só 4 faixas por ser uma unidade de análise mais granular e volátil (`IncluIA_Metodologia_Score_v1` nota que "municípios com poucas escolas ESP têm score volátil" — o mesmo vale, com mais força, para escolas individuais). **Recomendação**: manter as mesmas 5 faixas usadas em todo o produto para não haver 2 escalas de cor diferentes coexistindo — ver [[score-incluia]].

## RN-03 — Filtro "Situação crítica" e "Sem AEE" são mutuamente exclusivos no MVP

O seletor de filtro do protótipo permite apenas uma opção ativa por vez (não é multi-seleção). Antes de evoluir para filtros combináveis (ex.: "crítica E sem AEE"), validar se há demanda real do usuário — não implementar filtros combinados especulativamente no MVP.

## RN-04 — Exportação é best-effort no MVP

O botão "Exportar" pode ser entregue como Fase 2 sem bloquear o lançamento do MVP, **desde que a decisão seja explícita e comunicada** — no protótipo o botão está visível mas sem função, o que não deve chegar à produção sem aviso ("em breve") ou implementação real, pois um botão visualmente ativo sem ação quebra a confiança do gestor no produto.

**Por quê**: `context.md` §7.2 lista "Exportação de relatórios PDF por município" como Fase 2 explicitamente — por analogia, exportação de lista de escolas em CSV/XLSX é uma funcionalidade menor, mais simples de entregar no MVP, mas se não entrar, o botão deve refletir esse status (desabilitado + rótulo "em breve"), como já é feito com o botão "Entrar com gov.br" na tela de login.

## RN-05 — Escolas exclusivamente especiais (`IN_ESPECIAL_EXCLUSIVA=1`) aparecem na lista, mas com tratamento especial no Eixo IV

Uma escola cuja matrícula é 100% em classe especial exclusiva, por definição, não tem alunos em classe comum — isso não deve ser exibido como "❌ Crítico" no Eixo IV da mesma forma que uma escola regular que simplesmente segrega alunos indevidamente. A interface deve diferenciar (ex.: rótulo "Escola especial exclusiva — Eixo IV não aplicável") em vez de aplicar cegamente a fórmula de taxa de inclusão em classe comum.

**Por quê**: `IncluIA_Metodologia_Score_v1` define essa regra explicitamente para o cálculo do score (`V_taxa_CC=0` por definição para essas escolas), mas o cálculo correto no score não implica que a apresentação visual deva parecer uma falha de gestão — é uma característica estrutural da escola, não um gap a ser corrigido.
