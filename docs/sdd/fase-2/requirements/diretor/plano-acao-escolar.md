# Requisitos — Diretor | Plano de Ação Escolar

**Status:** Implementado · notas de implementação até 2026-10-26  
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

## Notas de implementação (2026-10-25, lado do diretor)

- **Código:**
  - backend em `backend/app/features/plano/` (rotas sob `/gestao/diretor/plano`, migração `8caf74ef5fcd`);
  - frontend em `features/gestao-ativa/components/PlanoAcao.tsx` (rota `/gestao/diretor/plano`);
  - testes em `backend/tests/test_plano.py`.
- **PAE-RF-00:**
  - o rascunho guarda a versão da Declaração usada como base;
  - quando sai uma versão mais nova, o plano mostra o aviso de desatualizado e o botão "Usar a Declaração vN", que mantém as ações e descarta as sugestões antigas;
  - o dashboard do diretor mostra o mesmo aviso.
- **PAE-RF-01 e 03:**
  - as sugestões são geradas por barreira, com o contexto AD-08 da escola do vínculo e a base normativa;
  - cada sugestão traz relação, responsável (cargo ou órgão), prazo, LOA ou PPA, custo "a estimar" quando não há base, premissas, fontes, incertezas e lacunas;
  - se a IA citar uma fonte fora do contexto, a resposta é reprovada e o pedido passa ao próximo provedor;
  - barreira "sem relato" não recebe sugestão automática (409) e aparece como lacuna.
- **PAE-RF-02:**
  - "Pedir outra proposta" aceita uma orientação opcional;
  - "Ajustar com a IA" (2026-10-25): o diretor diz o que mudar numa sugestão (há pedidos rápidos, como "Reduzir o prazo" ou "Ação sem custo para a escola"). A IA recebe a proposta anterior (de novo pelo Guardião), o pedido (pelo Guardião, com bloqueio de dado sensível) e o mesmo contexto da barreira, e devolve uma única sugestão com o selo "Ajustada a seu pedido". A sugestão anterior fica como `substituida`;
  - "Editar e incluir": o formulário abre preenchido com a sugestão e a ação entra já marcada como editada, mantendo as fontes;
  - só "Incluir no plano" leva a ação ao rascunho;
  - "Descartar" apaga a sugestão.
- **PAE-RF-05:**
  - cada ação registra a origem (`ia` ou `diretor`) e a marca `editada`, que aparecem como selo na tela e na versão enviada;
  - o histórico guarda as versões enviadas.
- **PAE-RF-06:**
  - "Revisar e enviar à secretaria" abre uma prévia (2026-10-26). Ela traz:
    - um sumário executivo calculado do rascunho, sem IA: ações, barreiras com relato cobertas, LOA/PPA, origem, custos;
    - os pontos para revisar: barreira com relato sem ação, ação sem responsável ou prazo, marcador do Guardião no texto;
    - o plano agrupado por barreira, como a secretaria vai recebê-lo;
  - o envio exige a caixa de confirmação;
  - a versão fica congelada em `versoes_plano` e `itens_versao_plano`, com estado `aguardando_analise`;
  - enquanto houver versão em análise, não sai uma nova.
- **PAE-RF-07:**
  - a tela já mostra o estado e o comentário da última versão;
  - a decisão do secretário (aceitar, pedir ajustes, reprovar) é a próxima etapa.
- **LGPD (revisão do AgLGPD em 2026-10-25, sem achado de risco alto):**
  - o texto livre do diretor (orientação e campos da ação) passa pelo Guardião antes da IA e antes de ser gravado; dado sensível de estudante identificável bloqueia (422);
  - a resposta da IA é protegida antes de ser gravada;
  - `responsavel` aceita só cargo ou órgão: se o Guardião encontrar um nome, a ação é recusada com 422; se a IA puser um nome, o campo fica vazio;
  - quando algum trecho é mascarado ou descartado, a resposta traz `avisoGuardiao` e a tela mostra o aviso (AD-05: mascarar e avisar);
  - a tela avisa que a orientação vai para uma IA externa e que a ação vai à secretaria como foi escrita;
  - o Guardião passou a aceitar como termos do domínio os verbos no infinitivo que abrem as ações ("Reunir a equipe..."). É uma lista fechada; prenomes como Valdir e Altair continuam mascarados (teste de regressão).
- **Ainda não implementado:**
  - conversa livre sobre cada sugestão (hoje é "outra proposta com orientação");
  - documentos formais e orçamento como contexto (dependem dos documentos do corpus).

## Decisões pendentes

Fontes e permissões dos documentos de contexto; prazo/horizonte e taxonomia orçamentária; política para ações descartadas; exportação e estatuto dos documentos formais.

Da revisão do AgLGPD (2026-10-25):
- **Retenção:**
  - as sugestões descartadas guardam o conteúdo completo, e as versões enviadas são imutáveis (RN-PAE-04);
  - falta definir em quantos dias o conteúdo das sugestões descartadas é apagado;
  - falta um procedimento administrativo auditado para retificar um item congelado, caso o Guardião tenha deixado passar algum dado;
  - falta a anonimização de `autor_id` e `submetida_por` quando a conta for encerrada (AD-07).
- **Auditoria:**
  - hoje só o envio gera evento;
  - falta registrar pedir sugestão, aceitar, editar e remover, guardando só identificador e tipo;
  - falta registrar as ocorrências do Guardião por funcionalidade e escola (tipo e quantidade), um ponto que vale para todas as funcionalidades.
- **Tela do secretário (próxima etapa):**
  - filtrar por `co_municipio` do vínculo no servidor;
  - mostrar só as versões enviadas, sem rascunhos nem sugestões;
  - passar o comentário do secretário pelo Guardião;
  - não expor `submetida_por`;
  - nada do plano vai para a área pública, exceto a versão aceita que o diretor publicar (decisão de 2026-10-26; ver "Publicação do plano aceito").

## Publicação do plano aceito (decisões do responsável em 2026-10-26)

- **Quem publica:** o diretor, depois que a secretaria aceitou a versão, com prévia e aprovação explícita (mesmo modelo da Declaração). Só a versão aceita mais recente pode ser publicada.
- **Com a Declaração:** o plano só aparece na página pública junto com a Declaração publicada; sem ela, não pode ser publicado e não é exibido.
- **O que o público vê:** barreira, ação, relação com o obstáculo, responsável, prazo, horizonte, custo estimado e fontes (citação legível); versão e datas de aceite e publicação; o aviso de que aceite não é orçamento nem execução. Premissas, autoria, origem (IA ou escola), sugestões, comentários da secretaria e rascunho não vão ao público.
- **Checagens na prévia (Guardião LGPD local, sem IA):**
  - dado sensível bloqueia;
  - em escola com poucas matrículas da educação especial (célula pequena, menos de 5), menção a estudante individual bloqueia, e um profissional de atendimento (AEE, intérprete, cuidador, monitor) como responsável também bloqueia; fora disso, esse responsável gera só aviso;
  - culpa e trecho mascarado geram aviso;
  - o conjunto dos campos públicos também é conferido.
- **Retirada:**
  - o diretor retira com motivo; a administração retira a pedido de titular (`/gestao/admin/planos/...`);
  - versão retirada não volta ao ar: o texto corrigido sai como nova versão, enviada e aceita de novo;
  - retirada por dado pessoal ou pedido de titular apaga o texto público congelado;
  - se a Declaração for retirada por esses motivos, o plano publicado sai junto.
- **Código:** `backend/app/features/plano/publicacao.py` (migração `e9cb2325e95d`), anexado à rota pública da Declaração; telas `PublicarPlano.tsx` e `DeclaracaoPublicaEscola.tsx`.
- **Pendente (AgLGPD, baixa):**
  - o cache da rota pública é por processo; com mais de um worker, a retirada leva até 60 s para valer em todos;
  - a administração ainda não tem uma tela para ver o plano publicado antes de retirar.
