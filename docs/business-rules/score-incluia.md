# Regras de Negócio — Score Escola Sem Barreiras (Engine de Cálculo)

## RN-01 — Fórmula oficial: 11 variáveis, 3 dimensões, pesos por Eixo do Decreto

Fonte de verdade: [`metodologia_score.md`](../../metodologia_score.md) (transcrição oficial de `IncluIA_Metodologia_Score_v1`). Score da escola (0 a 1, depois × 10 para escala 0–10):

```
Score_escola = 0,30×V_AEE + 0,15×V_taxa_CC + 0,15×V_libras + 0,10×V_braille
             + 0,08×V_rampa + 0,07×V_banheiro_pne + 0,06×V_corrimao
             + 0,04×V_piso_tatil + 0,02×V_sinal_visual + 0,02×V_sinal_sonoro + 0,01×V_elevador

Score_IncluIA_escola = Score_escola × 10
```

Reagrupando essas mesmas variáveis pelos **4 Eixos do Decreto** (como exibido na UI, ver `interface.md` §5.2), os pesos por eixo são:

| Eixo do Decreto | Peso | Variáveis |
|---|---|---|
| Eixo I — AEE | 30% | V_AEE |
| Eixo II — Acessibilidade Física | 30% | rampa(8%) + banheiro_pne(7%) + corrimao(6%) + piso_tatil(4%) + sinal_visual(2%) + sinal_sonoro(2%) + elevador(1%) |
| Eixo III — Profissionais Especializados | 25% | libras(15%) + braille(10%) |
| Eixo IV — Inclusão em Classe Comum | 15% | taxa_CC |

**Nota de reconciliação (resolvida)**: existiam 3 redações diferentes dos pesos nos documentos de planejamento — `IncluIA_Metodologia_Score_v1` (3 dimensões: AEE+CC=45%, Profissionais=25%, Acessibilidade=30%), o texto de `IncluIA_MVP5` (Acessibilidade **35%**, Profissionais **20%**) e o protótipo funcional (Acessibilidade **30%**, Profissionais **25%**). `metodologia_score.md` §8 ("Alinhamento com a PNEEI (Decreto 12.686/2025)") **confirma oficialmente** que os pesos por eixo são AEE 30% / Acessibilidade 30% / Profissionais 25% / Inclusão CC 15% — idênticos aos do protótipo e à Metodologia reagrupada por eixo. O texto do MVP5 (35%/20%) está errado e deve ser ignorado.

**Decisão adotada**: usar os pesos **30% / 30% / 25% / 15%** (Eixos I/II/III/IV), por serem os pesos oficiais confirmados em `metodologia_score.md` §8.

## RN-02 — Regras especiais de normalização das variáveis

- **`TP_AEE`** (valores confirmados no dicionário oficial do Censo 2025 — ver nota de correção em `metodologia_score.md`): valor `0` (não oferece) → `V_AEE = 0,0`. Valores `1` (sim, não exclusivamente) e `2` (sim, exclusivamente) → `V_AEE = 1,0` em ambos os casos — o campo distingue o *modelo* de oferta de AEE, não sua existência, então não há razão para pontuação parcial.
- **Piso tátil**: a variável de acessibilidade física correspondente é `IN_ACESSIBILIDADE_PISOS_TATEIS` (peso 4%) — não confundir com `IN_ACESSIBILIDADE_SINAL_TATIL` ("Sinalização tátil (piso/paredes)"), um campo diferente que não faz parte da fórmula do score.
- **Escolas `IN_ESPECIAL_EXCLUSIVA = 1`**: recebem `V_taxa_CC = 0` por definição (não têm classe comum), mas continuam entrando no cálculo do score geral normalmente — não são excluídas nem tratadas como exceção no cálculo. (Ver `docs/business-rules/escolas.md` RN-05 para o tratamento na **apresentação** desse caso, que é diferente do tratamento no **cálculo**.)
- **Escolas sem nenhum aluno ESP (`QT_MAT_ESP = 0`)**: recebem o valor médio do município para `V_taxa_CC` (não zero, não nulo) — evita penalizar artificialmente escolas sem alunos ESP matriculados, já que a variável não é observável para elas.

## RN-03 — Agregação é sempre ponderada por alunos ESP, nunca média simples entre escolas/municípios

`Score_município = Σ(Score_escola_i × QT_MAT_ESP_i) / Σ QT_MAT_ESP_i`. A mesma lógica se aplica de município para estado, ponderando pelo total de alunos ESP do município.

**Exceção**: se todas as escolas do município tiverem `QT_MAT_ESP = 0` (nenhum aluno ESP registrado em nenhuma escola), usar média simples entre as escolas para evitar divisão por zero.

**Por quê**: pondera o score pelo número de alunos efetivamente impactados — um município com uma escola excelente e 1 aluno ESP não deve superar um município com desempenho mediano em 50 escolas com milhares de alunos ESP.

## RN-04 — Faixas de classificação (idênticas em todos os documentos — sem divergência)

| Faixa | Status | Cor |
|---|---|---|
| 0,0 – 2,9 | Crítico | #E52207 |
| 3,0 – 4,9 | Insuficiente | #E05C00 |
| 5,0 – 6,9 | Em desenvolvimento | #E6B800 |
| 7,0 – 8,4 | Adequado | #168821 |
| 8,5 – 10,0 | Referência | #1351B4 |

Essas faixas se aplicam da mesma forma a escola, município e estado — ver também `docs/business-rules/escolas.md` RN-02 sobre a inconsistência observada no protótipo quanto ao uso dessas 5 faixas no nível de escola.

## RN-05 — Limitações metodológicas conhecidas (devem ser comunicadas ao usuário, não escondidas)

- O score mede **disponibilidade** de recursos/suporte, não a **qualidade** do seu uso.
- A taxa de inclusão em classe comum mede proporção, não qualidade pedagógica da inclusão.
- O peso baixo do elevador (1%) mitiga, mas não elimina, a penalização de municípios sem prédios de múltiplos andares.
- Só é comparável **dentro da mesma edição do Censo** (ver [[indicadores-municipio]] RN-03).
- Municípios/escolas com poucas unidades ESP têm score estatisticamente volátil — pequenas mudanças no numerador geram grandes saltos percentuais.

**Como aplicar**: essas limitações devem constar em algum texto de ajuda/tooltip acessível ao gestor (ex.: no painel de metodologia do score), não apenas em documentação interna.

## RN-06 — Reprocessamento do score é versionado por edição do Censo

Cada cálculo de score deve estar associado à versão/ano do Censo usada (ex.: "Censo 2025"). Isso é a mesma versão usada na chave de cache do diagnóstico de IA (ver [[diagnostico-ia]] RN-05) — garantindo que todo o produto (mapa, indicadores, diagnóstico) sempre reflita a mesma edição de dados de forma consistente, sem misturar anos diferentes entre módulos.
