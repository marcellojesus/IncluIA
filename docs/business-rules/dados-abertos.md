# Regras de Negócio — Dados Abertos (Módulo novo)

## RN-01 — Nunca simular um catálogo de datasets que não existe de verdade

`/dados-abertos` não lista datasets próprios para download (índice por município, matrículas ESP, etc.) enquanto essa exportação não for implementada de verdade — mesmo que visualmente atraente, uma lista de cards com botões "Baixar" desabilitados foi descartada por dar a impressão de uma funcionalidade que não existe. A página só cita, com link real, a fonte oficial já publicamente disponível: os microdados do Censo Escolar no site do INEP.

**Por quê**: mesmo princípio de RN-04 de `docs/business-rules/escolas.md` (um botão visualmente ativo sem ação quebra a confiança do gestor no produto) — aplicado aqui à decisão de não fingir um catálogo de dados.

## RN-02 — O filtro geográfico do cabeçalho não aparece nesta página

`GeoFiltroBar.tsx` verifica a rota atual e não se renderiza em `/dados-abertos` (lista `ROTAS_SEM_FILTRO`) — o filtro Região→UF→Município não faz sentido numa página sobre dados nacionais, sem escopo de município.

## RN-03 — "Ver a API" aponta para a documentação viva do backend, não para uma página estática

O botão "Ver a API" abre `${API_BASE_URL}/docs` — o Swagger UI gerado automaticamente pelo FastAPI a partir das rotas reais — não uma página de documentação escrita à mão que poderia ficar desatualizada em relação ao código.
