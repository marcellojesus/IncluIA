# Requisitos — Secretário | Fila e Revisão de Planos Escolares

**Status:** Implementado · notas de implementação até 2026-10-26  
**PRD:** RF-02 e RF-18 a RF-22

## Objetivo

Oferecer ao secretário municipal uma entrada própria para Gestão Ativa e uma fila de análise das escolas da rede que submeteram Plano de Ação.

## Fluxo

1. Após autenticação/autorização, o secretário entra no painel municipal, separado da experiência do diretor.
2. A fila mostra escolas com ao menos uma versão submetida, estado da revisão e data da última submissão.
3. O secretário abre a escola e consulta a versão submetida, Declaração de Obstáculos e histórico permitido.
4. O secretário aceita, solicita ajustes ou reprova a versão.
5. A decisão e comentários ficam visíveis ao diretor da escola correspondente.

## Requisitos funcionais

- **SFR-RF-01:** apresentar tela de entrada e navegação específicas para secretário, com escopo do município autorizado.
  - **Aceite:** diretor não vê a fila municipal; secretário não consulta redes de outros municípios.
- **SFR-RF-02:** listar escolas que possuem pelo menos um Plano de Ação submetido.
  - **Aceite:** a lista mostra a versão mais recente e o estado; ausência de submissão não é interpretada como ausência de obstáculos.
- **SFR-RF-03:** permitir abrir plano submetido junto com a versão da Declaração de Obstáculos em que ele se baseia, dentro da autorização.
  - **Aceite:** se a escola emitiu versão mais nova da declaração depois da submissão, a revisão mostra o aviso.
- **SFR-RF-04:** oferecer decisões “Aceitar”, “Solicitar ajustes” e “Reprovar”.
  - **Aceite:** pedir ajustes exige comentário; reprovar exige justificativa; aceitar não requer comentário de bloqueio.
- **SFR-RF-05:** associar toda decisão ao secretário, versão, data e comentário/justificativa.
- **SFR-RF-06:** disponibilizar a decisão ao diretor da escola, sem expor decisões de escolas alheias.
- **SFR-RF-07:** preservar versões e permitir nova submissão após ajustes, conforme política para reprovação a decidir.

## Estados exibidos

Aguardando análise, ajustes solicitados, aceita, reprovada e substituída por nova versão. Estado de financiamento/execução é distinto e não é inferido pela aprovação.

## Notas de implementação (2026-10-25)

- **Código:**
  - backend em `backend/app/features/plano/revisao.py` e `router_secretario.py` (rotas sob `/gestao/secretario/planos`), sem migração nova;
  - frontend em `features/gestao-ativa/components/FilaPlanos.tsx`, na aba "Planos das escolas" do painel do secretário;
  - testes em `backend/tests/test_revisao_planos.py`.
- **SFR-RF-01 e 02:**
  - o município vem do vínculo aprovado;
  - escola de outra rede, ou sem versão enviada, responde 404, inclusive na decisão (testado com secretário de outro município);
  - a fila mostra só escolas com versão enviada, as em análise primeiro;
  - o aviso diz que ausência na fila não é ausência de necessidade.
- **SFR-RF-03:**
  - a revisão mostra os itens congelados por horizonte, com origem (IA, editada, escola), fontes e premissas;
  - tem link para a Declaração base e aviso quando a escola já emitiu Declaração mais nova;
  - rascunho, sugestões da IA e quem enviou não são expostos.
- **SFR-RF-04 e 05:**
  - pedir ajustes e reprovar exigem comentário de 10 caracteres ou mais; aceitar não exige;
  - a decisão grava secretário, data e comentário;
  - só a versão mais recente, em análise, pode ser decidida, numa atualização condicional: entre duas decisões simultâneas, a segunda recebe 409;
  - a auditoria guarda só escola e versão, sem o comentário.
- **Apontamentos (2026-10-26, migração `632f9641fa05`):**
  - ao pedir ajustes ou reprovar, o secretário pode marcar barreiras e ações específicas, com uma nota curta opcional (500 caracteres, pelo Guardião);
  - a barreira precisa estar na Declaração base, e a ação, na própria versão; aceitar não leva apontamentos;
  - cada item enviado guarda a ação de origem do rascunho (`acao_id`). Assim, o diretor vê destacados em laranja o eixo, a barreira e a ação apontados, com a nota;
  - os destaques somem quando ele envia a nova versão; os apontamentos ficam na versão decidida;
  - a revisão do secretário passa a agrupar o plano por barreira, inclusive as barreiras com relato e sem ação.
- **SFR-RF-06:** o diretor vê o estado, o comentário e o **nome de quem decidiu** (RN-SFR-04), só da própria escola. A tela do secretário avisa que o comentário fica visível ao diretor com o nome dele.
- **SFR-RF-07:**
  - depois de qualquer decisão, a escola pode enviar nova versão; as anteriores ficam com a decisão e aparecem como "substituída";
  - hoje isso vale também após reprovação; a política definitiva segue pendente.
- **LGPD:**
  - o comentário passa pelo Guardião: dado de risco alto bloqueia (422) e o nome é mascarado, com aviso ao secretário;
  - o filtro da fila é só por município, o que funciona porque o piloto vincula apenas escolas da rede municipal; se outras redes entrarem, será preciso gravar a rede na versão.
- **Pendente:** o nome completo do secretário aparece para o diretor; registrar isso no aviso de privacidade do cadastro de secretários.

## Decisões pendentes

Prazo de análise, permissões de substitutos, aceitar com recomendações opcionais, política de reenvio após reprovação e mecanismo de notificação.
