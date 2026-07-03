# Publicação em produção — IncluIA v1.0

Stack de deploy (ver `arquitetura.md` §Infraestrutura): **GitHub** (código) → **Render** (backend FastAPI) → **Vercel** (frontend Next.js).

**URLs da v1.0 em produção**:
- Backend: https://incluia-api.onrender.com
- Frontend: https://inclu-ia.vercel.app

## Por que o `data/incluia.db` é versionado no Git

O `.gitignore` normalmente excluiria um banco de dados gerado, mas aqui é uma exceção deliberada: o backend em produção só lê esse arquivo (não recalcula nada em tempo de execução) e os dados brutos do Censo (`base/`, ~400MB) nunca vão ao repositório — não haveria como o Render gerar o `.db` sozinho. Por isso `data/incluia.db` (~30MB) é comitado como um artefato pronto.

**Atualizar o Censo no futuro**: rodar `python run_etl.py` localmente (dentro de `backend/`) com a nova base, e comitar o `data/incluia.db` resultante — o deploy no Render é automático a partir do push (ver abaixo).

## 1. Repositório no GitHub

Repositório privado, código versionado normalmente (segredos nunca entram — `.gitignore` já cobre `.env`).

## 2. Backend no Render (Blueprint)

Este repositório já tem um `render.yaml` na raiz — o Render lê esse arquivo automaticamente ao conectar o repo como "Blueprint" e propõe o serviço `incluia-api` pronto (Python, `rootDir: backend`, build/start commands, health check em `/health`).

Segredos que o Render vai pedir na hora de aplicar o Blueprint (não ficam no `render.yaml`, são inseridos só no dashboard):
- `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY` — chaves de IA já usadas em dev.
- `INCLUIA_JWT_SECRET` — gerado automaticamente pelo Render (`generateValue: true`), não precisa informar.

Depois do primeiro deploy, anotar a URL pública do serviço (algo como `https://incluia-api.onrender.com`) — é o que o frontend vai chamar.

**Limitação conhecida do plano gratuito**: o serviço "dorme" após 15 minutos sem requisições — a primeira chamada depois disso demora ~30-60s para acordar (`arquitetura.md` já documenta isso). Não é bug, é o trade-off do free tier.

## 3. Frontend na Vercel

Ao importar o repositório na Vercel:
- **Root Directory**: `frontend` (o projeto Next.js não está na raiz do repo).
- Framework é detectado automaticamente (Next.js).
- Variável de ambiente: `NEXT_PUBLIC_API_URL` = URL do backend no Render (do passo 2).

## 4. Fechar o CORS com a URL real do frontend

`INCLUIA_CORS_ORIGINS` no `render.yaml` **não** está marcada como `sync: false` — o valor vem do próprio arquivo, e o Render resincroniza a cada push. Por isso, para liberar a URL real do frontend, o jeito certo é editar o `value` desse campo no `render.yaml` e comitar/dar push — nunca editar só pelo painel do Render (um push futuro reverteria o valor). Sem essa origem liberada, o navegador bloqueia por CORS toda chamada feita direto do cliente (ex.: aba Escolas, chat do Diagnóstico IA) — só as chamadas feitas no servidor (SSR) continuam funcionando, o que confunde o diagnóstico do problema.

## 5. Limitações do MVP a ter em mente em produção

- **SQLite em disco efêmero do Render (plano free)**: o `data/incluia.db` versionado no Git sempre volta certinho a cada deploy, mas qualquer escrita em runtime (cache de diagnóstico de IA, histórico de chat, ajustes via chat) é perdida quando o serviço reinicia/reimplanta. Aceitável para o MVP — não é perda de dados do Censo, só de cache/conversas.
- **`INCLUIA_JWT_SECRET` gerado pelo Render permanece igual entre deploys** (não muda a cada redeploy) — sessões continuam válidas normalmente.
- Sem domínio próprio configurado neste guia — Render e Vercel já dão HTTPS nos subdomínios padrão (`.onrender.com` / `.vercel.app`), suficiente para a v1.0.
