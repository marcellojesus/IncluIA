# Feature: Score Escola Sem Barreiras (ETL)

Specs: `docs/requirements/score-incluia.md` · `docs/business-rules/score-incluia.md` · `metodologia_score.md`

Rodar: `python -m etl.run_etl` (a partir de `backend/`, com o `.venv` ativo) — gera `data/incluia.db`.

## Base normativa (AD-08)

Specs: `docs/sdd/fase-2/arquitetura.md` (AD-08) · `docs/legislacao.md`

Rodar: `python -m etl.base_normativa.construir` (a partir de `backend/`, com o `.venv` ativo e `GEMINI_API_KEY` no `.env`) — gera `data/base_normativa.db` a partir de `base/legislacao/` e dos arquivos `corpus.json` e `mapa_barreira_norma.json`. Com `--sem-embeddings`, gera só a busca por palavra-chave. No plano gratuito a geração dos embeddings espera o limite por minuto da API (cerca de 2 minutos para o corpus atual).

Para incluir um documento novo: registrar a fonte em `docs/legislacao.md`, salvar o texto em `base/legislacao/` e acrescentar a entrada em `corpus.json`; depois rodar o comando e os testes (`tests/test_base_normativa.py`).

Avaliar a busca e as respostas da IA: `python -m etl.base_normativa.avaliar` (só busca) ou `--com-ia` (também gera e valida respostas; consome cota, com 15 s entre perguntas). `--meta 0.9` faz o comando falhar abaixo de 90% de acerto entre os 3 primeiros. As perguntas ficam em `etl/base_normativa/avaliacao.json`; acrescentar perguntas reais a cada documento novo no corpus.
