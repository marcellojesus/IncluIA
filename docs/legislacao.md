# Base Legal da Escola Sem Barreiras

Este documento é a fonte de verdade única sobre qual texto legal fundamenta cada eixo do Score Escola Sem Barreiras. O código (`_ARTIGO_VALIDADO_POR_EIXO` em `backend/app/features/diagnostico_ia/service.py`) e o prompt do chat de diagnóstico devem espelhar exatamente este mapeamento — nunca citar um artigo que não esteja aqui.

## Os 3 textos legais do produto

Os textos integrais (ou o recorte relevante) estão salvos em `base/legislacao/`, cada um com a URL da fonte oficial e a data de consulta:

| Arquivo | O que é |
|---|---|
| `decreto_12686_2025_pneei.md` | **Decreto nº 12.686, de 20/10/2025 — texto consolidado** (fonte: Planalto, já incorporando as alterações do Decreto 12.773/2025 inline, com nota em cada trecho alterado) — o decreto que **efetivamente institui** a Política Nacional de Educação Especial Inclusiva (PNEEI) e a Rede Nacional de Educação Especial Inclusiva. 24 artigos: AEE, estudo de caso, PAEE, formação de professor de AEE e de profissional de apoio escolar, governança e Rede Nacional. |
| `decreto_12773_2025_alteracoes.md` | **Decreto nº 12.773, de 8/12/2025** — só 2 artigos; **altera pontualmente** o Decreto 12.686/2025 (eleva carga horária de formação de professor de AEE e de apoio escolar, consolida PAEE/PEI, garante recursos do Fundeb). Não institui nada por conta própria. |
| `lei_13146_2015_lbi_art27_a_30.md` | **Lei nº 13.146/2015 (Lei Brasileira de Inclusão — LBI)**, só o Capítulo IV "Do Direito à Educação" (Art. 27 a 30) — citada no próprio preâmbulo do Decreto 12.686/2025 como base legal. É aqui que estão as exigências de **acessibilidade física às edificações** (Art. 28, XVI) e de **LIBRAS/Braille/tecnologia assistiva** (Art. 28, XII) que o Decreto 12.686/2025 não detalha. |

**Correção histórica importante**: até esta revisão, o produto citava genericamente "Decreto 12.773/2025" como se fosse o decreto que institui a PNEEI, e o código chegou a citar "Art. 7º do Decreto 12.773/2025" como base para LIBRAS/Braille — artigo que na verdade nem existe nesse decreto (que só tem 2 artigos) e cujo equivalente no Decreto 12.686/2025 trata de regulamentação do AEE pelo MEC, sem nenhuma relação com LIBRAS/Braille. Essa citação era factualmente incorreta e foi substituída pelo mapeamento abaixo, agora rastreável a um trecho real de lei.

**Atualização de fonte**: `decreto_12686_2025_pneei.md` foi atualizado para o texto consolidado da Presidência da República (Planalto), que já mescla o texto original com as alterações do Decreto 12.773/2025 (a versão anterior, obtida da Câmara dos Deputados, trazia só o texto original de 20/10/2025). Essa consolidação revelou um detalhe relevante para o Eixo IV: o Art. 4º, II, que na redação original previa a faixa etária de "quatro aos dezessete anos", foi alterado pelo Decreto 12.773/2025 para "**de zero a dezessete anos**" — uma ampliação da cobertura etária da PNEEI que o produto não refletia antes desta atualização.

## Mapeamento oficial: eixo → base legal

| Eixo do Score Escola Sem Barreiras | Base legal validada | Trecho relevante |
|---|---|---|
| **I — AEE** | Decreto 12.686/2025, Art. 5º a Art. 10 | Define o AEE, seus objetivos e organização (caráter complementar/suplementar, não substitutivo à classe comum). |
| **II — Acessibilidade física** | Lei 13.146/2015, Art. 28, II e XVI | "aprimoramento dos sistemas educacionais... por meio da oferta de... recursos de acessibilidade que eliminem as barreiras" (II); "acessibilidade... às edificações, aos ambientes..." (XVI). |
| **III — Profissionais (LIBRAS/Braille)** | Lei 13.146/2015, Art. 28, XI, XII e § 2º | "formação e disponibilização de... tradutores e intérpretes da Libras... e de profissionais de apoio" (XI); "oferta de ensino da Libras, do Sistema Braille..." (XII); qualificação mínima exigida de tradutores/intérpretes de Libras (§ 2º). |
| **IV — Inclusão em classe comum** | Decreto 12.686/2025, Art. 1º, § 3º e Art. 8º | Garantia de inclusão dos estudantes em classes e escolas comuns (Art. 1º § 3º); "a matrícula no AEE não poderá ser substitutiva à matrícula e à frequência na classe comum" (Art. 8º). |

## Regra de uso (aplica-se a todo o produto)

- Nunca citar um número de artigo que não esteja nesta tabela. Ao validar uma nova base legal para um critério, primeiro adicionar a linha aqui (com o trecho literal), só depois usá-la no código/prompt.
- O aviso permanente "⚠️ Em validação jurídica" (RN-02 de `docs/business-rules/indicadores-municipio.md`) continua valendo mesmo com essas citações corretas — o mapeamento score↔lei é uma aproximação metodológica do produto, não uma certificação jurídica formal perante o MEC ou auditorias.
- Ao se referir ao decreto da PNEEI de forma genérica (sem citar artigo), usar **"PNEEI (Decreto 12.686/2025)"** — nunca só "Decreto 12.773/2025", que é apenas o decreto de alterações pontuais.
