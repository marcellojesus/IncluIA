# Requisitos — Diretor | Plano de Ação Escolar

**Status:** Proposta para validação · atualizada em 2026-10-18  
**PRD:** RF-12 a RF-17 e RF-41  
**Dependência:** Declaração de Obstáculos **emitida** (ver `declaracao-obstaculos.md`)

## Objetivo

Apoiar o diretor a transformar as posições da Declaração de Obstáculos emitida em ações pertinentes à sua escola, por meio de IA conversacional, e submeter uma versão do Plano de Ação à secretaria municipal.

## Fluxo

0. Sem Declaração emitida, o plano não pode ser iniciado; a tela orienta o diretor a concluir e emitir a declaração.
1. A IA carrega a versão emitida como contexto, cruza cada barreira com a posição registrada (obstáculo relatado ou divergência com o Censo) e sugere ação(ões), explicando a relação e as fontes usadas. Barreiras "sem relato nesta versão" aparecem como lacuna, sem proposta automática.
2. O contexto pode incluir normas, documentos formais, orçamento e histórico da escola, somente quando conectados e autorizados.
3. O diretor conversa com a IA para avaliar pertinência, pedir esclarecimento, corrigir contexto, solicitar alternativa, editar ou descartar cada sugestão.
4. O diretor seleciona as ações que compõem o plano, revisa responsáveis, prazos, horizonte LOA/PPA, custos, premissas e fontes.
5. Ao confirmar e submeter, uma versão congelada fica pendente de análise da secretaria.

## Requisitos funcionais

- **PAE-RF-00:** exigir Declaração de Obstáculos emitida para iniciar o plano e registrar a versão usada.
  - **Aceite:** o plano exibe "baseado na Declaração vN"; se uma versão mais nova for emitida, diretor e secretário veem o aviso de que o plano usa versão anterior.
- **PAE-RF-01:** gerar sugestões de ação ligadas explicitamente a uma barreira e à posição registrada na Declaração emitida.
  - **Aceite:** a proposta mostra a relação, o trecho da declaração usado, o contexto consultado, fontes/data e incertezas; não inventa documentos ou valores.
- **PAE-RF-02:** permitir diálogo sobre pertinência de cada sugestão.
  - **Aceite:** o diretor pode aceitar, editar, solicitar outra proposta ou descartar; somente sua seleção explícita entra no plano.
- **PAE-RF-03:** utilizar apenas contexto escolar disponível e autorizado.
  - **Aceite:** documentos de outra escola ou rede não são expostos nem enviados ao modelo; ausência de contexto é informada.
- **PAE-RF-04:** editar ação, responsável, prazo, observações, classificação LOA/PPA e estimativas.
  - **Aceite:** dados estimados mostram premissas e fonte; não são apresentados como orçamento aprovado.
- **PAE-RF-05:** salvar rascunho e histórico de versões do plano.
  - **Aceite:** sugestões da IA, alterações do diretor e confirmações são identificáveis separadamente.
- **PAE-RF-06:** submeter uma versão à secretaria municipal.
  - **Aceite:** exige confirmação explícita; a versão enviada fica imutável e com estado `aguardando_analise`.
- **PAE-RF-07:** exibir ao diretor o estado e a decisão da secretaria.
  - **Aceite:** comentários de ajuste/reprovação apontam para a versão avaliada; nova submissão cria nova versão sem apagar a anterior.

## Decisões pendentes

Fontes e permissões dos documentos de contexto; prazo/horizonte e taxonomia orçamentária; política para ações descartadas; exportação e estatuto dos documentos formais.
