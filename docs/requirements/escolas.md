# Requisitos — Lista de Escolas do Município (Módulo 5)

Fonte de interface: `interface.md` §6. Fonte de contexto: `context.md` (Módulo 5).

## Objetivo

Permitir que o gestor identifique quais escolas específicas do seu município priorizar, listando todas as escolas com seus indicadores por eixo e score individual, com detalhamento completo por escola.

## Atores

Secretário Municipal (escolas do próprio município) e Secretário Estadual (escolas de qualquer município da UF).

## Pré-condições

- Município selecionado (contexto ativo, ver [[indicadores-municipio]]).
- Score por escola já calculado (depende de [[score-incluia]]).

## Requisitos Funcionais

- **RF-01**: Listar todas as escolas do município selecionado, com nome + bairro/rede/alunos ESP e o status por eixo (I–IV). **Status atual (rastreabilidade)**: a lista é renderizada como cartões empilhados (`ListaEscolas.tsx`), um por escola — não mais uma tabela HTML — e o status por eixo usa um badge de texto com ponto colorido ("Conforme"/"Parcial"/"Não conf.") em vez dos ícones ✅/⚠️/❌ da especificação original; a legenda de ícones (`LegendaIconesEscola.tsx`) foi removida por ficar redundante com os badges de texto. O score individual (0–10) saiu da lista e só aparece no modal de detalhamento (RF-04) — a lista prioriza a leitura rápida da conformidade por eixo.
- **RF-02**: Oferecer um filtro com pelo menos as opções: "Todas as escolas", "Situação crítica" (score < 3,0) e "Sem AEE" (status Eixo I = ❌).
- **RF-03**: Ao clicar em qualquer linha da tabela, abrir um modal com o detalhamento completo da escola.
- **RF-04**: O modal deve exibir, no mínimo: nome, rede, bairro/endereço, código INEP, os 4 status por eixo, score individual, e posição da escola no ranking do município.
- **RF-05**: Oferecer exportação da lista de escolas filtrada (ex.: CSV/XLSX) — funcionalidade classificada como desejável para o MVP, mas pode ser adiada para Fase 2 se houver restrição de prazo (ver RN correspondente).
- **RF-06**: A lista deve suportar municípios com centenas de escolas sem degradar a performance de renderização (ex.: paginação ou virtualização de lista).
- **RF-07**: A ordenação padrão da lista deve priorizar as escolas mais críticas (menor score primeiro), para que o gestor veja imediatamente onde agir.

## Requisitos Não Funcionais

- **RNF-01**: Nome, bairro e rede da escola devem ser exibidos exatamente como registrados no Censo (`CO_ENTIDADE`), sem normalização que possa confundir a identificação da escola pelo gestor.
- **RNF-02**: A busca/filtro deve responder localmente (client-side) se o número de escolas do município for pequeno (dezenas), e via API se for grande (centenas), para manter a UI responsiva.

## Dados de entrada/saída

**Entrada**: `codigoIbge` do município, filtro selecionado.
**Saída**: lista de `{ codigoInep, nome, bairro, endereco, rede, alunosEsp, statusEixoI..IV, score, rankingMunicipal }`.

## Fluxo principal

1. Usuário abre a aba "Escolas" de um município.
2. Sistema busca a lista completa de escolas do município, já ordenada por score crescente.
3. Usuário pode filtrar por situação crítica ou sem AEE.
4. Usuário clica em uma escola → modal com detalhamento completo é exibido.

## Fluxos alternativos

- **Município sem nenhuma escola cadastrada com aluno ESP no Censo**: exibir estado vazio explicativo ("Nenhuma escola com alunos com deficiência registrada no Censo para este município"), não uma tabela em branco sem explicação.
- **Filtro sem resultados** (ex.: "Sem AEE" em município 100% conforme): exibir mensagem "Nenhuma escola nesta situação" em vez de tabela vazia.

## Critérios de aceite

- [ ] Filtro "Situação crítica" retorna exatamente as escolas com score < 3,0, nada além disso.
- [ ] Modal de detalhamento sempre mostra código INEP e posição no ranking municipal (lacuna identificada no protótipo, ver `interface.md` §6.1).
- [ ] Lista renderiza corretamente para um município com 300+ escolas sem travar a interface.
