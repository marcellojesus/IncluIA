# Requisitos — Página de Metodologia

Fonte de contexto: `metodologia_score.md` (documento fonte de verdade da fórmula do Score Escola Sem Barreiras).

## Objetivo

Dar a qualquer gestor acesso, a partir de qualquer tela do sistema, ao texto completo e formatado da metodologia oficial do Score Escola Sem Barreiras — sem precisar sair do sistema ou abrir um arquivo bruto.

## Atores

Qualquer usuário autenticado ou não (tela de Login já expõe o link).

## Requisitos Funcionais

- **RF-01**: Exibir, em uma barra horizontal discreta no rodapé de toda tela do sistema (Login e telas pós-login), um link "Metodologia do Score Escola Sem Barreiras".
- **RF-02**: O link leva a uma página dedicada (`/metodologia`) que renderiza o conteúdo de `metodologia_score.md` formatado (títulos, negrito, tabelas, citações) no estilo visual do Design System gov.br já usado no restante do sistema.
- **RF-03**: A página de metodologia lê o conteúdo diretamente do arquivo `metodologia_score.md` do repositório (não uma cópia mantida em paralelo) — qualquer atualização do arquivo fonte se reflete automaticamente na página, sem exigir alteração de código.

## Critérios de aceite

- [ ] O rodapé com o link aparece em `/login`, `/mapa` e `/municipio/{codigoIbge}`.
- [ ] `/metodologia` renderiza títulos, tabelas e texto em negrito corretamente, sem exibir marcações Markdown cruas.
- [ ] Alterar `metodologia_score.md` e recarregar a página reflete o novo conteúdo sem alteração de código.
