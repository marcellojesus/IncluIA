# Requisitos — Diretor | Declaração de Obstáculos

**Status:** Proposta para validação · atualizada em 2026-10-18 com as decisões da validação do protótipo  
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

Salvar parcial/retomar; bloqueio de retificação enquanto um plano está em análise; retirada da publicação e moderação; resposta da secretaria a uma declaração; justificativa para "sem relato nesta versão"; encaminhamento das divergências ao Educacenso; exportação e valor jurídico do documento.
