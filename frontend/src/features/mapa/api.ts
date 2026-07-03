import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { KpisNacionais, MunicipioResumo, RankingUf } from "./types";

export async function getKpisNacionais(): Promise<KpisNacionais> {
  const res = await fetch(`${API_BASE_URL}/kpis-nacionais`);
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
