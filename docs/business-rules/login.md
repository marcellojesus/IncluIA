# Regras de Negócio — Login / Autenticação

## RN-01 — Autenticação é simulada no MVP, real na Fase 2

No MVP, a autenticação é feita por e-mail/senha cadastrados manualmente (sem autosserviço de cadastro). A integração com **gov.br SSO** é explicitamente **Fase 2** (`context.md` §7.2) — o botão correspondente deve permanecer visível, porém desabilitado, para comunicar o roadmap ao usuário sem implementá-lo.

**Por quê**: alinhamento ao documento MVP5, que classifica SSO gov.br como funcionalidade futura, e ao fato de que a integração real com gov.br exige homologação institucional fora do escopo de um MVP de validação.

## RN-02 — Um usuário pertence a exatamente um perfil

Cada conta tem um perfil fixo no momento do cadastro: **Secretário Municipal** ou **Secretário Estadual**. Não há troca de perfil dentro da mesma sessão nem contas com múltiplos perfis simultâneos no MVP.

**Como aplicar**: o campo `perfil` não restringe mais o acesso a município (ver histórico da RN-03, revogada) — hoje serve só para exibição (cargo/UF no cabeçalho) e para eventual telemetria futura.

## RN-03 — Revogada: escopo de acesso a município por perfil (histórico)

**Redação original** (nunca chegou a ser implementada — nenhum endpoint validava o JWT emitido no login): "Secretário Municipal só pode visualizar dados do `municipioId` vinculado à sua conta; Secretário Estadual, todos os municípios da `uf` vinculada."

**Status atual**: revogada. Substituída por **RN-06** — o produto pivotou de "multi-tenant por secretaria" para "público, exceto Diagnóstico IA": Mapa, Indicadores e Escolas são públicos para qualquer visitante (sem exigir conta), e o Diagnóstico IA exige apenas estar autenticado — **qualquer** usuário cadastrado pode gerar diagnóstico de **qualquer** município, não só do seu. Mantida aqui só por histórico, para quem procurar a decisão original.

## RN-04 — Nenhuma tela de erro genérica de autenticação deve revelar existência de conta

Mensagens de erro de login devem ser idênticas para "e-mail não cadastrado" e "senha incorreta" (ex.: "E-mail ou senha inválidos").

**Por quê**: prática padrão de segurança para evitar enumeração de contas institucionais.

## RN-05 — Estatísticas da tela de login são nacionais e read-only

Os 3 números exibidos na tela de login (2,45M alunos, 98.310 escolas sem AEE, 5.570 municípios mapeados) são agregados nacionais calculados a partir do mesmo dataset do Censo usado pelo Score IncluIA (ver [[score-incluia]]) — não são específicos do usuário logado e não mudam por perfil.

**Como aplicar**: podem ser cacheados de forma agressiva (ex.: 24h ou até a próxima atualização do Censo), pois não dependem de usuário nem de sessão.

## RN-06 — O sistema é público; só o Diagnóstico IA exige autenticação

Mapa, Indicadores do Município e Escolas são acessíveis **sem login** — a porta de entrada do produto (`/`) leva direto ao Mapa, não à tela de Login. Só a aba "🤖 Diagnóstico IA" exige uma conta: ao clicar nela sem estar autenticado, o usuário é redirecionado para `/login?redirect=...` e, após autenticar, volta automaticamente para a mesma aba do mesmo município (`?aba=diagnostico`). Qualquer usuário autenticado acessa o Diagnóstico IA de **qualquer** município — não há escopo por perfil/UF (ver RN-03, revogada).

**Por quê**: o Diagnóstico IA é a única funcionalidade do produto com custo real por uso (cada chamada aciona Gemini, Groq ou Mistral) — as demais telas só leem dados já processados do Censo, sem custo marginal por visita. Abrir o resto do produto ao público maximiza o alcance/transparência (é dado público do Censo Escolar), enquanto a barreira de login contém o custo de IA a usuários identificáveis.

**Como aplicar**: a barreira real é no backend — `backend/app/features/diagnostico_ia/router.py` aplica a dependência `exigir_usuario_autenticado` (`backend/app/shared/auth.py`) a todas as suas rotas; o redirecionamento de UI é só conveniência de UX, nunca a única proteção. Qualquer rota nova de diagnóstico-ia herda a proteção automaticamente por estar registrada no mesmo `APIRouter`.
