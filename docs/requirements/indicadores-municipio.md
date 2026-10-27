# Requisitos — Indicadores do Município (Módulo 2)

> **Integração com a Gestão Ativa (2026-10-27).** A Início ganhou o bloco "O que as escolas publicaram" (quantas escolas do município publicaram Declaração de Obstáculos e Plano de Ação, buscado no navegador por causa do limite por IP da rota pública — PUB-04) e a porta de entrada da Gestão Ativa para diretores e secretarias. Os botões "Registrar uma barreira", que só abriam um aviso de função futura, foram substituídos: no topo, "Sou gestor: Gestão Ativa" (leva a `/participar`); no card "O que você pode fazer", "Entender os números" (leva à leitura pública com IA). Ver [impacto da Fase 2](../sdd/fase-2/impacto-fase-1.md).

Fonte de interface: `interface.md` §4 e §5. Fonte de contexto: `context.md` (Módulo 2).

> **Status atual (rastreabilidade)**: esta tela é hoje a "Início" pública de um município (`/municipio/[codigoIbge]`), sem exigir login — ver RN-00/RN-06/RN-07 de `docs/business-rules/indicadores-municipio.md`. RF-01 e RF-05 abaixo descrevem a especificação original (barra de 3 abas + tabela de detalhamento) e ficam mantidos por histórico; RF-13 e RF-14 documentam o que substituiu cada um na tela atual.

## Objetivo

Traduzir os dados do Censo Escolar do município selecionado em um diagnóstico estruturado pelos 4 Eixos da PNEEI (Decreto 12.686/2025), com semáforos, scores e detalhamento dos critérios legais.

## Atores

Qualquer visitante, sem necessidade de login (RN-06 de `docs/business-rules/login.md`) — a tela não é mais restrita a Secretário Municipal/Estadual. Só o Diagnóstico IA (rota irmã, não mais aba desta tela) exige conta.

## Pré-condições

- Município já possui Score Escola Sem Barreiras e scores por eixo calculados (depende de [[score-incluia]]).
- Usuário chegou a esta tela a partir do filtro geográfico do cabeçalho (`GeoFiltroBar.tsx`) ou de navegação direta por município.

## Requisitos Funcionais

- **RF-01**: Exibir uma barra de contexto fixa com nome do município, UF, score geral (valor + badge de status) e as 3 abas de navegação (Indicadores, Escolas, Diagnóstico IA). *(histórico — ver RF-13: hoje é o cabeçalho global do produto, não uma barra local desta tela, e Escolas/Diagnóstico IA são rotas próprias, não abas.)*
- **RF-02**: Na aba Indicadores, exibir 4 cards de semáforo (um por eixo do Decreto), cada um com ícone de status (✅/⚠️/❌), rótulo do eixo, valor-resumo e subtexto.
- **RF-03**: Exibir o painel "Score por Eixo" com uma barra de progresso (0–10) por eixo, incluindo o peso do eixo no rótulo.
- **RF-04**: Exibir o painel "Dados Gerais" com os indicadores agregados do município (alunos ESP, % escolas com AEE, % inclusão em classe comum, professores LIBRAS, revisores Braille, % rampa/piso tátil/banheiro PNE) e comparativo com médias estadual e nacional.
- **RF-05**: Exibir a tabela "Detalhamento — PNEEI (Decreto 12.686/2025)" mapeando cada critério legal à variável do Censo, valor observado e badge de conformidade, com aviso permanente de "Em validação jurídica". *(histórico — ver RF-14: este painel não é mais renderizado na Início.)*
- **RF-06**: Exibir indicador de tendência (melhora/piora) comparando com a edição anterior do Censo, quando o dado histórico existir. *(ainda não implementado na tela atual.)*
- **RF-07**: O botão "← Mapa" deve retornar à tela de Mapa mantendo a UF de onde o usuário veio. *(histórico — não há mais botão "← Mapa"; a navegação de volta é pelo cabeçalho/filtro geográfico global.)*
- **RF-13** (novo): O cabeçalho do produto (`AppHeader.tsx`) exibe os links de nível superior Início, Escolas, Comparar, Diagnóstico IA, Dados abertos e Sobre, escopados ao município atualmente selecionado no filtro geográfico — substitui a barra de contexto com 3 abas da especificação original (RF-01).
- **RF-14** (novo): Entre o painel "Score por Eixo + Dados Gerais" e a seção "O que você pode fazer", exibir "Como [estado] se compara": ranking nacional de estados (top 6 + o estado atual destacado como 7ª linha se estiver fora do top 6), com link "Ver ranking completo" para `/comparar` (ver [[comparar]]) — substitui a tabela de detalhamento da especificação original (RF-05).

## Requisitos Não Funcionais

- **RNF-01**: Todos os valores exibidos devem ser rastreáveis a uma variável específica do Censo (nenhum número "mágico" sem origem documentada) — necessário para a defensabilidade jurídica do painel de conformidade.
- **RNF-02**: Carregamento dos 4 painéis desta aba deve ocorrer em uma única chamada de API (ou chamadas paralelas), evitando múltiplos round-trips sequenciais que atrasem a renderização da tela.

## Dados de entrada/saída

**Entrada**: `codigoIbge` do município.
**Saída**: `{ eixos[4], scoreEixos[4], dadosGerais[], detalhamentoDecreto[] }` conforme shape descrito em `interface.md` §9.

## Fluxo principal

1. Usuário chega à tela de Contexto do Município vindo do Mapa ou do Ranking.
2. Sistema busca o detalhe do município e popula semáforos, scores por eixo, dados gerais e tabela do decreto.
3. Aba Indicadores é exibida por padrão (não Escolas nem Diagnóstico IA).

## Fluxos alternativos

- **Município sem dado suficiente para algum eixo** (ex.: zero escolas com alunos ESP): exibir estado "sem dados" no card do eixo em vez de um valor calculado artificialmente (evita falso ✅ ou falso ❌).
- **Indicador de tendência sem Censo anterior disponível**: omitir o indicador de tendência para esse item, não exibir "0%" ou "—" como se fosse um dado real.

## Critérios de aceite

- [ ] Os 4 semáforos refletem exatamente o `status` retornado pela API (ok/warn/nok), sem lógica de cor duplicada no frontend.
- [ ] A tabela do Decreto sempre exibe o aviso de "Em validação jurídica" visível sem precisar de scroll adicional.
- [ ] Trocar de município (via mapa) atualiza todos os painéis desta aba sem recarregar a página inteira.
