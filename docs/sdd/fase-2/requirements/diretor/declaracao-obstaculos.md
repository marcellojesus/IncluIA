# Requisitos — Diretor | Declaração de Obstáculos

**Status:** Implementado, com publicação e retirada · notas de implementação até 2026-10-24  
**PRD:** RF-07 a RF-11, RF-32 e RF-39 a RF-42  
**Dependência:** acesso aprovado à escola, conforme `../acesso-gestao-ativa.md`

## Objetivo

Permitir que o diretor explique, barreira por barreira, a situação da escola diante das lacunas identificadas nos dados do Censo Escolar e **emita** uma Declaração de Obstáculos: a justificativa formal da escola, visível ao secretário da rede e, depois de publicada, ao público. A versão emitida é o contexto que a IA usa para construir o Plano de Ação.

## Fluxo

1. O diretor consulta as barreiras da escola, agrupadas por eixo, com sua origem nos dados. Pode registrar todos os eixos em sequência ou um eixo por vez.
2. Para cada barreira, registra uma **posição**:
   - **Obstáculo relatado:** a IA conversacional pergunta sobre o obstáculo, aprofunda o relato e apresenta uma formulação estruturada; o diretor revisa, corrige e confirma ou retorna à conversa.
   - **Divergência com o dado do Censo:** o diretor descreve a realidade da escola que o dado não reflete.
   - **Sem relato nesta versão:** escolha explícita de não relatar a barreira nesta versão.
3. Quando todas as barreiras têm posição, o diretor revisa a Declaração consolidada e a **emite**. A emissão congela a versão e a torna visível ao secretário.
4. Opcionalmente, o diretor **publica** a versão emitida: o sistema gera a versão pública, aponta possíveis dados pessoais e o diretor aprova.
5. Para mudar uma declaração emitida, o diretor **retifica**: altera posições e emite nova versão.

## Requisitos funcionais

- **DO-RF-01:** listar barreiras por eixo com variável/fonte do Censo e a posição registrada.
  - **Aceite:** dado observado, barreira inferida pela regra do produto e posição do diretor aparecem diferenciados.
- **DO-RF-02:** conduzir conversa contextualizada para cada barreira e solicitar aprofundamento quando necessário.
  - **Aceite:** a IA não confirma nem encerra o registro sem revisão explícita do diretor; o texto gerado é factual e neutro, sem atribuir culpa a pessoas ou órgãos.
- **DO-RF-03:** permitir corrigir e confirmar a formulação do obstáculo.
  - **Aceite:** o registro confirmado preserva o relato original, o texto revisado, autoria e data.
- **DO-RF-04:** permitir registrar divergência com o dado do Censo.
  - **Aceite:** a divergência descreve a realidade informada pela escola, fica rotulada como divergência e não altera dado, score nem faixa.
- **DO-RF-05:** permitir marcar uma barreira como "sem relato nesta versão".
  - **Aceite:** a marcação é explícita do diretor e aparece como tal na declaração, nunca como barreira inexistente.
- **DO-RF-06:** emitir a Declaração somente quando todas as barreiras tiverem posição.
  - **Aceite:** o botão de emissão indica quantas barreiras faltam; a versão emitida fica imutável, com autoria e data, e visível ao secretário da rede.
- **DO-RF-07:** retificar uma declaração emitida por meio de nova versão.
  - **Aceite:** versões anteriores continuam consultáveis; um Plano de Ação baseado em versão anterior é sinalizado ao diretor e ao secretário.
- **DO-RF-08:** publicar uma versão emitida.
  - **Aceite:** antes da publicação, a checagem assistida aponta possíveis dados pessoais e riscos de identificação indireta; a publicação exige aprovação explícita do diretor; a página pública mostra a versão publicada com data e número da versão.
- **DO-RF-09:** mostrar o estado da Declaração (rascunho, emitida, publicada) no dashboard do diretor.

## Estados

- **Por barreira:** sem posição, rascunho (relato em andamento), obstáculo relatado, divergência com o Censo, sem relato nesta versão.
- **Da Declaração:** rascunho, emitida (vN), publicada (vN). Uma versão emitida pode ou não estar publicada; a versão publicada é sempre uma versão emitida.

## Decisões pendentes

**Resolvida em 2026-10-23:** salvar parcial e retomar — o rascunho (posições e conversa em andamento) fica gravado por escola e é retomado de onde parou. Continuam pendentes: bloqueio de retificação enquanto um plano está em análise; retirada da publicação e moderação; resposta da secretaria a uma declaração; justificativa para "sem relato nesta versão"; encaminhamento das divergências ao Educacenso; exportação e valor jurídico do documento.

## Implementação (2026-10-23)

- Backend: `backend/app/features/declaracao/` (posições, emissão com versões congeladas, conversa com a IA); telas em `frontend/src/features/gestao-ativa/components/DeclaracaoObstaculos.tsx` e `ModaisDeclaracao.tsx`, rota `/gestao/diretor/declaracao` (com `?eixo=` para registrar um eixo só).
- Todo texto do diretor (relato, texto formal, resumo, divergência) é gravado mascarado pelo Guardião LGPD; dado de saúde, documento ou situação sensível bloqueia e pede reescrita.
- A conversa usa o contexto do AD-08 com foco na barreira; a IA propõe texto formal e resumo, e o diretor revisa e confirma. Sem IA disponível, o diretor escreve o texto direto.
- Ao confirmar, a conversa é apagada e as falas do diretor ficam como relato original da posição.
- Publicação (DO-RF-08) implementada em 2026-10-24: prévia com frases fixas, checagem local de dados pessoais (dado sensível impede; demais achados são mascarados e avisados), aprovação explícita, só a versão emitida mais recente, texto público congelado; aparece no modal público da escola (Fase 1) com versão e data. O secretário vê as versões emitidas da rede na aba "Declarações das escolas". Retirada implementada (diretor e administração, com motivo em lista fechada e auditoria; a versão emitida continua guardada). Revisão do AgLGPD da publicação aplicada: escola com menos de 5 matrículas da educação especial não publica texto sobre um estudante no singular; cargo de pessoa única e linguagem que culpa viram ponto de atenção; rota pública com cache curto, no-store, noindex e limite por IP. Pendentes: canal público para pedir revisão de uma declaração publicada e se a contagem exata de alunos da área pública da Fase 1 também passa a "menos de 5" (pendência 13 da arquitetura).
- Revisão do AgLGPD (2026-10-23) aplicada: a versão emitida grava o dado do Censo sem contagem de célula pequena; na emissão, cada texto e o conjunto passam de novo pelas regras do Guardião, e um achado novo recusa a emissão indicando a barreira; a fala da IA também é mascarada; conversas paradas há mais de 30 dias são apagadas.
- Decisões pendentes da revisão: (a) por quanto tempo guardar o relato original de cada posição depois da emissão (o requisito DO-RF-03 pede preservá-lo); (b) se um novo diretor da mesma escola deve ver o relato original e as conversas do anterior; (c) prazo de guarda das versões emitidas, que são registro oficial (pendência 4 da arquitetura).
