# Feature: Gestão Ativa (acesso, diretor, secretário)

Specs: `docs/sdd/fase-2/requirements/acesso-gestao-ativa.md` · `docs/sdd/fase-2/business-rules/acesso-gestao-ativa.md` · `docs/sdd/fase-2/requirements/diretor/dashboard-situacao-escola.md` · protótipo aprovado `FASE2/prototipo_gestao_ativa_v2.html`

Rotas: `/participar` (entrada pública), `/gestao/entrar` (código por e-mail), `/gestao/diretor`, `/gestao/secretario`, `/gestao/admin`.

Sessão própria (`store.ts`), a única do produto: o login da Fase 1 saiu do ar em 2026-10-27 e `/login` redireciona para `/gestao/entrar` (RF-12). A autorização de verdade é do backend: `AreaRestrita` só evita mostrar tela vazia e redireciona quem não tem acesso.

Ambiente local: `python -m app.features.acesso.cli demo` (em `backend/`) cria administrador, secretária de Niterói/RJ e um pedido de diretora pendente; os códigos aparecem no console do backend e na caixa de teste `/gestao/dev/emails` (só `AMBIENTE=dev`).
