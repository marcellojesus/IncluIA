# Requisitos — Sobre (Módulo novo)

Fonte de código: `frontend/src/app/(app)/sobre/page.tsx`.

## Objetivo

Explicar o que é o produto, como o índice é calculado, o que já existe versus o que ainda está em desenvolvimento, e dar transparência sobre a origem acadêmica do projeto.

## Atores

Qualquer visitante, sem login.

## Requisitos Funcionais

- **RF-01**: Exibir um selo "Sobre a plataforma", título "Escola Sem Barreiras" e um parágrafo institucional citando a PNEEI (Decreto 12.686/2025) e o Censo Escolar do INEP como fonte de dados.
- **RF-02**: Exibir o aviso "Protótipo acadêmico" com link para os microdados oficiais do Censo Escolar no site do INEP (ver RN-02 de `docs/business-rules/sobre.md`).
- **RF-03**: Exibir o aviso "Metodologia em construção" com link para `/metodologia`.
- **RF-04**: Exibir a seção "Trabalho acadêmico": disciplinas cursadas, programa de pós-graduação e instituição (Universidade Federal de Tocantins), lista de discentes (com e-mail quando informado) e lista de docentes.
- **RF-05**: Exibir uma seção "Projeto de código aberto" com um botão que abre o repositório do projeto no GitHub em uma nova aba.
- **RF-06**: Exibir dois botões de saída: "Explorar a plataforma" (→ `/`) e "Ver dados abertos" (→ `/dados-abertos`).

## Dados de entrada/saída

Nenhum — página inteiramente estática (sem chamada a API).

## Critérios de aceite

- [ ] `/sobre` abre sem exigir login e sem nenhuma chamada de rede.
- [ ] Os dois avisos (Protótipo acadêmico, Metodologia em construção) estão sempre visíveis, sem precisar de interação.
- [ ] O link "Ver no GitHub" abre em nova aba e aponta para o repositório real do projeto.
