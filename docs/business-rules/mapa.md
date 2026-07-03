# Regras de Negócio — Mapa da Inclusão (Módulo 1)

## RN-01 — Granularidade do MVP é município, não escola

O mapa exibe e colore **municípios**, nunca escolas individuais. Mapear as ~214 mil escolas no mapa é explicitamente Fase 2 (`context.md` §7.2), por exigir infraestrutura de clusterização/tiles que o MVP não cobre.

**Como aplicar**: qualquer requisito ou ideia de "mostrar escola no mapa" deve ser recusado ou movido para backlog — não implementar no MVP mesmo que pareça simples com poucos dados de exemplo.

## RN-02 — A cor do município no mapa é sempre derivada do Score IncluIA vigente

Não existe cor "manual" ou "override" de município no mapa — a cor é 100% função do score calculado (ver [[score-incluia]] para faixas e cores exatas). Isso garante que o mapa é sempre consistente com os demais painéis (ranking, barra de contexto, semáforos).

## RN-03 — Fonte oficial e gratuita de geometria: sempre API pública do IBGE

Os polígonos dos municípios devem vir da API pública do IBGE (`servicodados.ibge.gov.br/api/v3/malhas/...`) e os nomes/códigos da API de localidades do IBGE — nunca de um shapefile de terceiros ou de uma cópia estática desatualizada.

**Por quê**: garante dados geográficos oficiais e atualizados sem custo de licenciamento (`context.md` §6.1, "Nenhuma API key ou conta paga necessária").

**Como aplicar**: se a API do IBGE ficar indisponível, o sistema deve degradar graciosamente (mensagem de erro), não substituir silenciosamente por uma fonte alternativa sem aviso.

## RN-04 — Ranking "Críticos" é definido pelo mesmo limiar de score usado em todo o produto

A seção "⚠️ Críticos" do ranking lateral usa o mesmo limiar de `score < 3,0` que define a faixa "Crítico" na metodologia do Score IncluIA (ver [[score-incluia]]) — não é um "top 3 piores" arbitrário, é um filtro por limiar absoluto. Isso significa que uma UF pode não ter nenhum município nessa seção (se nenhum estiver abaixo de 3,0) ou ter dezenas.

## RN-05 — Escopo de visualização por perfil (decisão de produto pendente)

`docs/business-rules/login.md` (RN-03) já define que o Secretário Municipal só pode **acessar dados** do próprio município. Falta decidir, como regra de UX/produto, se para esse perfil o mapa da UF:
(a) mostra todos os municípios coloridos normalmente, mas só permite abrir o próprio (demais cliques bloqueados/sem ação); ou
(b) mostra todos os municípios em cinza neutro, exceto o próprio destacado nas cores normais.

**Status**: em aberto — `context.md` §3.2 menciona apenas "mapa do estado (município destacado)", sem detalhar o tratamento visual dos demais municípios. Definir antes de implementar o Módulo 1 para o perfil Municipal.

## RN-06 — KPIs nacionais independem da UF selecionada

Os KPIs no topo (Municípios Críticos, Escolas sem AEE, Score Médio Nacional, Score Desejado, Municípios Mapeados) são sempre nacionais — não recalculam ao trocar de UF no seletor. Apenas o mapa e o ranking lateral são escopados pela UF selecionada.

## RN-07 — "Score Desejado" é o limiar da faixa "Adequado", não um número novo

O KPI "Score Desejado" vale **7,0** — o mesmo limiar mínimo que já classifica um município como "Adequado" em `metodologia_score.md` §5. Não é uma meta inventada separadamente: é derivado da mesma constante `FAIXAS` já usada para colorir o mapa e classificar municípios/escolas (`backend/etl/score.py`).

**Por quê**: manter um único lugar de verdade para os limiares do score. Se a metodologia mudar o limiar de "Adequado" no futuro, o KPI "Score Desejado" muda junto automaticamente, sem precisar lembrar de atualizar um valor duplicado.

**Interpretação para o gestor**: municípios abaixo do Score Desejado ainda têm lacunas relevantes de conformidade com a PNEEI (Decreto 12.686/2025) a fechar; a partir dele, o município está numa faixa de boa conformidade.

## RN-08 — Legenda de score do município reaproveita cor/faixa do backend

A legenda de score exibida ao lado do seletor de município (RF-11) usa exatamente o mesmo `score`/`faixa`/`cor` que já vêm do backend para aquele município (mesma fonte de verdade da RN-02) — nunca é recalculada ou reclassificada no cliente.

## RN-09 — Legenda das 5 faixas usa a mesma classificação de todo o produto

A legenda permanente sobre o mapa (RF-12) usa as mesmas 5 faixas e cores hex de `metodologia_score.md` §5 (`frontend/src/shared/lib/score.ts::FAIXAS`, espelhando `backend/etl/score.py::FAIXAS`) — não é uma lista de cores mantida separadamente na UI. Se a metodologia mudar um limiar ou cor, a legenda muda junto.
