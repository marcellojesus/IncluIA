# Requisitos — Cadastro, validação de vínculo e acesso à Gestão Ativa

**Status:** Implementado no piloto (rede municipal) · notas de implementação atualizadas em 2026-10-26  
**Rastreabilidade:** Documento de Requisitos do Produto (PRD) geral B2-13; PRD da Fase 2 RF-01 e RF-03 a RF-06  
**Data:** 2026-10-11

## Objetivo

Habilitar acesso ao módulo Gestão Ativa somente a diretores de escola e secretários municipais cuja identidade e vínculo institucional tenham sido verificados por um fluxo aprovado. O módulo não usará gov.br no produto mínimo viável (MVP). As páginas públicas da Fase 1 continuarão públicas e independentes desta autorização.

## Atores

- **Candidato a diretor:** solicita vínculo com uma escola identificada pelo código do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP; campo `CO_ENTIDADE`).
- **Diretor aprovado:** usuário associado a uma única escola por vez.
- **Secretário municipal:** usuário associado a uma rede municipal.
- **Administrador autorizado do produto:** valida e provisiona inicialmente contas de secretário.
- **Autoridade educacional ou mantenedora autorizada:** confirma a identidade e o vínculo funcional do diretor, conforme a dependência administrativa da escola.

## Fluxo 1 — Habilitação inicial do secretário

1. O administrador autorizado do produto identifica a secretaria municipal e seu representante por canais institucionais independentes dos dados fornecidos no pedido de cadastro.
2. O administrador registra um convite para o secretário, limitado ao município correspondente.
3. O secretário confirma o controle do canal institucional por código de uso único e aceita o convite.
4. O administrador registra aprovador, data, método de verificação e município associado.
5. A conta fica ativa somente após a confirmação e o provisionamento; antes disso não acessa Gestão Ativa.

## Fluxo 2 — Solicitação de acesso do diretor

1. O candidato informa nome, canal institucional de contato e código INEP da escola em que declara atuar como diretor.
2. O sistema valida que o código identifica uma escola existente e cria uma solicitação `pendente`; o candidato ainda não acessa Gestão Ativa.
3. O candidato confirma controle do e-mail ou telefone informado por código de uso único. Essa etapa confirma o canal, não o cargo.
4. A solicitação é encaminhada à autoridade educacional ou mantenedora autorizada responsável pela escola. Essa pessoa consulta seus registros funcionais ou evidência oficial vigente obtida por canal institucional.
5. O aprovador confirma ou rejeita o vínculo, registrando sua identidade, data e método. O próprio candidato não pode aprovar a solicitação.
6. Após aprovação, o sistema ativa a conta e associa o diretor somente à escola aprovada. Após rejeição, a solicitação permanece sem acesso e o candidato recebe instrução para contestar ou corrigir os dados.

## Requisitos funcionais

Os identificadores RF correspondem a requisitos funcionais.

- **RF-01:** O módulo Gestão Ativa deve aceitar somente os perfis Diretor de escola e Secretário municipal de educação com estado de acesso ativo.
  - **Aceite:** conta pública da Fase 1, visitante anônimo, perfil diferente ou conta pendente/rejeitada/suspensa não acessa nenhuma tela nem rota da Gestão Ativa.
- **RF-02:** O candidato a diretor deve informar nome, contato e código INEP da própria escola para solicitar acesso.
  - **Aceite:** a solicitação referencia uma escola existente; o nome ou código informado não concede acesso automaticamente.
- **RF-03:** Toda solicitação de diretor deve iniciar como pendente.
  - **Aceite:** antes da aprovação institucional, chamadas diretas às rotas protegidas são negadas no servidor e não revelam dados da escola.
- **RF-04:** O sistema deve permitir confirmar o controle do canal de contato por código de uso único.
  - **Aceite:** código expirado, já utilizado ou inválido não confirma o canal; o sistema aplica limites de tentativa e reenvio definidos na implementação.
- **RF-05:** Um aprovador institucional autorizado deve confirmar o vínculo atual entre a pessoa e a escola antes da ativação.
  - **Aceite:** aprovação exige uma fonte institucional independente do candidato, identifica o aprovador e registra data e método; o candidato não pode aprovar a própria solicitação.
- **RF-06:** Contas de secretário municipal devem ser provisionadas por administrador autorizado do produto, sem cadastro público com autoatribuição do perfil.
  - **Aceite:** o município é associado durante o provisionamento e a identidade/função é confirmada por canal institucional oficial, com trilha de auditoria.
- **RF-07:** O sistema deve aplicar escopo de autorização no servidor.
  - **Aceite:** diretor só consulta ou altera registros da escola vinculada; secretário só consulta ou altera registros da rede municipal vinculada; alterar parâmetros da requisição não amplia o escopo.
- **RF-08:** O sistema deve registrar criação, aprovação, rejeição, troca de vínculo, suspensão e revogação de acesso.
  - **Aceite:** cada evento contém ator responsável, data/hora, alvo, resultado e método ou justificativa, sem guardar credenciais ou códigos de uso único.
- **RF-09:** O sistema deve permitir rejeitar, suspender ou revogar o acesso e informar o procedimento de correção/contestação.
  - **Aceite:** o estado inativo impede imediatamente o uso de novas rotas protegidas; mudanças de escola/rede exigem nova aprovação.
- **RF-10:** A criação de conta não deve exigir integração com gov.br no MVP.
  - **Aceite:** nenhum fluxo depende de login gov.br; a implementação não deve simular identidade oficial ou sugerir autenticação governamental.
- **RF-11:** O fluxo deve minimizar dados pessoais coletados.
  - **Aceite:** cópia de documento pessoal não é obrigatória por padrão; qualquer exceção precisa de justificativa, prazo de retenção, controle de acesso e aprovação de privacidade/jurídica.
- **RF-12:** A camada de autenticação/autorizações da Gestão Ativa deve ser separada do acesso público da Fase 1.
  - **Aceite:** adicionar ou revogar permissões no módulo não exige login para dashboard, escolas ou comparação públicas da Fase 1.

## Dados mínimos propostos

- Conta: identificador, nome, e-mail e/ou telefone institucional confirmado, papel, estado da conta e datas de criação/alteração.
- Vínculo de diretor: código INEP da escola, estado do vínculo, autoridade aprovadora, data e método/referência da confirmação.
- Vínculo de secretário: código/identificador do município, administrador aprovador, data e método de provisionamento.
- Auditoria: eventos de solicitação, confirmação, aprovação, rejeição, alteração e revogação.

Não armazenar código INEP como prova de identidade, senha em texto puro, códigos de uso único depois do processamento ou cópias de documentos pessoais por padrão.

## Requisitos não funcionais

- Autorização aplicada e testada no servidor, não apenas por ocultação de páginas na interface.
- Senhas e tokens protegidos conforme os padrões de segurança adotados pelo produto; códigos de confirmação têm validade curta, uso único e armazenamento seguro.
- Auditoria acessível apenas a operadores autorizados. Retenção de 5 anos, sem alteração ([retencao.md](../business-rules/retencao.md), RN-RET-03).
- Interface de aprovação acessível e com estados explícitos de pendente, aprovada, rejeitada, suspensa e revogada.

## Decisões pendentes

1. **Resolvida em 2026-10-23:** o piloto fica restrito às escolas da rede municipal.
2. **Resolvida em 2026-10-23 para o piloto:** o secretário municipal aprova os diretores das escolas da própria rede. Continua pendente como delegar ou substituir essa autoridade.
3. Definir fonte institucional mínima aceita para confirmar o vínculo, especialmente quando não houver diretório público ou ato de designação facilmente consultável.
4. Definir se o secretário pode convidar diretamente diretores ou apenas revisar solicitações encaminhadas.
5. Definir prazos de expiração das solicitações, códigos, revisão periódica e contestação.
6. Definir como a equipe administradora do produto valida o primeiro secretário de cada município.

## Limite conhecido da fonte Censo

A `Tabela_Gestor_Escolar_2025.csv` local contém o código da escola e campos agregados, incluindo a quantidade de gestores que declararam a função de diretor (`QT_GEST_BAS_DIRETOR`). Ela não contém nome nem contato individual e não permite identificar automaticamente o candidato. Ver [microdados oficiais do Censo Escolar no INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar).

## Notas de implementação (2026-10-23, revisadas em 2026-10-26)

- **Código:**
  - backend em `backend/app/features/acesso/` (constantes em `seguranca.py`), banco próprio da Gestão Ativa via SQLAlchemy/Alembic;
  - telas `/participar`, `/gestao/entrar`, `/gestao/secretario` (aba "Vínculos de diretores") e `/gestao/admin`;
  - testes em `backend/tests/test_acesso_gestao.py`.
- **Entrada sem senha:** e-mail → código de 6 dígitos → sessão. Não há senha nem telefone; o canal confirmado é só o e-mail (RF-02, RF-04).
- **Código de uso único:**
  - válido por 10 minutos, com no máximo 5 tentativas; um código novo invalida os anteriores;
  - reenvio a cada 60 s, no máximo 5 códigos por hora e 10 por dia por e-mail; 20 erros por dia bloqueiam o e-mail;
  - guardado como HMAC; o consumo é atômico;
  - ao atingir um limite, a resposta é a mesma de um envio normal, e e-mail desconhecido também recebe a mesma resposta.
- **Limite por IP:** 30 requisições a cada 10 minutos nas rotas anônimas (em memória, por processo); acima disso, 429.
- **Sessão:** token JWT de 8 horas, com audiência e segredo próprios da Gestão Ativa, guardado só na aba do navegador. O estado da conta e do vínculo é relido a cada requisição, e o token da Fase 1 é recusado (RF-12).
- **Segredos:** `GESTAO_SEGREDO_TOKEN` e `GESTAO_SEGREDO_CODIGO`, com no mínimo 32 bytes fora do ambiente de desenvolvimento. Sem eles, ou sem provedor de e-mail, só a Gestão Ativa responde 503 e o site público continua no ar.
- **Perfis:** além de diretor e secretário (RF-01), existe o perfil **administrador**, criado só pela linha de comando (`python -m app.features.acesso.cli criar-admin`), que provisiona secretários e pode retirar publicações.
- **Aprovação do diretor (RF-05; decisões de 2026-10-23):**
  - só escolas da rede municipal são aceitas;
  - quem aprova é o secretário do município da escola;
  - o pedido só aparece ao secretário depois que o candidato confirma o código daquele pedido;
  - quem decide não pode decidir o próprio vínculo;
  - a fonte institucional é declarada pelo secretário numa lista fechada (ofício, sistema da rede, telefone institucional, presencial, outro) com texto descritivo; o sistema registra, mas não verifica a fonte.
- **Estados do vínculo:** pendente, aprovado, rejeitado, suspenso e revogado. Suspenso pode ser **reativado**; revogado é final, e voltar exige pedido novo. Cada decisão usa motivos em lista fechada e texto de 5 a 1000 caracteres, que passa pelo Guardião LGPD (dado sensível é recusado).
- **Secretário (RF-06):** provisionado pelo administrador, com município validado no Censo e método (ofício, telefone institucional, Diário Oficial, outro). O "aceite do convite" é a primeira entrada com código.
- **Retenção:** pedidos nunca confirmados são apagados em 72 horas e registros de código em 24 horas. A limpeza roda na subida do servidor e pela linha de comando (`limpar`).
- **Auditoria (RF-08):** só inserção, sem código nem token; o evento guarda a categoria do motivo, e o texto livre fica no vínculo.
- **Ambiente de desenvolvimento:**
  - `EMAIL_MODO=console` só vale com `AMBIENTE=dev`;
  - a caixa de e-mails de teste fica em `/gestao/dev/emails`, só em dev e só pela própria máquina, com até 30 mensagens em memória;
  - `python -m app.features.acesso.cli demo` cria administrador, secretária de Niterói e um pedido de diretora (e-mails `@demo.local`).
- **Ainda não implementado:**
  - telefone como canal;
  - suspensão e revogação de secretário (RF-09, RN-06 e RN-12 valem hoje só para o diretor);
  - evento próprio de "troca de vínculo" (hoje é revogação mais novo pedido);
  - tela de consulta da auditoria (o prazo de retenção foi definido em 2026-11-03: 5 anos, [retencao.md](../business-rules/retencao.md));
  - convite de diretor pelo secretário (o secretário só revisa pedidos);
  - provedor de e-mail real para produção (pendência 3 da AD-02).
