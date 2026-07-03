# Regras de Negócio — Página de Metodologia

## RN-01 — A página nunca mantém uma cópia do texto da metodologia

`frontend/src/app/metodologia/page.tsx` lê `metodologia_score.md` do sistema de arquivos em tempo de renderização (`fs.readFileSync`) e converte para HTML com `react-markdown` — não existe um segundo texto da metodologia hardcoded na página ou em um CMS.

**Por quê**: `metodologia_score.md` já é a fonte de verdade oficial (ver seu próprio cabeçalho). Duplicar o conteúdo criaria risco de a página exibir uma versão desatualizada da fórmula do Score IncluIA.

**Como aplicar**: qualquer correção futura na metodologia (pesos, variáveis, faixas) é feita apenas em `metodologia_score.md` — nunca editar texto de metodologia diretamente em componentes React.

## RN-02 — O link de metodologia é visível em todo o sistema, autenticado ou não

O `Footer.tsx` compartilhado (usado tanto em `/login` quanto no layout pós-login) é o único lugar onde o link para `/metodologia` é definido — evita ter o link presente em algumas telas e ausente em outras por esquecimento.
