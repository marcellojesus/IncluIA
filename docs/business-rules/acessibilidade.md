# Regras de Negócio — Barra de Acessibilidade (transversal, módulo novo)

Fonte de código: `frontend/src/shared/components/BarraAcessibilidade.tsx`.

## RN-01 — A barra aparece em toda página do produto, incluindo fora do grupo `(app)`

A barra (texto institucional + "Alto contraste" + ajuste de fonte A-/A/A+) é montada dentro de cada layout que controla a altura total da tela — `(app)/layout.tsx`, `LoginPage.tsx` (as duas variantes: institucional e a tela contextual do Diagnóstico IA) e `app/metodologia/page.tsx` — em vez de uma única vez no layout raiz (`app/layout.tsx`).

**Por quê**: essas telas já fixam sua própria altura em `h-screen`/`min-h-screen` com rolagem interna própria (padrão "app shell" com cabeçalho/rodapé fixos e conteúdo central rolável). Montar a barra no layout raiz somaria sua altura por cima do `h-screen` de cada uma, estourando o viewport e cortando o rodapé — por isso a barra é replicada como primeiro item dentro de cada shell, não centralizada uma única vez.

## RN-02 — Alto contraste inverte a página inteira, não é um tema alternativo mantido à parte

Ativar "Alto contraste" aplica `filter: invert(1) hue-rotate(180deg)` em `body` (classe `alto-contraste` no `<html>`, ver `globals.css`) e reaplica o mesmo filtro em imagens/ícones/vídeo para não saírem como negativo. Não existe uma segunda paleta de cores mantida manualmente para o modo alto contraste.

**Por quê**: o produto usa dezenas de cores hardcoded (`bg-gray-*`, `text-orange-*` etc., não só os tokens de tema `--color-*`) — manter um tema alternativo completo exigiria revisar cor por cor em cada componente. A inversão de filtro CSS obtém um contraste real sem esse custo, ao preço de não ser um alto-contraste "curado" visualmente.

## RN-03 — Preferências de contraste e fonte persistem entre páginas, mas não têm efeito no primeiro paint

`altoContraste` e `escalaFonte` são lidos do `localStorage` (chaves `esb-alto-contraste`, `esb-escala-fonte`) dentro de um `useEffect`, depois de o componente montar — nunca no primeiro render do servidor. Isso significa que, por uma fração de segundo, a página pode renderizar sem o contraste/fonte preferidos antes de o efeito aplicar as classes no `<html>`.

**Como aplicar**: se esse "flash" incomodar no futuro, a solução é ler a preferência antes da hidratação (ex.: script inline no `<head>`), não mover a leitura para fora de um efeito — `localStorage` não existe durante a renderização no servidor.

## RN-04 — VLibras foi removido; não deve ser reintroduzido sem novo pedido explícito

Uma primeira versão da barra integrava o widget oficial do governo (`vlibras.gov.br/app/vlibras-plugin.js`) para tradução em Libras. Foi removido a pedido — a barra atual não carrega nenhum script externo, só os dois recursos de RN-02/RN-03.

## RN-05 — O filtro geográfico do cabeçalho é ocultado em rotas nacionais, não relacionado à barra de acessibilidade

`GeoFiltroBar.tsx` mantém uma lista própria de rotas onde não se renderiza (`ROTAS_SEM_FILTRO`, hoje só `/dados-abertos`) — mecanismo independente da barra de acessibilidade, mas que também é uma barra fixa no topo do produto, por isso documentado aqui para quem procurar "barras do cabeçalho" num lugar só. Novas rotas sem escopo de município (ex.: uma futura página 100% nacional) devem ser adicionadas a essa lista se o filtro não fizer sentido nelas.
