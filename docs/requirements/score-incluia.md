# Requisitos — Score Escola Sem Barreiras (Engine de Cálculo)

Fonte de contexto: `context.md` §5, `IncluIA_Metodologia_Score_v1`. Esta é uma funcionalidade **transversal**: não tem tela própria, mas alimenta [[mapa]], [[indicadores-municipio]] e [[escolas]].

## Objetivo

Calcular, a partir dos microdados do Censo Escolar, um índice único de 0 a 10 (Score Escola Sem Barreiras) por escola, agregável para município e estado, refletindo o grau de conformidade com os 4 Eixos da PNEEI (Decreto 12.686/2025).

## Atores

Nenhum ator humano direto — é um processo de backend (ETL + cálculo) consumido pelas demais funcionalidades. Indiretamente, todo gestor que usa o produto depende deste cálculo.

## Pré-condições

- Microdados do Censo Escolar disponíveis (`Tabela_Escola_2025.csv`, `Tabela_Matricula_2025.csv`) ou dataset equivalente (mock/seed enquanto os arquivos reais não estiverem disponíveis).

## Requisitos Funcionais

- **RF-01**: Calcular o score de cada escola a partir das 11 variáveis do Censo definidas na metodologia (ver regras de negócio), normalizadas para uma escala 0–10.
- **RF-02**: Agregar o score de escola para score de município por média ponderada pelo número de alunos com deficiência (`QT_MAT_ESP`) de cada escola.
- **RF-03**: Agregar o score de município para score de estado (UF) pela mesma lógica de ponderação por total de alunos ESP.
- **RF-04**: Calcular também o score parcial por eixo do Decreto (I–IV), não apenas o score geral — necessário para os semáforos e barras de progresso de [[indicadores-municipio]].
- **RF-05**: Classificar qualquer score (escola, município ou estado) em uma das 5 faixas: Crítico, Insuficiente, Em desenvolvimento, Adequado, Referência — com a cor correspondente.
- **RF-06**: Reprocessar o score sempre que uma nova edição do Censo for carregada, versionando o resultado (o score de uma edição anterior não deve ser sobrescrito silenciosamente antes de o time confirmar a nova carga).
- **RF-07**: Expor o score e seus componentes (por eixo, por variável) via API para consumo pelo frontend — nunca calcular o score no frontend a partir de dados brutos.

## Requisitos Não Funcionais

- **RNF-01**: O cálculo deve rodar em lote (ETL) sobre ~214 mil escolas e ~5.570 municípios em tempo viável para atualização anual (não precisa ser tempo real).
- **RNF-02**: O resultado do cálculo deve ser persistido (SQLite no MVP) para consulta rápida pela API, sem recalcular a cada requisição.
- **RNF-03**: A fórmula de cálculo deve estar centralizada em um único módulo/função por nível (escola, município, estado), para que uma mudança de peso ou variável não exija alterar múltiplos pontos do código.

## Dados de entrada/saída

**Entrada**: linhas do Censo por escola, com as variáveis listadas em `docs/business-rules/score-incluia.md`.
**Saída**: `{ codigoInep|codigoIbge, score, scoreEixoI, scoreEixoII, scoreEixoIII, scoreEixoIV, faixa, cor }`.

## Fluxo principal

1. ETL lê os CSVs do Censo (ou dataset seed) e cruza Escola × Matrícula por `CO_ENTIDADE`.
2. Para cada escola, calcula o score geral e por eixo.
3. Agrega para município e estado, ponderando por alunos ESP.
4. Persiste os resultados em SQLite (tabelas `escolas`, `municipios`, `uf_agregado`, conforme `IncluIA_PlanoTrabalho_v1`).
5. API expõe os resultados já calculados para as demais funcionalidades.

## Fluxos alternativos

- **Escola sem nenhum aluno ESP matriculado** (`QT_MAT_ESP=0`): não deve distorcer a agregação municipal (peso zero na ponderação) nem gerar um score de escola sem sentido — ver regra de negócio específica.
- **Dataset do Censo real ainda não disponível**: usar gerador de dados sintéticos com as mesmas colunas e prevalências documentadas (ver `IncluIA_Metodologia_Score_v1`), claramente marcado como dado mock, nunca misturado sem rótulo com dado real.

## Critérios de aceite

- [ ] Soma dos pesos das variáveis usadas no cálculo é exatamente 100% (ver [[diagnostico-ia]] RN-03 sobre a fonte do veredito).
- [ ] Score de um município recalculado bate com a média ponderada manual das escolas daquele município (teste de conferência).
- [ ] Toda escola/município tem uma faixa e cor associadas sem ambiguidade (nenhum score cai fora das 5 faixas definidas).
