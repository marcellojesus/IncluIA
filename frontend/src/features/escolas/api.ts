import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { Escola } from "./types";

export async function getEscolasPorMunicipio(codigoIbge: number): Promise<Escola[]> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/escolas`);
  return res.json();
}

export async function getEscolaDetalhe(coEntidade: number): Promise<Escola> {
  const res = await fetch(`${API_BASE_URL}/escolas/${coEntidade}`);
  return res.json();
}
