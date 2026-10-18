# Requisitos — Diretor | Dashboard da Situação Atual da Escola

**Status:** Proposta para validação  
**PRD:** RF-01, RF-02, RF-33, RF-35 e RF-38  
**Dependência:** acesso aprovado e vínculo ativo com a escola

## Objetivo

Ser a tela inicial do diretor na Gestão Ativa e oferecer uma visão ampliada e privada da situação da escola antes de iniciar o registro dos obstáculos.

## Conteúdo proposto

- Identificação da escola e edição/ano dos dados apresentados.
- Score geral, faixa e explicação de que se trata de indicador calculado, não de certificação legal.
- Situação detalhada nos quatro eixos da PNEEI, com indicadores e dados de origem disponíveis.
- Barreiras identificadas por eixo e sinalização de quais têm obstáculo registrado ou permanecem sem contexto.
- Declaração de Obstáculos existente, Plano de Ação atual, submissões e decisões municipais.
- Ação principal para **Registrar obstáculos**, habilitada a partir da revisão dos eixos/barreiras, além de acesso ao Plano de Ação quando aplicável.

## Requisitos funcionais

- **DSE-RF-01:** abrir este dashboard como tela inicial do diretor após autenticação e autorização.
  - **Aceite:** diretor é encaminhado apenas à escola do vínculo ativo; solicitações pendentes não entram no dashboard.
- **DSE-RF-02:** apresentar score geral, faixa, quatro eixos e indicadores disponíveis em visão ampliada.
  - **Aceite:** cada métrica identifica fonte/edição do Censo; dado ausente aparece como indisponível, não como zero.
- **DSE-RF-03:** apresentar barreiras por eixo e a posição registrada pelo diretor (sem posição, rascunho, obstáculo relatado, divergência com o Censo, sem relato nesta versão).
  - **Aceite:** obstáculo confirmado, rascunho e ausência de registro são estados distintos; nenhum deles altera o indicador de origem.
- **DSE-RF-04:** apresentar status e atalhos para Declaração de Obstáculos (rascunho, emitida vN, publicada vN) e Plano de Ação, incluindo decisão municipal mais recente. O atalho do Plano de Ação só fica ativo após a emissão da declaração.
- **DSE-RF-05:** oferecer ação explícita para iniciar a Declaração de Obstáculos a partir da situação da escola.
  - **Aceite:** iniciar o fluxo leva à feature própria e preserva escola/eixo/barreira selecionados quando aplicável.
- **DSE-RF-06:** impedir que dados deste dashboard sejam acessíveis por outro diretor ou por visitante público.
  - **Aceite:** autorização é validada no servidor; a interface pública da escola continua independente.

## Decisões pendentes

Quais indicadores detalhados serão exibidos além dos quatro eixos; como mostrar data/edição dos dados; se score deve ser apresentado em destaque ou contextualizado; comportamento quando dados do Censo e relato do diretor divergem.
