# Requisitos — Diagnóstico de IA por Eixo (Módulo 6)

Fonte de interface: `interface.md` §7. Fonte de contexto: `context.md` (Módulo 6, IA_Estrategia).

## Objetivo

Transformar os indicadores do município em um plano de ação estruturado por eixo do Decreto, gerado por IA generativa, com linguagem acessível, alertas legais e recomendações com estimativa de custo/prazo.

## Atores

Secretário Municipal e Secretário Estadual (ao visualizar qualquer município da sua UF).

## Pré-condições

- Indicadores do município já calculados (depende de [[score-incluia]] e [[indicadores-municipio]]).
- Ao menos um provedor de IA (Gemini, Groq ou Mistral) configurado, ou modo de fallback para dados brutos ativo.

## Requisitos Funcionais

- **RF-01**: Para cada um dos 4 eixos da PNEEI, gerar e exibir: análise em linguagem natural, alerta legal (quando houver risco de descumprimento, citando a base legal validada em `docs/legislacao.md`), recomendações priorizadas (com custo estimado e prazo) e benchmarking com município de perfil similar.
- **RF-10**: Cada eixo tem um chat próprio (histórico persistido) onde o gestor pode tirar dúvidas sobre o diagnóstico e pedir o ajuste de uma recomendação — a IA pode propor uma recomendação revisada, que passa a ser exibida no lugar da original, mas nunca pode alterar o status/score do eixo (ver `docs/business-rules/diagnostico-ia.md` RN-09).
- **RF-02**: Exibir metadado de rastreabilidade: modelo de IA usado e há quanto tempo o diagnóstico foi gerado/atualizado.
- **RF-03**: Oferecer um botão "Regenerar" que força um novo diagnóstico, ignorando o cache vigente.
- **RF-04**: Implementar fallback automático entre provedores de IA (Gemini → Groq → Mistral → dados brutos sem narrativa) sem exibir erro ao usuário em nenhum estágio da cadeia.
- **RF-05**: Cachear cada diagnóstico por eixo por 24h, permitindo regeneração parcial (só o eixo expirado) em vez de sempre regenerar os 4 eixos juntos.
- **RF-06**: Gerar os 4 eixos em paralelo (não sequencialmente), para manter o tempo de resposta próximo ao do eixo mais lento, não à soma dos 4.
- **RF-07**: Nunca enviar dados pessoais identificáveis de aluno ou professor para as APIs de IA — apenas dados agregados públicos do Censo.
- **RF-08**: Exportação do diagnóstico em PDF é desejável, mas pode ser adiada para Fase 2 (`context.md` §7.2 já a lista como backlog) — se adiada, o botão correspondente deve refletir esse status (ver `docs/business-rules/escolas.md` RN-04 para o mesmo padrão aplicado a exportação).
- **RF-09**: O sistema deve registrar (log) prompts e respostas de IA sem dados pessoais, para fins de auditoria e ajuste de custo.

## Requisitos Não Funcionais

- **RNF-01**: Timeout por provedor de IA (sugestão: 8s, conforme `IncluIA_IA_Estrategia_v1`) antes de acionar o próximo fallback.
- **RNF-02**: Contexto enviado ao modelo de IA deve ser mantido enxuto (referência: <2.000 tokens por chamada de eixo) para controlar custo.
- **RNF-03**: Painel administrativo (fora do escopo desta tela, mas dependência futura) deve poder consultar: tokens consumidos, taxa de acerto de cache, distribuição de uso entre modelos.
- **RNF-04**: O custo mensal de IA deve ser monitorável e alertável ao atingir 80% do orçamento definido (requisito de governança, não necessariamente uma tela no MVP).

## Dados de entrada/saída

**Entrada**: `codigoIbge` do município, eixo (I–IV) — chamado individualmente ou em lote para os 4.
**Saída por eixo**: `{ situacao, analise, alertaLegal?, recomendacoes: [{ acao, custoEstimado, prazo, impactoAlunos, fundamentacao }], referenciaMunicipio, modeloUsado, geradoEm }`.

## Fluxo principal

1. Usuário abre a aba "Diagnóstico IA" de um município.
2. Sistema verifica cache (SQLite, chave = hash de código IBGE + eixo + versão do Censo) para cada um dos 4 eixos.
3. Eixos com cache válido (<24h) são exibidos imediatamente; eixos sem cache disparam geração em paralelo via IA.
4. Resultado é exibido eixo a eixo, na ordem I → II → III → IV.

## Fluxos alternativos

- **Todos os provedores de IA falham ou estão sem chave configurada**: exibir os dados brutos do eixo (mesmos dados já mostrados na aba Indicadores) sem análise narrativa, e sem exibir uma tela de erro — a aba nunca deve "quebrar" visualmente.
- **Usuário clica "Regenerar" repetidamente**: desabilitar o botão durante a geração em curso para evitar chamadas duplicadas e custo desnecessário.

## Critérios de aceite

- [ ] Diagnóstico de um município já visitado nas últimas 24h carrega do cache, sem nova chamada de IA.
- [ ] Queda proposital do provedor primário (Gemini) resulta em fallback para Groq sem erro visível ao usuário.
- [ ] Nenhum dado pessoal de aluno/professor aparece no payload enviado à API de IA (auditável via log).
- [ ] Todo alerta legal exibido cita a base legal validada em `docs/legislacao.md` (Decreto 12.686/2025 ou Lei 13.146/2015, conforme o eixo) — nunca um artigo não mapeado ali.
- [ ] O chat de cada eixo persiste o histórico entre recarregamentos de página e reflete uma recomendação ajustada quando o gestor pedir uma.
