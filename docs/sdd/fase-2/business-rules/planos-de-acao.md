# Índice de Regras de Negócio — Funcionalidades da Gestão Ativa

Este arquivo é somente o mapa das regras; cada funcionalidade mantém suas regras específicas separadas por perfil e responsabilidade.

## Diretor

- **Dashboard da Situação Atual da Escola:** visão privada baseada nos dados e regras oficiais, separada da página pública. Ver [regras](diretor/dashboard-situacao-escola.md).
- **Declaração de Obstáculos:** distingue barreira, obstáculo e confirmação do diretor. Ver [regras](diretor/declaracao-obstaculos.md).
- **Plano de Ação Escolar:** IA sugere; diretor escolhe e submete uma versão. Ver [regras](diretor/plano-acao-escolar.md).

## Secretário Municipal

- **Dashboard Municipal:** entrada privada com prioridades e fila; não mistura status de submissão com classificação de criticidade. Ver [regras](secretario/dashboard-municipal.md).
- **Fila e Revisão de Planos:** secretário decide sobre uma versão submetida, com histórico e justificativas. Ver [regras](secretario/fila-revisao-planos.md).
- **Analítico de Barreiras:** métricas são reproduzíveis e inferências da IA permanecem identificadas. Ver [regras](secretario/analitico-barreiras.md).
- **Plano Estratégico Municipal:** pode cobrir ações escolares por inteiro ou parcialmente, sem alterar o estado do restante do plano. Ver [regras](secretario/plano-estrategico-municipal.md).

## Compartilhadas

As regras de cadastro, verificação e escopo de acesso ficam em [Acesso à Gestão Ativa](acesso-gestao-ativa.md). O acesso continua separado por papel e unidade escolar/rede.

Os **Documentos em PDF** só saem de versões congeladas, seguem o mesmo acesso da tela e não usam IA. Ver [regras](documentos-pdf.md).
