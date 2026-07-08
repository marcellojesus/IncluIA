import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { KpisNacionais, MunicipioResumo, RankingUf, UfRanking } from "./types";

export async function getKpisNacionais(): Promise<KpisNacionais> {
  const res = await fetch(`${API_BASE_URL}/kpis-nacionais`);
  return res.json();
}

// Ranking nacional dos 27 estados (score agregado por UF, ponderado pelo total de alunos ESP —
// ver metodologia_score.md §4.3). Lista completa, já ordenada por score desc.
export async function getRankingNacional(): Promise<UfRanking[]> {
  const res = await fetch(`${API_BASE_URL}/ranking-nacional`);
  return res.json();
}

export async function getMunicipiosPorUf(uf: string): Promise<MunicipioResumo[]> {
  const res = await fetch(`${API_BASE_URL}/uf/${uf}/municipios`);
  return res.json();
}

export async function getRankingPorUf(uf: string): Promise<RankingUf> {
  const res = await fetch(`${API_BASE_URL}/uf/${uf}/ranking`);
  return res.json();
}
