# Requisitos — Login / Autenticação

Fonte de interface: `interface.md` §2. Fonte de contexto: `context.md` (perfis de acesso), `arquitetura.md` (backend FastAPI).

## Objetivo

Permitir que um gestor de secretaria de educação (municipal ou estadual) se autentique para acessar o Diagnóstico IA — a única funcionalidade do produto que exige login (RN-06 de `docs/business-rules/login.md`; Mapa, Indicadores e Escolas são públicos) — sem exigir integração com gov.br SSO no MVP.

## Atores

- **Secretário Municipal** / **Secretário Estadual** — contas de gestor, provisionadas manualmente (seed), sem cadastro público.
- **Público em geral** (família/responsável, jornalista/imprensa, sociedade civil/ONG, pesquisador, poder público) — cria a própria conta na tela de Diagnóstico IA.

## Pré-condições

- Perfis de gestor: usuário possui uma conta previamente cadastrada (cadastro em si é fora do escopo do MVP — provisionamento manual/seed).
- Perfis públicos: nenhuma — a conta é criada na hora, na própria tela de login contextual do Diagnóstico IA (RF-09).

## Requisitos Funcionais

- **RF-01**: A tela de login deve exibir um botão "Entrar com gov.br", visivelmente desabilitado e marcado como "Fase 2" — não deve disparar nenhuma ação.
- **RF-02**: A tela de login deve oferecer autenticação por e-mail institucional + senha.
- **RF-03**: Ao submeter credenciais válidas, o sistema autentica o usuário, identifica seu perfil (Municipal/Estadual) e o município/UF associado, e redireciona para a tela de Mapa da Inclusão.
- **RF-04**: Ao submeter credenciais inválidas, o sistema deve exibir mensagem de erro clara, sem revelar se o e-mail existe ou não (evitar enumeração de contas).
- **RF-05**: Durante a autenticação, o botão de login deve indicar estado de carregamento (ex.: "Entrando…") e ficar desabilitado para evitar múltiplos submits.
- **RF-06**: A tela de login deve exibir estatísticas institucionais fixas (alunos com deficiência no Brasil, escolas sem AEE, municípios mapeados) — dados agregados nacionais, atualizados junto com o dataset do Censo vigente.
- **RF-07**: Deve existir um botão "Sair" visível no header do app em qualquer tela pós-login, que encerra a sessão e retorna à tela de login.
- **RF-08**: Após logout, a próxima entrada não deve reaproveitar UF/município previamente selecionados na sessão anterior — o usuário reinicia no mapa padrão do seu perfil.
- **RF-09**: Ao clicar na aba "🤖 Diagnóstico IA" (ou navegar direto para ela via URL) sem estar autenticado, o sistema redireciona para a tela de login com um parâmetro de retorno (`?redirect=...`); após autenticar com sucesso, o sistema volta automaticamente para o mesmo município na aba Diagnóstico IA, sem exigir nova navegação manual. Nesse caso, a tela de login exibe um layout contextual (ícone, título e descrição do Diagnóstico IA) com abas "Criar conta" e "Entrar", em vez do layout institucional genérico.
- **RF-10**: O parâmetro de retorno só é aceito se apontar para um caminho interno do próprio sistema (começar com `/`) — nunca redirecionar para uma URL externa vinda da querystring.
- **RF-11**: Na aba "Criar conta" da tela contextual do Diagnóstico IA, o público em geral se autocadastra informando nome completo, perfil ("Você é": família/responsável, jornalista/imprensa, sociedade civil/ONG, secretário(a) de educação, pesquisador(a) ou poder público/gestor), e-mail e senha. Ao concluir, o sistema já autentica a conta criada e redireciona para o `redirect` recebido, sem exigir login separado em seguida.
- **RF-12**: Se o e-mail informado no autocadastro já existir, o sistema deve rejeitar com uma mensagem clara (ex.: "Este e-mail já está cadastrado"), sem criar uma segunda conta nem sobrescrever a existente.

## Requisitos Não Funcionais

- **RNF-01**: Senhas nunca devem ser armazenadas em texto puro (hash + salt).
- **RNF-02**: Sessão deve expirar após um período de inatividade configurável (sugestão inicial: 8h, alinhado a jornada de trabalho).
- **RNF-03**: Preparar o modelo de dados de usuário para acomodar, no futuro, um `sub` do gov.br SSO sem quebrar contas já cadastradas por e-mail/senha (não implementar SSO agora, apenas não bloquear a evolução).

## Dados de entrada/saída

**Entrada (login)**: e-mail, senha.
**Entrada (autocadastro público)**: nome completo, e-mail, senha, perfil (`familia`|`imprensa`|`sociedade_civil`|`secretario_educacao`|`pesquisador`|`poder_publico`).
**Saída (sessão autenticada)**: `{ usuarioId, nome, perfil, municipioId?, uf? }` — `municipioId`/`uf` só existem para contas de gestor (seed); contas públicas não os têm.

## Fluxo principal

1. Usuário acessa a URL do sistema → cai direto na tela de Mapa (pública, RN-06), sem precisar de login.
2. Usuário navega livremente por Mapa, Indicadores e Escolas sem se autenticar.
3. Ao clicar em "🤖 Diagnóstico IA", se não autenticado, vai para a tela de login com `?redirect=` apontando para a aba que tentou abrir.
4. Preenche e-mail e senha → clica "Entrar".
5. Backend valida credenciais e retorna token de sessão + perfil do usuário.
6. Frontend redireciona para o `redirect` recebido (a aba Diagnóstico IA do município de origem) ou, se acessado direto por `/login`, para o Mapa.

## Fluxos alternativos

- **Credenciais inválidas**: exibir erro inline no formulário, sem redirecionar.
- **Perfil Municipal sem município associado no cadastro**: bloquear login com mensagem orientando contato com o suporte (situação de dado inconsistente, não deve ocorrer em operação normal).
- **Sessão expira enquanto a aba Diagnóstico IA já está aberta**: a próxima chamada à API (ex.: enviar mensagem no chat) retorna 401; a tela mostra uma mensagem convidando a fazer login novamente, em vez de um erro genérico.

## Critérios de aceite

- [ ] Login com credenciais válidas redireciona ao mapa correto para o perfil do usuário.
- [ ] Login com credenciais inválidas não autentica e exibe erro.
- [ ] Botão "Entrar com gov.br" nunca é clicável no MVP.
- [ ] Logout limpa a sessão e qualquer estado de UF/município em memória.
- [ ] Acessar o Mapa, um Município (aba Indicadores/Escolas) sem estar logado nunca pede login.
- [ ] Clicar em "🤖 Diagnóstico IA" sem login vai para `/login`; logar em seguida volta para a mesma aba do mesmo município.
- [ ] Nesse fluxo, `/login` mostra a tela contextual (ícone + "Diagnóstico com IA" + abas Criar conta/Entrar), não o layout institucional genérico.
- [ ] Criar conta com um e-mail novo autentica na hora e volta para o Diagnóstico IA do município de origem.
- [ ] Criar conta com um e-mail já cadastrado é rejeitado com mensagem clara, sem duplicar a conta.
