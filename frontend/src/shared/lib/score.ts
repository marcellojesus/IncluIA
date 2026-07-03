// Classificação do Score IncluIA em faixas — espelha backend/etl/score.py e metodologia_score.md §5.
// Fonte de verdade do CÁLCULO do score é sempre o backend; esta função só decide COR/RÓTULO no cliente.

export type Faixa = "Crítico" | "Insuficiente" | "Em desenvolvimento" | "Adequado" | "Referência";

export const FAIXAS: Array<{ limite: number; faixa: Faixa; cor: string }> = [
  { limite: 8.5, faixa: "Referência", cor: "#1351B4" },
  { limite: 7.0, faixa: "Adequado", cor: "#168821" },
  { limite: 5.0, faixa: "Em desenvolvimento", cor: "#E6B800" },
  { limite: 3.0, faixa: "Insuficiente", cor: "#E05C00" },
  { limite: 0, faixa: "Crítico", cor: "#E52207" },
];

export function classificarFaixa(score: number): { faixa: Faixa; cor: string } {
  const encontrada = FAIXAS.find(({ limite }) => score >= limite);
  const { faixa, cor } = encontrada ?? FAIXAS[FAIXAS.length - 1];
  return { faixa, cor };
}

export function formatarScore(score: number): string {
  return score.toFixed(1).replace(".", ",");
}
