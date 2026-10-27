# Regras de Negócio — Login / Autenticação

> **Desativado em 2026-10-27** ([impacto da Fase 2](../sdd/fase-2/impacto-fase-1.md)). A área pública não tem login; o Diagnóstico IA virou uma leitura pública sem conta. O único login do produto é o da Gestão Ativa (código por e-mail, só para diretores e secretarias com vínculo validado — [requisitos de acesso](../sdd/fase-2/requirements/acesso-gestao-ativa.md)). `/login` redireciona para `/gestao/entrar`; as rotas `/auth/*` e o autocadastro saíram do ar. Este documento fica como histórico. Pendente: o destino das contas já gravadas na tabela `usuarios` de `data/incluia.db`.

## RN-01 — Autenticação de gestor é simulada no MVP; autocadastro público existe para o Diagnóstico IA

As contas de gestor (**Secretário Municipal**/**Secretário Estadual**) continuam sendo provisionadas manualmente (seed), sem tela de cadastro — mesma simulação de sempre. A integração com **gov.br SSO** é explicitamente **Fase 2** (`context.md` §7.2) — o botão correspondente deve permanecer visível, porém desabilitado, para comunicar o roadmap ao usuário sem implementá-lo.

Já o público em geral (famílias, imprensa, sociedade civil, pesquisadores) **tem autocadastro real** via `POST /auth/registrar`, oferecido na aba "Criar conta" da tela de login contextual do Diagnóstico IA (ver RN-06) — reverte a restrição original desta regra para esse público, mantendo-a para os perfis de gestor.

**Por quê**: alinhamento ao documento MVP5 quanto ao SSO gov.br (fora de escopo) e à decisão de produto de que o Diagnóstico IA — único recurso com custo real por chamada de IA — deve ser acessível a qualquer cidadão identificável, não só a gestores previamente cadastrados.

## RN-02 — Um usuário pertence a exatamente um perfil

Cada conta tem um perfil fixo no momento do cadastro. Perfis de gestor (provisionados manualmente): **Secretário Municipal**, **Secretário Estadual**. Perfis públicos (autocadastro): **Família/responsável**, **Jornalista/imprensa**, **Sociedade civil/ONG**, **Secretário(a) de Educação**, **Pesquisador(a)**, **Poder público/gestor**. Não há troca de perfil dentro da mesma sessão nem contas com múltiplos perfis simultâneos no MVP.

**Como aplicar**: o campo `perfil` não restringe o acesso a município (ver histórico da RN-03, revogada) — hoje serve só para exibição (cargo no cabeçalho) e para eventual telemetria futura. Contas de perfil público não têm `municipioId`/`uf` associados (o autocadastro não coleta essa informação — RN-06 já garante acesso a qualquer município independente do perfil).

## RN-03 — Revogada: escopo de acesso a município por perfil (histórico)

**Redação original** (nunca chegou a ser implementada — nenhum endpoint validava o JWT emitido no login): "Secretário Municipal só pode visualizar dados do `municipioId` vinculado à sua conta; Secretário Estadual, todos os municípios da `uf` vinculada."

**Status atual**: revogada. Substituída por **RN-06** — o produto pivotou de "multi-tenant por secretaria" para "público, exceto Diagnóstico IA": Mapa, Indicadores e Escolas são públicos para qualquer visitante (sem exigir conta), e o Diagnóstico IA exige apenas estar autenticado — **qualquer** usuário cadastrado pode gerar diagnóstico de **qualquer** município, não só do seu. Mantida aqui só por histórico, para quem procurar a decisão original.

## RN-04 — Nenhuma tela de erro genérica de autenticação deve revelar existência de conta

Mensagens de erro de login devem ser idênticas para "e-mail não cadastrado" e "senha incorreta" (ex.: "E-mail ou senha inválidos").

**Por quê**: prática padrão de segurança para evitar enumeração de contas institucionais.

## RN-05 — Estatísticas da tela de login são nacionais e read-only

Os 3 números exibidos na tela de login (2,45M alunos, 98.310 escolas sem AEE, 5.570 municípios mapeados) são agregados nacionais calculados a partir do mesmo dataset do Censo usado pelo Score Escola Sem Barreiras (ver [[score-incluia]]) — não são específicos do usuário logado e não mudam por perfil.

**Como aplicar**: podem ser cacheados de forma agressiva (ex.: 24h ou até a próxima atualização do Censo), pois não dependem de usuário nem de sessão.

## RN-06 — O sistema é público; só o Diagnóstico IA exige autenticação

Mapa, Indicadores do Município e Escolas são acessíveis **sem login** — a porta de entrada do produto (`/`) leva direto ao Mapa, não à tela de Login. Só a aba "🤖 Diagnóstico IA" exige uma conta: ao clicar nela sem estar autenticado, o usuário é redirecionado para `/login?redirect=...` e, após autenticar, volta automaticamente para a mesma aba do mesmo município (`?aba=diagnostico`). Qualquer usuário autenticado acessa o Diagnóstico IA de **qualquer** município — não há escopo por perfil/UF (ver RN-03, revogada).

**Tela de login contextual**: quando o `redirect` aponta para uma rota de Diagnóstico IA, `/login` exibe uma tela dedicada (ícone + "Diagnóstico com IA" + nome do município, quando conhecido pelo `useAppStore`) com abas "Criar conta" (autocadastro público — RN-01) e "Entrar" (credenciais existentes), em vez do layout institucional genérico de 2 colunas. Esse layout genérico permanece para quem chega em `/login` sem esse contexto (ex.: link "Entrar" do cabeçalho).

**Por quê**: o Diagnóstico IA é a única funcionalidade do produto com custo real por uso (cada chamada aciona Gemini, Groq ou Mistral) — as demais telas só leem dados já processados do Censo, sem custo marginal por visita. Abrir o resto do produto ao público maximiza o alcance/transparência (é dado público do Censo Escolar), enquanto a barreira de login contém o custo de IA a usuários identificáveis.

**Como aplicar**: a barreira real é no backend — `backend/app/features/diagnostico_ia/router.py` aplica a dependência `exigir_usuario_autenticado` (`backend/app/shared/auth.py`) a todas as suas rotas; o redirecionamento de UI é só conveniência de UX, nunca a única proteção. Qualquer rota nova de diagnóstico-ia herda a proteção automaticamente por estar registrada no mesmo `APIRouter`.
