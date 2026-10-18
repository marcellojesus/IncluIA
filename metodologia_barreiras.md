# Barreiras Identificadas — Metodologia de Identificação

> Regra para identificar, a partir do Censo Escolar, as barreiras de cada escola usadas na Gestão Ativa
> Versão 0.1 (proposta) · Outubro 2026 · Baseada nos Microdados do Censo Escolar 2025 — INEP/MEC

> **Status: proposta para validação.** Esta metodologia foi elaborada para o produto mínimo viável (MVP) da Fase 2 e ainda não foi validada com diretores, secretários ou especialistas. Ela será revisada após a validação, assim como a [metodologia do score](metodologia_score.md).

Este documento define **o que é uma barreira** para a Escola Sem Barreiras, **como ela é identificada** em cada escola e **como é apresentada** ao diretor, ao secretário e ao público. As variáveis, os campos do Censo e os pesos vêm da [metodologia do score](metodologia_score.md); nenhuma variável nova foi criada para esta versão. As definições dos campos foram conferidas no dicionário oficial de dados do Censo 2025 (`base/microdados_censo_escolar_2025/Anexos/ANEXO I - Dicionário de Dados`).

---

## Resumo Executivo

Uma **barreira** é um recurso de inclusão que, segundo o Censo Escolar, a escola não tem. Para cada uma das 11 variáveis do score, a escola tem uma barreira quando o seu próprio dado indica ausência do recurso. Assim, toda barreira explica pontos que a escola deixa de somar no score, e os pontos perdidos no score aparecem como barreiras, com uma exceção documentada no Eixo IV (§1.2).

As barreiras são calculadas por regra fixa, sem uso de inteligência artificial, e ordenadas pelos pontos do score que cada uma representa. No Censo 2025, as escolas em atividade têm em média **7,8 barreiras** (mediana 8).

A barreira é o ponto de partida da Declaração de Obstáculos: para cada barreira, o diretor registra uma posição (obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão). A barreira não é veredito de descumprimento legal nem certificação.

---

## 1. Fundamentação

O score resume a situação da escola em um número. Para que diretores e secretários possam agir, é preciso dizer **quais recursos faltam**, com a mesma base de dados e a mesma lógica do score. Esta metodologia transforma cada variável do score em uma barreira legível e verificável.

### 1.1 Conceitos

| Termo | Definição | Quem define |
|---|---|---|
| **Barreira** | Ausência de um recurso de inclusão segundo o Censo Escolar, identificada por regra fixa | Esta metodologia, a partir do Censo |
| **Posição** | O que o diretor registra sobre a barreira: obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão | O diretor, na Declaração de Obstáculos |
| **Obstáculo** | Explicação da escola sobre o que impede superar a barreira | O diretor |

### 1.2 Princípios

- **Paridade com o score:** as barreiras usam exatamente as 11 variáveis e os campos do score. Uma barreira nunca existe sem impacto no score, e o score só perde pontos sem barreira correspondente em uma exceção do Eixo IV: a escola sem matrícula da educação especial, em que o score usa a média municipal (§4.1). Esta versão pressupõe a metodologia do score v1.1, que corrigiu o tratamento de `IN_ESPECIAL_EXCLUSIVA` (Anexo A).
- **Dado da própria escola:** a barreira só é identificada com o dado da escola. Valores estimados (como a média municipal usada no score para escolas sem matrícula da educação especial) não geram barreira.
- **Determinismo:** a mesma base produz sempre as mesmas barreiras. Inteligência artificial não identifica, remove nem ordena barreiras.
- **Auditabilidade:** cada barreira mostra o campo do Censo e o valor que a gerou.
- **Linguagem neutra:** a barreira descreve o dado ("o Censo não registra rampa"), sem atribuir culpa nem afirmar descumprimento legal.
- **Revisão explícita:** mudanças nas regras geram nova versão desta metodologia, com registro do que mudou.

---

## 2. Universo e Fonte

- **Fonte:** Microdados do Censo Escolar 2025 — `Tabela_Escola_2025.csv` e `Tabela_Matricula_2025.csv` (cruzadas por `CO_ENTIDADE`).
- **Universo:** escolas em atividade (`TP_SITUACAO_FUNCIONAMENTO = 1`), o mesmo universo do score. No Censo 2025: **180.540 escolas**.
- **Edição:** as barreiras valem para uma edição do Censo. Uma nova edição gera uma nova lista de barreiras; a lista anterior permanece associada às Declarações emitidas com base nela.

---

## 3. Regras de Identificação

Para cada escola, uma barreira é identificada quando a regra abaixo é verdadeira. A coluna **Pontos em jogo** mostra quantos pontos do score (escala 0 a 10) a escola deixa de somar por causa da barreira (ver §5).

### Eixo I — Atendimento Educacional Especializado (AEE)

| Código | Barreira | Regra (campo do Censo) | Texto exibido | Pontos em jogo |
|---|---|---|---|---|
| B-I-01 | Sem oferta de AEE | `TP_AEE = 0` | "O Censo 2025 registra que a escola não oferece AEE." | 3,0 |

### Eixo II — Acessibilidade física

| Código | Barreira | Regra (campo do Censo) | Texto exibido | Pontos em jogo |
|---|---|---|---|---|
| B-II-01 | Sem rampas | `IN_ACESSIBILIDADE_RAMPAS = 0` | "O Censo 2025 não registra rampas nas vias de circulação interna." | 0,8 |
| B-II-02 | Sem banheiro acessível | `IN_BANHEIRO_PNE = 0` | "O Censo 2025 não registra banheiro acessível a pessoas com deficiência ou mobilidade reduzida." | 0,7 |
| B-II-03 | Sem corrimão e guarda-corpos | `IN_ACESSIBILIDADE_CORRIMAO = 0` | "O Censo 2025 não registra corrimão e guarda-corpos." | 0,6 |
| B-II-04 | Sem pisos táteis | `IN_ACESSIBILIDADE_PISOS_TATEIS = 0` | "O Censo 2025 não registra pisos táteis." | 0,4 |
| B-II-05 | Sem sinalização visual | `IN_ACESSIBILIDADE_SINAL_VISUAL = 0` | "O Censo 2025 não registra sinalização visual (piso/paredes)." | 0,2 |
| B-II-06 | Sem sinalização sonora | `IN_ACESSIBILIDADE_SINAL_SONORO = 0` | "O Censo 2025 não registra sinalização sonora." | 0,2 |
| B-II-07 | Sem elevador | `IN_ACESSIBILIDADE_ELEVADOR = 0` | "O Censo 2025 não registra elevador." | 0,1 |

### Eixo III — Profissionais especializados

| Código | Barreira | Regra (campo do Censo) | Texto exibido | Pontos em jogo |
|---|---|---|---|---|
| B-III-01 | Sem tradutor e intérprete de Libras | `QT_PROF_TRAD_LIBRAS = 0` | "O Censo 2025 não registra tradutor e intérprete de Libras atuando na escola." | 1,5 |
| B-III-02 | Sem revisor de texto em Braille | `QT_PROF_REVISOR_BRAILLE = 0` | "O Censo 2025 não registra revisor de texto em Braille atuando na escola." | 1,0 |

### Eixo IV — Inclusão em classe comum

| Código | Barreira | Regra (campo do Censo) | Texto exibido | Pontos em jogo |
|---|---|---|---|---|
| B-IV-01 | Matrículas da educação especial em classes exclusivas | `QT_MAT_ESP > 0` e `QT_MAT_ESP_CE > 0` | "O Censo 2025 registra X de Y matrículas da educação especial em classes exclusivas." | 1,5 × (1 − Taxa_CC) |

`Taxa_CC = QT_MAT_ESP_CC ÷ QT_MAT_ESP`, conforme a metodologia do score.

---

## 4. Casos Especiais

### 4.1 Escola sem matrícula da educação especial (`QT_MAT_ESP = 0`)

- **Eixo IV:** não há barreira, porque não há matrícula para avaliar. O score usa a média municipal nesse caso (metodologia do score, §3), mas valor estimado não gera barreira (princípio do dado da própria escola). A escola aparece com "Eixo IV: sem matrícula da educação especial no Censo 2025".
- **Eixos I, II e III:** as barreiras são identificadas normalmente, como no score. A acessibilidade e o atendimento especializado são tratados como condição da escola, independentemente de haver matrícula naquele ano. A tela informa: "a escola não tem matrícula da educação especial no Censo 2025". **Ponto para validação** (ver §11).

### 4.2 Dado não informado

Quando o campo está vazio na base, o score o trata como ausência do recurso (valor 0). Para as barreiras, o dado vazio gera uma barreira com a marca **"informação não registrada no Censo"**, exibida de forma distinta da ausência confirmada. Ela conta nos pontos em jogo, para manter a paridade com o score. No Censo 2025, os campos usados aqui não têm valores vazios nas escolas em atividade; 1,0% das escolas não tem linha na tabela de matrícula e são tratadas como sem matrícula da educação especial (§4.1).

### 4.3 Escola sem nenhum recurso de acessibilidade

Quando `IN_ACESSIBILIDADE_INEXISTENTE = 1`, as barreiras B-II-01 e B-II-03 a B-II-07 são identificadas pelas regras normais (os campos correspondentes estarão em 0). A tela pode agrupá-las como "nenhum recurso de acessibilidade de circulação registrado".

### 4.4 Elevador

O Censo não informa o número de pavimentos da escola. Uma escola térrea terá a barreira B-II-07 mesmo sem precisar de elevador. A barreira é mantida pela paridade com o score, mas aparece por último na ordenação (0,1 ponto) com a nota "pode não se aplicar a prédios térreos". O diretor pode registrar a situação como divergência com o dado do Censo.

### 4.5 Escolas com classe especial exclusiva

`IN_ESPECIAL_EXCLUSIVA = 1` significa, no dicionário do Censo 2025, que a escola **possui ao menos uma classe especial exclusiva** — não que a escola seja exclusivamente especial. A barreira B-IV-01 usa a quantidade de matrículas (`QT_MAT_ESP_CE`), não esse indicador, em linha com a metodologia do score v1.1 (Anexo A).

### 4.6 Tradutor e intérprete de Libras

O campo `QT_PROF_TRAD_LIBRAS` conta tradutores e intérpretes de Libras que atuam em ambientes da escola **fora da sala de aula**. A barreira usa essa definição e o texto exibido não fala em "professor de Libras".

---

## 5. Ordenação das Barreiras

As barreiras de uma escola são ordenadas pelos **pontos em jogo**: os pontos do score (escala 0 a 10) que a escola deixa de somar por causa daquela barreira.

```
Pontos_em_jogo(x) = 10 × peso(x) × (1 − V_x)
```

Onde `peso(x)` e `V_x` são os da metodologia do score (§3 e §4.1). Para as variáveis binárias, os pontos em jogo são fixos (tabela da §3). Para o Eixo IV, dependem da taxa de inclusão em classe comum da escola. Em caso de empate, vale a ordem dos eixos (I, II, III, IV) e depois a ordem dos códigos.

> Os pontos em jogo são uma conta sobre o score, não uma estimativa de impacto real na vida dos estudantes. Eles respondem: "se este recurso passasse a constar no Censo, quantos pontos o score da escola somaria?". Essa leitura atende parcialmente à decisão pendente 12 do PRD da Fase 2 (método determinístico para estimar impacto no score).

---

## 6. Agregação para o Município

Para o secretário, cada barreira tem dois indicadores por município:

```
Recorrência(x) = escolas em atividade com a barreira x ÷ escolas em atividade do município
Matrículas_afetadas(x) = Σ QT_MAT_ESP das escolas com a barreira x
```

**Proposta para validação — barreira de alta recorrência na rede:** quando uma barreira está presente em **90% ou mais** das escolas do município, ela é sinalizada ao secretário como "alta recorrência na rede", indicando que a resposta provavelmente depende de ação municipal, e não de cada escola. O limite de 90% é uma proposta desta versão e deve ser validado.

No Censo 2025, as barreiras de profissionais especializados são as mais recorrentes no país: 97,7% das escolas não registram tradutor e intérprete de Libras e 99,6% não registram revisor de Braille.

---

## 7. Relação com a Declaração de Obstáculos

- A lista de barreiras da escola é gerada por esta metodologia e não pode ser editada pelo diretor nem pela secretaria.
- Para cada barreira, o diretor registra uma **posição** na Declaração de Obstáculos: obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão.
- A Declaração é emitida quando todas as barreiras da escola têm posição. Ela fica vinculada à edição do Censo e à versão desta metodologia usadas.
- Nenhuma posição, divergência, emissão ou publicação altera o dado do Censo, a barreira identificada ou o score.

---

## 8. Dados de Referência — Censo Escolar 2025

Prevalência de cada barreira nas **180.540 escolas em atividade** do Censo 2025 (base completa, não amostra):

| Código | Barreira | Escolas com a barreira |
|---|---|---|
| B-III-02 | Sem revisor de texto em Braille | 99,6% |
| B-III-01 | Sem tradutor e intérprete de Libras | 97,7% |
| B-II-06 | Sem sinalização sonora | 95,4% |
| B-II-07 | Sem elevador | 94,3% |
| B-II-05 | Sem sinalização visual | 88,0% |
| B-II-04 | Sem pisos táteis | 86,3% |
| B-I-01 | Sem oferta de AEE | 70,9% |
| B-II-03 | Sem corrimão e guarda-corpos | 61,3% |
| B-II-02 | Sem banheiro acessível | 43,0% |
| B-II-01 | Sem rampas | 38,0% |
| B-IV-01 | Matrículas da educação especial em classes exclusivas | 2,1% |

- **Barreiras por escola:** média 7,8 · mediana 8 · 10% das escolas têm 6 ou menos · 10% têm 10 ou mais.
- **Escolas com matrícula da educação especial** (`QT_MAT_ESP > 0`): 83,0%.

> Cálculo feito sobre os arquivos `Tabela_Escola_2025.csv` e `Tabela_Matricula_2025.csv` locais, com o filtro `TP_SITUACAO_FUNCIONAMENTO = 1`.

---

## 9. Limitações e Cautelas

- **Disponibilidade, não qualidade:** a barreira indica a ausência de registro do recurso, não a qualidade de uso de um recurso existente.
- **Dado declarado:** o Censo é preenchido pela própria escola. Um recurso existente e não declarado aparece como barreira; por isso existe a posição "divergência com o dado do Censo".
- **Sem tipo de deficiência por escola:** os microdados públicos por escola não informam quantos estudantes têm cada tipo de deficiência (os campos `QT_MAT_ESP_D`, `_DM`, `_DV` e `_N` referem-se a turnos). Por isso, a barreira "sem tradutor e intérprete de Libras" é identificada mesmo que a escola não tenha estudantes surdos matriculados.
- **Barreiras quase universais:** Libras e Braille estão ausentes em quase todas as escolas; tendem a ser resolvidas pela rede, não pela escola isoladamente (ver §6).
- **Elevador em prédios térreos:** ver §4.4.
- **Comparação entre anos:** barreiras são comparáveis apenas dentro da mesma edição do Censo.
- **Não é certificação:** a barreira não constitui avaliação jurídica de conformidade com a PNEEI.

---

## 10. Candidatas para a Próxima Revisão

Campos do Censo 2025 relacionados à inclusão que **não entram nesta versão** porque não fazem parte do score. A inclusão de qualquer um exige revisão conjunta desta metodologia e da metodologia do score.

| Campo | Descrição no dicionário | Observação |
|---|---|---|
| `IN_SALA_ATENDIMENTO_ESPECIAL` | Sala de Recursos Multifuncionais para AEE | 70,0% das escolas em atividade não registram a sala |
| `IN_ACESSIBILIDADE_VAO_LIVRE` | Portas com vão livre de, no mínimo, 80 cm | Acessibilidade de circulação |
| `IN_ACESSIBILIDADE_SINAL_TATIL` | Sinalização tátil (piso/paredes) | Diferente de pisos táteis |
| `IN_ACESSIBILIDADE_SINALIZACAO` | Sinalização/alarme luminoso | Relevante para estudantes surdos |
| `IN_MATERIAL_PED_EDU_ESP` | Materiais pedagógicos para a educação especial | Recurso pedagógico |
| `IN_MATERIAL_PED_BIL_SURDOS` | Materiais pedagógicos para a educação bilíngue de surdos | Recurso pedagógico |

---

## 11. Questões para Validação

1. Barreiras dos Eixos I, II e III devem ser identificadas em escolas sem matrícula da educação especial (§4.1)?
2. O limite de 90% para "alta recorrência na rede" é adequado (§6)?
3. Barreiras quase universais (Libras e Braille) devem exigir posição de cada diretor na Declaração, ou podem ser tratadas como barreiras da rede, com posição registrada pela secretaria?
4. A sala de recursos multifuncionais deve entrar na próxima versão do score e desta metodologia (§10)?
5. O elevador deve continuar gerando barreira enquanto o Censo não informar o número de pavimentos (§4.4)?
6. A redação dos textos exibidos (§3) é clara e neutra para diretores, secretários e público?

---

## Anexo A — Divergências Encontradas na Metodologia do Score

Ao conferir os campos no dicionário oficial do Censo 2025 para esta metodologia, foram encontradas três diferenças na [metodologia do score](metodologia_score.md) v1.0. **As três foram corrigidas na v1.1 do score (outubro de 2026).**

1. **`IN_ESPECIAL_EXCLUSIVA` (metodologia do score, §4.2):** a v1.0 descrevia o campo como "escola que oferta apenas modalidade de ensino especial" e atribuía `V_taxa_cc = 0`. O dicionário define o campo como "escola possui classe especial exclusiva (ao menos uma turma exclusiva)". No Censo 2025, 2.080 escolas com esse indicador tinham matrículas da educação especial em classe comum e, mesmo assim, recebiam 0 no Eixo IV. Na v1.1, essas escolas usam a taxa real de inclusão em classe comum.
2. **`QT_PROF_TRAD_LIBRAS` (metodologia do score, §2 e §3):** o score chama a variável de "Professor de LIBRAS". O dicionário define "Tradutor e Intérprete de Libras para atendimento em outros ambientes da escola que não seja sala de aula".
3. **`IN_ACESSIBILIDADE_SINAL_VISUAL` (metodologia do score, §3):** o score justifica a variável como "sinalização para surdos". O dicionário define "Sinalização visual (piso/paredes)"; o recurso de alarme luminoso é outro campo (`IN_ACESSIBILIDADE_SINALIZACAO`).

---

## Anexo B — Exemplo de Aplicação

Escola fictícia, em atividade, com os seguintes dados no Censo:

| Campo | Valor |
|---|---|
| `TP_AEE` | 0 |
| `QT_PROF_TRAD_LIBRAS` / `QT_PROF_REVISOR_BRAILLE` | 0 / 0 |
| `IN_ACESSIBILIDADE_RAMPAS` / `IN_BANHEIRO_PNE` / `IN_ACESSIBILIDADE_CORRIMAO` | 1 / 0 / 1 |
| `IN_ACESSIBILIDADE_PISOS_TATEIS` / `_SINAL_VISUAL` / `_SINAL_SONORO` / `_ELEVADOR` | 0 / 0 / 0 / 0 |
| `QT_MAT_ESP` / `QT_MAT_ESP_CC` / `QT_MAT_ESP_CE` | 10 / 8 / 2 |

Barreiras identificadas, já ordenadas por pontos em jogo:

| Ordem | Código | Barreira | Pontos em jogo |
|---|---|---|---|
| 1 | B-I-01 | Sem oferta de AEE | 3,0 |
| 2 | B-III-01 | Sem tradutor e intérprete de Libras | 1,5 |
| 3 | B-III-02 | Sem revisor de texto em Braille | 1,0 |
| 4 | B-II-02 | Sem banheiro acessível | 0,7 |
| 5 | B-II-04 | Sem pisos táteis | 0,4 |
| 6 | B-IV-01 | 2 de 10 matrículas da educação especial em classes exclusivas | 0,3 |
| 7 | B-II-05 | Sem sinalização visual | 0,2 |
| 8 | B-II-06 | Sem sinalização sonora | 0,2 |
| 9 | B-II-07 | Sem elevador (pode não se aplicar a prédios térreos) | 0,1 |

Total de pontos em jogo: 7,4. Score da escola: 10 − 7,4 = **2,6**, o mesmo resultado da fórmula da metodologia do score (§4.1): 10 × (0,15 × 0,8 + 0,08 + 0,06) = 2,6. Isso confirma a paridade entre as duas metodologias para esta escola.
