// Classificação do Score Escola Sem Barreiras em faixas — espelha backend/etl/score.py e metodologia_score.md §5.
// Fonte de verdade do CÁLCULO do score é sempre o backend; esta função só decide COR/RÓTULO no cliente.

export type Faixa = "Crítico" | "Insuficiente" | "Em desenvolvimento" | "Adequado" | "Referência";

export const FAIXAS: Array<{ limite: number; faixa: Faixa; cor: string }> = [
  { limite: 8.5, faixa: "Referência", cor: "#0a5c4f" },
  { limite: 7.0, faixa: "Adequado", cor: "#2f9e6b" },
  { limite: 5.0, faixa: "Em desenvolvimento", cor: "#e0952b" },
  { limite: 3.0, faixa: "Insuficiente", cor: "#f0a54a" },
  { limite: 0, faixa: "Crítico", cor: "#d64545" },
];

export function classificarFaixa(score: number): { faixa: Faixa; cor: string } {
  const encontrada = FAIXAS.find(({ limite }) => score >= limite);
  const { faixa, cor } = encontrada ?? FAIXAS[FAIXAS.length - 1];
  return { faixa, cor };
}

export function formatarScore(score: number): string {
  return score.toFixed(1).replace(".", ",");
}
