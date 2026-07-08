# Regras de Negócio — Sobre (Módulo novo)

## RN-01 — `/sobre` é uma página real, não um placeholder

`/sobre` deixou de usar `PaginaEmConstrucao` — todo o conteúdo descrito neste documento está implementado (`frontend/src/app/(app)/sobre/page.tsx`), diferente de `/dados-abertos` (parcialmente real, ver [[dados-abertos]]) e `/participar` (ainda placeholder).

## RN-02 — Dois avisos de transparência são obrigatórios e não podem ser removidos sem decisão explícita

A página exibe dois avisos permanentes, no mesmo estilo visual (caixa laranja):

1. **Protótipo acadêmico**: os números exibidos no produto são ilustrativos, com link para os microdados oficiais do Censo Escolar no INEP.
2. **Metodologia em construção**: a fórmula do Índice de Inclusão é uma proposta dos alunos da UFT, ainda sem revisão por um estatístico e por um especialista em educação — com link para `/metodologia`.

**Por quê**: mesmo princípio de RN-02 de `docs/business-rules/indicadores-municipio.md` (nunca apresentar uma aproximação metodológica não validada como se fosse definitiva) — aplicado aqui ao produto como um todo, não só ao mapeamento score↔Decreto.

## RN-03 — Créditos acadêmicos ficam nesta página, não espalhados pelo produto

Disciplinas, programa de pós-graduação, instituição (Universidade Federal de Tocantins) e a lista de discentes/docentes vivem exclusivamente na seção "Trabalho acadêmico" de `/sobre` — não são repetidos no rodapé global (`Footer.tsx`) nem no cabeçalho.

## RN-04 — Link do repositório aponta para o remoto git real do projeto

O botão "Ver no GitHub" usa a URL do remote `origin` configurado no repositório (`https://github.com/marcellojesus/IncluIA`) — não é um link de exemplo. Se o repositório for renomeado ou tornado privado, este link quebra e deve ser atualizado junto.
