# Requisitos — Dados Abertos (Módulo novo)

Fonte de código: `frontend/src/app/(app)/dados-abertos/page.tsx`.

> **Histórico**: esta página já teve duas versões antes da atual — primeiro um placeholder (`PaginaEmConstrucao`), depois uma versão com 6 cards de datasets fictícios e botões "Baixar" desabilitados. Ambas foram substituídas por decisão explícita (ver RN-01 de `docs/business-rules/dados-abertos.md`) por uma versão só com texto explicativo e links reais.

## Objetivo

Dar transparência sobre a origem dos dados do produto (Censo Escolar do INEP) e apontar caminhos reais para quem quer os dados brutos, a API ou a metodologia — sem simular funcionalidades que não existem.

## Atores

Qualquer visitante, sem login.

## Requisitos Funcionais

- **RF-01**: Exibir título "Dados abertos" e um parágrafo, centralizados, explicando que o índice vem do Censo Escolar do INEP.
- **RF-02**: O parágrafo deve incluir um link real para a página oficial de microdados do Censo Escolar no site do INEP.
- **RF-03**: Exibir uma seção "API pública e metodologia aberta" com dois links: "Ver a API" (abre a documentação Swagger do backend em nova aba) e "Metodologia" (→ `/metodologia`).
- **RF-04**: Não exibir o filtro geográfico do cabeçalho (Região/UF/Município) nesta página.

## Dados de entrada/saída

Nenhum — página estática (sem chamada a API própria do produto; os links levam a documentação/fontes externas ou internas já existentes).

## Critérios de aceite

- [ ] `/dados-abertos` não exibe a barra de filtro geográfico do cabeçalho.
- [ ] O link para o INEP abre em nova aba e aponta para a URL oficial de microdados do Censo Escolar.
- [ ] "Ver a API" abre o Swagger do backend (`/docs`) em nova aba.
