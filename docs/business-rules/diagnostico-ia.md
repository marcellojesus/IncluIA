# Regras de Negócio — Diagnóstico de IA por Eixo (Módulo 6)

> Toda esta feature exige autenticação — ver RN-06 de `docs/business-rules/login.md` (única funcionalidade do produto com custo real de IA; demais módulos são públicos). A barreira é aplicada no backend, não só na UI.

## RN-01 — Ordem de fallback entre modelos é fixa e hierárquica

1º Gemini 2.0 Flash → 2º Groq LLaMA 3.3 70B → 3º Mistral Small → 4º dados brutos sem narrativa (sem IA).

**Por quê**: `IncluIA_IA_Estrategia_v1` define essa ordem com base em free tier disponível (Gemini: 1.500 req/dia, 1M tokens contexto) e velocidade. Não pular etapas (ex.: ir direto de Gemini para dados brutos sem tentar Groq/Mistral) — cada etapa reduz o custo antes de desistir da narrativa gerada por IA.

**Como aplicar**: implementar como módulo isolado (`ai_client.py` na documentação original) — trocar a ordem ou adicionar um modelo deve ser uma mudança pequena e localizada, não espalhada pelo código de UI.

## RN-02 — Falha de IA nunca deve ser visível como erro para o gestor

O último nível de fallback é sempre "mostrar os dados brutos sem análise de IA" — nunca uma tela de erro, spinner infinito ou mensagem técnica. Esse é um requisito de produto, não apenas técnico: o gestor deve sempre conseguir ver alguma informação útil na aba de Diagnóstico IA, mesmo que os 3 provedores de IA estejam fora do ar.

## RN-03 — O veredito do semáforo nunca vem da IA; só a narrativa vem

A IA generativa nunca decide se um eixo é ✅/⚠️/❌ — isso é calculado deterministicamente (ver [[indicadores-municipio]] RN-01). A IA recebe o veredito já calculado como parte do contexto e apenas o explica, recomenda ações e cita a base legal.

**Por quê**: impede que uma alucinação do modelo mude o "resultado oficial" de conformidade exibido ao gestor — a IA é uma camada de explicação sobre uma verdade determinística, não a fonte da verdade.

## RN-04 — Nenhum dado pessoal trafega para a IA

Apenas dados agregados e públicos do Censo (contagens, percentuais, médias) podem compor o prompt enviado a Gemini/Groq/Mistral. Nomes de alunos, professores ou qualquer identificador individual nunca fazem parte do contexto.

**Por quê**: privacidade por design (`IncluIA_IA_Estrategia_v1`) — os dados do Censo usados são agregações por escola/município, não microdados de indivíduos, então essa regra é naturalmente satisfeita se a fonte de dados do prompt for sempre o resultado do Score IncluIA (ver [[score-incluia]]), nunca uma tabela de matrícula bruta.

## RN-05 — Cache de 24h com chave dependente da versão do Censo

Chave de cache: `SHA256(codigoIbge + eixo + versaoCenso)`. A inclusão da versão do Censo na chave garante invalidação automática de todo o cache quando uma nova edição do Censo é processada — não é necessário limpar o cache manualmente a cada atualização anual de dados.

## RN-06 — Artigo específico só quando validado contra o texto oficial (revisada)

**Redação original** (mantida aqui por histórico): "todo alerta legal deve citar o artigo exato do Decreto, nunca de forma genérica."

**Histórico de correção importante**: por um bom tempo, o produto citou "Art. 7º do Decreto 12.773/2025" como base para LIBRAS/Braille (Eixo III) — uma citação fabricada, nunca conferida contra o texto oficial. Ao buscar os textos reais (ver `docs/legislacao.md`), descobriu-se que: (1) quem efetivamente institui a PNEEI é o **Decreto 12.686/2025**, não o 12.773/2025 (que só tem 2 artigos de alteração pontual); e (2) o Art. 7º real não tem nenhuma relação com LIBRAS/Braille. A citação foi corrigida.

**Decisão de implementação vigente**: com os 3 textos legais completos agora salvos em `base/legislacao/` e mapeados em `docs/legislacao.md`, os 4 eixos têm base legal validada (não fabricada) em `_ARTIGO_VALIDADO_POR_EIXO` (`backend/app/features/diagnostico_ia/service.py`):

- Nos demais casos (base legal ainda não mapeada para um novo critério), o alerta legal referencia a "PNEEI (Decreto 12.686/2025)" de forma geral — nunca um artigo não validado.
- Isso **não dispensa** o aviso permanente de "⚠️ Em validação jurídica" já exigido em `docs/business-rules/indicadores-municipio.md` RN-02 — mesmo com citações corretas, o mapeamento score↔lei continua sendo uma aproximação metodológica do produto, não uma certificação jurídica formal.

**Como aplicar**: ao validar uma nova base legal para outro critério, primeiro adicionar a linha em `docs/legislacao.md` (com o trecho literal do artigo), só então em `_ARTIGO_VALIDADO_POR_EIXO` — o prompt passa a usá-la automaticamente, sem mudança de lógica. O mesmo corpus e mapeamento fundamentam o chat de ajuste de recomendações (ver RN-09).

## RN-09 — Chat por eixo permite Q&A e ajuste de recomendação, mas nunca muda o veredito

Cada eixo do diagnóstico tem um chat próprio (histórico persistido em `chat_diagnostico_mensagens`) onde o gestor pode tirar dúvidas ou pedir o ajuste de uma recomendação. A IA pode responder com uma `recomendacoesAtualizadas`, que passa a ser exibida no lugar da recomendação original (persistida em `chat_diagnostico_recomendacoes_ajustadas`) — mas **nunca** pode alterar o status ✅/⚠️/❌ nem o score do eixo (RN-03 continua valendo integralmente dentro do chat). O chat só pode citar a base legal listada em `docs/legislacao.md` para aquele eixo — nunca um artigo fora dela.

**Por quê**: dar ao secretário um jeito de refinar a recomendação (custo/prazo/ação) para a realidade do seu município, sem abrir uma brecha para a IA "recalcular" o diagnóstico oficial por conversa — o mesmo princípio de RN-03, aplicado a uma superfície interativa nova.

## RN-10 — Botão "Reprocessar" gera uma versão final do diagnóstico considerando toda a conversa

Além do ajuste automático por mensagem (RN-09, que só troca a lista de recomendações quando a IA julga pertinente), cada chat por eixo tem um botão explícito — "🔄 Reprocessar diagnóstico com esta conversa" — que envia todo o histórico da conversa para a IA e pede uma **versão final e completa** do diagnóstico daquele eixo (situação, análise, alerta legal e recomendações), não só a recomendação. Essa versão passa a ser a nova versão oficial cacheada do eixo (`recomendacoes` e `analise` etc.), com o mesmo TTL de 24h de qualquer diagnóstico gerado, e com o campo `reprocessadoEm` marcado para rastreabilidade — qualquer ajuste pontual anterior (RN-09) é descartado, porque a versão reprocessada já o incorpora.

**Por quê**: o ajuste automático por mensagem é conveniente para pedidos pontuais e explícitos ("mude o prazo para X"), mas depende da IA decidir, a cada mensagem, se deve ou não propor uma atualização — o que pode deixar o gestor sem noção clara de quando a conversa "valeu" e quando não valeu. O botão dá uma ação explícita e previsível: o gestor conversa livremente, e só quando pede o reprocessamento é que o diagnóstico muda de fato — sem depender do juízo silencioso da IA a cada mensagem trocada.

**Como aplicar**: como no restante do produto, RN-03 continua valendo integralmente — o reprocessamento nunca muda o status ✅/⚠️/❌ nem o score do eixo, só o texto explicativo e as recomendações.

## RN-07 — Toda recomendação deve ter estimativa de custo e prazo, nunca só a ação

Uma recomendação sem custo estimado e prazo é considerada incompleta pelo padrão do produto (ver exemplos em `interface.md` §7) — reforça o objetivo de decisão de alocação de recursos, não apenas diagnóstico.

## RN-08 — Geração paralela dos 4 eixos, cache independente por eixo

Os 4 eixos são solicitados em paralelo (`Promise.all` ou equivalente), e cada um é cacheado individualmente. Isso permite que o botão "Regenerar" (ou a expiração natural do cache) afete apenas o eixo necessário, sem forçar a regeneração cara dos 4 eixos quando só 1 mudou.
