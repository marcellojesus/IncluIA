# Regras de Negócio — Retenção e eliminação de dados (AD-07)

**Decisão do responsável:** 2026-11-03 · **Arquitetura:** AD-03 e AD-07 em [arquitetura.md](../arquitetura.md) · **Política:** PBD-101 a 104 em [politica-privacidade-pbd.md](../politica-privacidade-pbd.md)

Os prazos abaixo foram escolhidos pelo responsável do produto e **ainda precisam da validação do jurídico e do encarregado de dados** (PBD-120). Uma só rotina (`app/features/retencao`) aplica todos eles na subida do servidor e pelo comando `python -m app.features.acesso.cli limpar`. Cada execução devolve só a quantidade atingida por regra, sem conteúdo. Cada regra grava em separado: a que falhar fica no log, só com o tipo do erro, e não desfaz as outras nem impede a subida. A rotina recusa data futura.

## Resumo

| Dado | Prazo | O que acontece |
|---|---|---|
| Código de acesso | 24 horas | apagado (de antes) |
| Pedido de acesso nunca confirmado | 72 horas | apagado com a conta (de antes) |
| Conversa da Declaração parada | 30 dias | apagada (RN-RET-01) |
| Sugestão da IA descartada, substituída, esquecida, ou aceita e depois editada ou removida | 30 dias | perde o conteúdo; fica a linha (RN-RET-01) |
| Pedido de acesso recusado | 30 dias | apagado (RN-RET-02) |
| Auditoria | 5 anos | não muda; apagada depois do prazo (RN-RET-03) |
| Conta que nunca teve vínculo aprovado | 30 dias depois da recusa | pseudonimizada: nome e e-mail apagados (RN-RET-04) |
| Conta revogada | 6 meses depois do fim do vínculo | pseudonimizada: nome e e-mail apagados (RN-RET-04) |
| Texto de versão retirada por dado pessoal ou pedido de titular | 30 dias depois da retirada | texto livre apagado, com as cópias da escola; a estrutura fica (RN-RET-05) |
| Versões emitidas, enviadas, decididas e confirmadas | enquanto durar o programa | guardadas, com revisão anual (RN-RET-06) |
| Síntese do Analítico | 1 ano, ou antes | apagada (RN-RET-07) |

## RN-RET-01 — Rascunho que não virou documento sai em 30 dias

- A conversa da Declaração sem mensagem nova há 30 dias é apagada. A posição confirmada guarda só o relato original.
- A sugestão da IA (Plano de Ação Escolar e Plano Municipal) descartada, substituída por um ajuste ou deixada pendente há 30 dias perde o conteúdo. A linha fica, para mostrar que houve sugestão. A pendente passa a "expirada".
- A sugestão aceita fica enquanto a ação dela existe sem edição, porque aí o texto é o mesmo da ação. Se a ação foi editada ou removida, a sugestão perde o conteúdo em 30 dias.

## RN-RET-02 — Pedido recusado sai em 30 dias

O pedido de vínculo recusado guarda a justificativa da secretaria e o método de verificação. Ele é apagado 30 dias depois da recusa. A auditoria da recusa continua, sem o texto.

## RN-RET-03 — Auditoria por 5 anos, sem alteração

- O evento de auditoria (quem, o quê, quando, sobre qual registro, sem conteúdo) fica 5 anos, o prazo que a administração pública tem para apurar atos (Lei 9.873/1999).
- O banco impede alterar qualquer evento e impede apagar evento com menos de 5 anos, também para quem acessa o banco por fora da aplicação com o papel da aplicação (gatilhos da migração `7d1e0c5a9b42`, no SQLite e no PostgreSQL; no PostgreSQL também o `TRUNCATE`).
- O evento entra sempre com a data do servidor: não dá para gravar evento com data antiga, nem para forjar histórico, nem para fabricar evento já vencido.
- **Limites:** quem é dono das tabelas pode remover os gatilhos (no SQLite, quem tem o arquivo). No PostgreSQL de produção, a aplicação deve usar um papel que não seja dono da tabela e sem permissão de `UPDATE`, `DELETE` e `TRUNCATE` nela, e a exclusão aos 5 anos deve rodar com um papel separado (a definir com o AD-01).
- Depois de 5 anos, a rotina apaga o evento.
- Mudança futura de esquema da tabela `auditoria` no SQLite precisa recriar os gatilhos, porque o SQLite recria a tabela ao alterá-la.

## RN-RET-04 — Conta encerrada é pseudonimizada

- Conta de diretor ou secretário sem vínculo vigente (pendente, aprovado ou suspenso) é pseudonimizada:
  - 6 meses depois do fim do último vínculo, quando ele foi revogado;
  - 30 dias depois da recusa, quando a conta nunca teve vínculo aprovado.
- Pseudonimizar é trocar o nome por "Conta encerrada", trocar o e-mail por um endereço inválido único, apagar justificativa e método de verificação dos vínculos e apagar os códigos de acesso do e-mail antigo. A auditoria registra a pseudonimização.
- **Não é anonimização** (LGPD, art. 12): o identificador da conta continua ligado aos vínculos (escola, período), às versões e à auditoria, e quem foi diretor de uma escola num período costuma ser público. A ligação fica para a prestação de contas e a auditoria da gestão; a base legal dessa guarda e a necessidade de manter a ligação com a escola vão ao jurídico (revisão do AgLGPD, M2).
- Versões, decisões e auditoria guardam só o identificador da conta e passam a mostrar "Conta encerrada".
- Quem voltar com o mesmo e-mail faz um pedido novo, que passa de novo pela aprovação da secretaria.
- Suspensão não conta como fim: a conta suspensa fica como está.
- A conta de administrador não é pseudonimizada pela rotina: é provisionada e encerrada à mão.

## RN-RET-05 — Texto de versão retirada por proteção de dados sai em 30 dias

- Declaração ou versão de plano retirada por **dado pessoal** ou **pedido de titular** tem o texto livre apagado 30 dias depois da retirada. Os 30 dias permitem à escola e à secretaria conferir e corrigir antes.
- Na Declaração saem relato, resumo e texto público. Ficam barreira, posição, dado do Censo e pontos.
- No plano saem ação, relação com o obstáculo, responsável, prazo, custo, premissas, texto público, comentário e apontamentos da secretaria. Ficam barreira, horizonte, origem e fontes.
- O texto apagado é trocado por "[Texto apagado: versão retirada por proteção de dados]", e a versão ganha a data do apagamento.
- As outras cópias da mesma escola saem junto (revisão do AgLGPD, A2):
  - outras versões da Declaração com o mesmo relato (a comparação ignora pontuação, acento e caixa);
  - todas as versões do plano feitas sobre a Declaração retirada, publicadas ou não, e as versões irmãs de um plano retirado (ajustes pedidos pela secretaria);
  - o rascunho do plano feito sobre a Declaração retirada, as ações em edição com o mesmo texto e as sugestões da IA dessa base;
  - o relato original da conversa nas barreiras atingidas, mesmo que o diretor já tenha corrigido o texto; o texto confirmado só sai se ainda for o retirado;
  - a conversa dessas barreiras.
- Desde a retirada, o plano feito sobre a Declaração retirada não entra mais na base da IA do plano municipal.
- A retirada por outro motivo (decisão da escola) não apaga o texto.
- **O que não volta:** PDFs baixados antes da retirada e cópias de backup (PBD-100 e 104). A retirada impede novos downloads.
- **Pendentes:**
  - a retirada só existe para versão publicada. Pedido de titular sobre versão nunca publicada precisa de uma "retirada para apagamento" pela administração (LGPD, art. 18);
  - versões e narrativas do plano municipal já confirmadas que usaram ações desse plano não são alteradas; precisam de revisão humana (PBD-103).
- Esta é a única exceção à imutabilidade das versões (AD-03), e a auditoria registra cada apagamento.

## RN-RET-06 — Versões ficam enquanto durar o programa

- Declarações, planos escolares, decisões da secretaria, planos municipais e narrativas executivas são o histórico da gestão e ficam enquanto o programa existir.
- O responsável revisa os prazos uma vez por ano, e o fim do programa exige um plano de eliminação ou de transferência para o arquivo da secretaria.

## RN-RET-07 — Síntese do Analítico sai em 1 ano ou antes

A síntese é apagada no que vier primeiro:
- 1 ano depois de gerada;
- quando sai uma edição nova do Censo para o município (a síntese guarda a edição usada desde 2026-11-03; as anteriores seguem só o prazo de 1 ano);
- quando usou relato de Declaração depois retirada por dado pessoal ou pedido de titular.

Continuam guardadas no máximo as 5 últimas por município (regra aplicada ao gerar a síntese). Município fora do artefato do Censo não perde a síntese pela regra da edição, só pelo prazo.

## RN-RET-08 — Quando a rotina roda

A rotina roda na subida do servidor e pelo comando `limpar`. No deploy, ela precisa rodar ao menos uma vez por dia, com um agendamento (cron) se o servidor ficar dias sem reiniciar. Cópias e backups seguem os mesmos prazos (PBD-100 e 104), a definir com o provedor de banco (AD-01).
