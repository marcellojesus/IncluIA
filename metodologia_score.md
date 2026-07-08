# Score Escola Sem Barreiras — Metodologia de Cálculo

> Índice de Governança da Inclusão Escolar
> Versão 1.0 · Julho 2026 · Baseado nos Microdados do Censo Escolar 2025 — INEP/MEC

Esta é a **fonte de verdade oficial** para a fórmula, pesos e regras de cálculo do Score Escola Sem Barreiras — prevalece sobre qualquer resumo de pesos citado em `context.md` ou `arquitetura.md`. As regras de negócio derivadas deste documento estão consolidadas em [docs/business-rules/score-incluia.md](docs/business-rules/score-incluia.md).

> **Correções aplicadas após validação com o dicionário oficial de dados do Censo 2025** (`base/microdados_censo_escolar_2025/Anexos/ANEXO I - Dicionário de Dados`), que têm precedência sobre o texto original do `IncluIA_Metodologia_Score_v1.docx`:
> 1. **Campo de "Piso tátil" corrigido**: o documento original citava `IN_ACESSIBILIDADE_SINAL_TATIL`, mas esse campo é na verdade "Sinalização tátil (piso/paredes)" — um recurso diferente (placas/sinalização, não o piso em si). O campo correto para piso tátil é **`IN_ACESSIBILIDADE_PISOS_TATEIS`** ("Pisos táteis"). Corrigido em todo este documento.
> 2. **Significado de `TP_AEE` corrigido**: o documento original descrevia os valores como `0=não oferta`, `1=oferta na própria escola`, `2=oferta em outro estabelecimento`. O dicionário oficial do Censo 2025 define: `0 = Não oferece`, `1 = Sim, não exclusivamente`, `2 = Sim, exclusivamente` — não há distinção de local, e sim se a escola oferta AEE junto com ensino regular (1) ou exclusivamente (2). **Decisão adotada**: como ambos os valores 1 e 2 indicam que a escola efetivamente oferta AEE, `V_AEE = 1,0` para `TP_AEE ∈ {1, 2}` e `V_AEE = 0,0` apenas para `TP_AEE = 0` — a pontuação parcial (0,5) do documento original foi descartada por não fazer mais sentido com a definição real do campo.

---

## 📋 Resumo Executivo

O Score Escola Sem Barreiras é um índice composto de 0 a 10 que mede o nível de governança da inclusão escolar de cada escola e município brasileiro. É calculado a partir de variáveis dos Microdados do Censo Escolar 2025 (INEP/MEC), agrupadas em três dimensões: **Suporte Educacional Especializado**, **Recursos Humanos Especializados** e **Acessibilidade Física**. O índice é calculado por escola e agregado para o nível municipal por média ponderada pelo número de alunos com deficiência matriculados. Aplicado a 214 mil escolas e 5.570 municípios, é o primeiro instrumento padronizado, auditável e replicável para monitoramento de políticas públicas de educação especial no Brasil.

> **Nota editorial**: o resumo executivo do documento original cita "10 variáveis", mas a estrutura detalhada nas seções 3 e 4 usa **11 variáveis** com pesos somando 100% (ver §3 e §4.1). Considerar 11 como o número correto — é o valor também usado em `IncluIA_MVP5` e no protótipo funcional.

---

## 1. Fundamentação

O Score Escola Sem Barreiras foi desenvolvido para responder a uma lacuna crítica de governança: apesar de o Brasil possuir dados anuais detalhados sobre infraestrutura e recursos de inclusão escolar — os Microdados do Censo Escolar do INEP —, não existe nenhum índice que transforme essas variáveis em uma métrica comparável, auditável e acionável para gestores públicos.

O Decreto 12.686/2025, que institui a Política Nacional de Educação Especial Inclusiva (PNEEI) — posteriormente alterado pontualmente pelo Decreto 12.773/2025, ver `docs/legislacao.md` —, agrava essa lacuna ao estabelecer critérios objetivos de conformidade sem oferecer instrumentos de medição. O Score Escola Sem Barreiras nasce como resposta direta a essa demanda regulatória.

### 1.1 Princípios Metodológicos

- **Auditabilidade**: cada variável é rastreável ao campo original do Censo Escolar, permitindo verificação independente.
- **Replicabilidade**: a metodologia pode ser aplicada a qualquer edição futura do Censo sem alteração estrutural.
- **Comparabilidade**: o mesmo índice é calculado com as mesmas variáveis e pesos para todos os 5.570 municípios.
- **Acionabilidade**: o score é decomposto por dimensão, permitindo que o gestor identifique exatamente onde seu município está mal e o que fazer.
- **Ponderação por impacto, não por raridade**: variáveis mais raras no Censo (como revisores de Braille) recebem pesos compatíveis com seu impacto na inclusão, não com sua frequência.

---

## 2. Dados de Referência — Censo Escolar 2025

Prevalência real de cada indicador na base do Censo Escolar 2025, calculada sobre uma amostra representativa de 50.000 estabelecimentos. Esses dados fundamentam as decisões de ponderação.

| Variável | Campo no Censo | Prevalência (amostra 50k) |
|---|---|---|
| AEE ofertado, não exclusivamente | `TP_AEE = 1` | 21,3% |
| AEE ofertado, exclusivamente | `TP_AEE = 2` | 0,5% |
| Sem nenhum AEE | `TP_AEE = 0` | 63,3% |
| Sala de atendimento especial | `IN_SALA_ATENDIMENTO_ESPECIAL = 1` | 25,1% |
| Professor de LIBRAS | `QT_PROF_TRAD_LIBRAS > 0` | 1,7% |
| Revisor de Braille | `QT_PROF_REVISOR_BRAILLE > 0` | 0,4% |
| Rampa de acessibilidade | `IN_ACESSIBILIDADE_RAMPAS = 1` | 53,9% |
| Banheiro adaptado PNE | `IN_BANHEIRO_PNE = 1` | 41,4% |
| Corrimão | `IN_ACESSIBILIDADE_CORRIMAO = 1` | 19,8% |
| Piso tátil | `IN_ACESSIBILIDADE_PISOS_TATEIS = 1` | 3,1% |
| Sinal visual | `IN_ACESSIBILIDADE_SINAL_VISUAL = 1` | 7,2% |
| Sinal sonoro | `IN_ACESSIBILIDADE_SINAL_SONORO = 1` | 2,2% |
| Elevador | `IN_ACESSIBILIDADE_ELEVADOR = 1` | 1,5% |
| Taxa de inclusão em classe comum | `QT_MAT_ESP_CC / QT_MAT_ESP` (Tabela Matrícula) | — |

> ⚠️ **Nota sobre TP_AEE**: o campo indica se a escola oferta AEE: `0` = não oferece, `1` = sim, não exclusivamente (AEE ofertado junto com ensino regular), `2` = sim, exclusivamente (escola/unidade dedicada só ao AEE). Ambos os valores 1 e 2 indicam que a escola oferta AEE — a diferença é o modelo de oferta, não a existência do serviço. Por isso ambos recebem pontuação completa (ver §3, Dimensão 1).

---

## 3. Estrutura do Score Escola Sem Barreiras

O Score é organizado em três dimensões, cada uma cobrindo um aspecto distinto da governança da inclusão. A soma dos pesos de todas as variáveis totaliza 100%.

### Dimensão 1 — Suporte Educacional Especializado (45%)

É a dimensão de maior peso por representar o serviço central mandatório da política de inclusão. A oferta de AEE é o indicador mais crítico: uma escola sem AEE não oferece suporte educacional especializado, independentemente de quantos recursos físicos possua.

| Variável | Campo | Pontuação | Peso |
|---|---|---|---|
| Oferta de AEE — não exclusivamente | `TP_AEE = 1` | 1,0 | 30% |
| Oferta de AEE — exclusivamente | `TP_AEE = 2` | 1,0 | (incluso nos 30%) |
| Sem oferta de AEE | `TP_AEE = 0` | 0,0 | (incluso nos 30%) |
| Taxa de inclusão em classe comum | `QT_MAT_ESP_CC / QT_MAT_ESP` | 0,0 a 1,0 | 15% |

**📐 Cálculo — Taxa de Inclusão em Classe Comum**
```
Taxa_CC = QT_MAT_ESP_CC ÷ QT_MAT_ESP
```
Onde `QT_MAT_ESP_CC` = matrículas de alunos com deficiência em classe comum, e `QT_MAT_ESP` = total de matrículas de alunos com deficiência. Para escolas sem nenhum aluno com deficiência matriculado (`QT_MAT_ESP = 0`), a variável recebe o valor médio do município. Fonte: `Tabela_Matricula_2025.csv` — requer cruzamento com `CO_ENTIDADE`.

### Dimensão 2 — Recursos Humanos Especializados (25%)

Profissionais especializados são os recursos mais raros e de mais difícil reposição do sistema. Um professor de LIBRAS ou revisor de Braille representa um investimento de anos de formação. A raridade (1,7% e 0,4% das escolas, respectivamente) justifica o peso elevado: quando presente, representa uma entrega concreta de inclusão.

| Variável | Campo | Pontuação | Peso |
|---|---|---|---|
| Professor de LIBRAS | `QT_PROF_TRAD_LIBRAS > 0` | 1,0 (binário) | 15% |
| Revisor de Braille | `QT_PROF_REVISOR_BRAILLE > 0` | 1,0 (binário) | 10% |

### Dimensão 3 — Acessibilidade Física (30%)

A acessibilidade física é condição necessária mas não suficiente para a inclusão. Seu peso total (30%) é expressivo, mas inferior ao suporte educacional porque um prédio acessível sem AEE ou profissionais capacitados não garante inclusão real. As variáveis são ponderadas de acordo com seu impacto funcional: rampa e banheiro PNE são requisitos básicos de deslocamento e higiene, corrimão é complementar, e sinalizações atendem necessidades sensoriais específicas.

| Variável | Campo | Prevalência | Peso | Justificativa |
|---|---|---|---|---|
| Rampa de acessibilidade | `IN_ACESSIBILIDADE_RAMPAS` | 53,9% | 8% | Requisito básico de deslocamento |
| Banheiro adaptado PNE | `IN_BANHEIRO_PNE` | 41,4% | 7% | Necessidade fisiológica fundamental |
| Corrimão | `IN_ACESSIBILIDADE_CORRIMAO` | 19,8% | 6% | Complementar à rampa |
| Piso tátil | `IN_ACESSIBILIDADE_PISOS_TATEIS` | 3,1% | 4% | Orientação para deficientes visuais |
| Sinal visual | `IN_ACESSIBILIDADE_SINAL_VISUAL` | 7,2% | 2% | Sinalização para surdos |
| Sinal sonoro | `IN_ACESSIBILIDADE_SINAL_SONORO` | 2,2% | 2% | Alertas para deficientes visuais |
| Elevador | `IN_ACESSIBILIDADE_ELEVADOR` | 1,5% | 1% | Acesso em edificações de múltiplos andares |

---

## 4. Fórmulas de Cálculo

### 4.1 Score por Escola

O Score de cada escola é calculado como a soma ponderada dos indicadores normalizados:

```
Score_escola = (0,30 × V_AEE) + (0,15 × V_taxa_CC) + (0,15 × V_libras) + (0,10 × V_braille)
             + (0,08 × V_rampa) + (0,07 × V_banheiro_pne) + (0,06 × V_corrimao)
             + (0,04 × V_piso_tatil) + (0,02 × V_sinal_visual) + (0,02 × V_sinal_sonoro) + (0,01 × V_elevador)
```

Onde cada `V_x ∈ [0,0 ; 1,0]` conforme a tabela de pontuações. O resultado `Score_escola ∈ [0,0 ; 1,0]` é multiplicado por 10 para obter a escala final:

```
Score_IncluIA_escola = Score_escola × 10
```

> ✅ **Verificação**: a soma de todos os pesos = 0,30 + 0,15 + 0,15 + 0,10 + 0,08 + 0,07 + 0,06 + 0,04 + 0,02 + 0,02 + 0,01 = **1,00 (100%)**. Score máximo possível = 10,0 quando todos os indicadores = 1.

### 4.2 Agregação para o Nível Municipal

O Score municipal é a média ponderada dos scores das escolas do município, onde o peso de cada escola é o número de alunos com deficiência matriculados (`QT_MAT_ESP`). Isso garante que escolas com mais alunos incluídos tenham maior impacto na nota do município.

```
Score_municipio = Σ (Score_escola_i × QT_MAT_ESP_i) ÷ Σ QT_MAT_ESP_i
```

Para municípios onde todas as escolas têm `QT_MAT_ESP = 0`, utiliza-se média simples dos scores das escolas (média não ponderada).

> ⚠️ **Tratamento de escolas exclusivamente especiais**: escolas com `IN_ESPECIAL_EXCLUSIVA = 1` ofertam apenas modalidade de ensino especial — não há integração com ensino regular. Essas escolas recebem `V_taxa_CC = 0` por definição (não há classe comum), mas são mantidas no cálculo para não distorcer o score do município. O campo `IN_ESPECIAL_EXCLUSIVA` é registrado como flag na base para análises desagregadas.

### 4.3 Agregação para o Nível Estadual

```
Score_UF = Σ (Score_municipio_j × QT_MAT_ESP_total_municipio_j) ÷ Σ QT_MAT_ESP_total_UF
```

---

## 5. Interpretação do Score

| Faixa | Classificação | Significado para o Gestor |
|---|---|---|
| 0,0 a 2,9 | 🔴 Crítico | Município sem infraestrutura mínima. AEE ausente ou inexistente na maioria das escolas. Intervenção urgente. |
| 3,0 a 4,9 | 🟠 Insuficiente | Alguns recursos presentes, mas gaps críticos. Falta AEE estruturado ou profissionais especializados. |
| 5,0 a 6,9 | 🟡 Em desenvolvimento | Base mínima de inclusão. Recursos físicos presentes, mas RH especializado escasso. |
| 7,0 a 8,4 | 🟢 Adequado | Boa cobertura de AEE e acessibilidade. Gaps pontuais em sinalizações ou Braille. |
| 8,5 a 10,0 | 🟣 Referência | Município exemplar. Pode ser usado como benchmark para municípios de mesmo porte. |

> **Nota de consistência visual**: este documento usa 🟣 (roxo) como emoji ilustrativo da faixa "Referência", mas o valor hexadecimal usado em toda a interface e nos demais documentos (`context.md`, `interface.md`) é **#1351B4 (azul institucional)** — usar sempre a cor hex como fonte de verdade de implementação, o emoji é só uma legenda textual do documento original.

---

## 6. Decomposição do Score — Diagnóstico por Dimensão

Além do score total, a Escola Sem Barreiras exibe o score por dimensão (D1, D2, D3), permitindo diagnóstico preciso. Um município pode ter score total 6,0 mas score D2 = 0,0 (sem nenhum professor de LIBRAS ou revisor de Braille) — isso é informação acionável que o score total não revelaria.

| Dimensão | Score Parcial | O que revela ao gestor |
|---|---|---|
| D1 — Suporte Educacional (45%) | `Score_D1 = (0,30×V_AEE + 0,15×V_CC) ÷ 0,45 × 10` | Se AEE está estruturado e alunos estão em classe comum |
| D2 — Recursos Humanos (25%) | `Score_D2 = (0,15×V_libras + 0,10×V_braille) ÷ 0,25 × 10` | Se há profissionais especializados para surdos e cegos |
| D3 — Acessibilidade Física (30%) | `Score_D3 = soma_D3 ÷ 0,30 × 10` | Qual infraestrutura física está disponível |

---

## 7. Limitações e Cautelas

- O score mede **disponibilidade** de recursos, não qualidade de uso. Uma escola pode ter sala de AEE registrada e não utilizá-la adequadamente — isso não é capturável pelos microdados.
- A taxa de inclusão em classe comum mede **proporção**, não qualidade da inclusão. Um aluno matriculado em classe comum sem suporte adequado é contado positivamente no indicador.
- **Elevador** penaliza municípios com escolas em terrenos planos que nunca necessitarão de elevador. Isso é uma limitação conhecida — o peso baixo (1%) minimiza o impacto.
- O score é comparável **apenas dentro da mesma edição do Censo**. Comparações interanuais requerem recálculo com os dados de cada ano.
- Municípios muito pequenos (< 5 escolas com alunos ESP) têm score mais volátil — uma única escola impacta significativamente a média municipal.

---

## 8. Alinhamento com a PNEEI (Decreto 12.686/2025)

A PNEEI (Decreto 12.686/2025, alterado pontualmente pelo Decreto 12.773/2025; ver `docs/legislacao.md` para o texto legal completo e o mapeamento validado por eixo) estabelece quatro eixos de conformidade para a inclusão escolar. A tabela abaixo mostra a correspondência entre esses eixos e as variáveis do Score Escola Sem Barreiras:

| Eixo da PNEEI | Indicador Escola Sem Barreiras | Variável do Censo |
|---|---|---|
| Oferta de AEE | V_AEE (peso 30%) | `TP_AEE` |
| Acessibilidade física | D3 completo (peso 30%) | 6 variáveis `IN_ACESSIBILIDADE_*` |
| Profissionais especializados | D2 completo (peso 25%) | `QT_PROF_TRAD_LIBRAS`, `QT_PROF_REVISOR_BRAILLE` |
| Inclusão em classe comum | V_taxa_CC (peso 15%) | `QT_MAT_ESP_CC / QT_MAT_ESP` |

Esta tabela é a confirmação oficial de que os pesos por Eixo da PNEEI usados na interface (`interface.md` §5.2) devem ser **30% / 30% / 25% / 15%** (Eixo I / II / III / IV) — exatamente os mesmos valores já adotados como decisão em [docs/business-rules/score-incluia.md](docs/business-rules/score-incluia.md) RN-01.

> ⚠️ **Nota jurídica**: o alinhamento com a PNEEI apresentado nesta seção é uma aproximação metodológica baseada na leitura técnica dos textos legais (ver `docs/legislacao.md`). Os critérios exatos de conformidade jurídica estão em processo de validação com especialistas em direito educacional e serão incorporados na Fase 2 do produto. **O Score Escola Sem Barreiras não deve ser utilizado como instrumento oficial de prestação de contas ao MEC até a conclusão dessa validação.**
