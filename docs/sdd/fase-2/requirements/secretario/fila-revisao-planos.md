# Requisitos — Secretário | Fila e Revisão de Planos Escolares

**Status:** Proposta para validação  
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

## Decisões pendentes

Prazo de análise, permissões de substitutos, aceitar com recomendações opcionais, política de reenvio após reprovação e mecanismo de notificação.
