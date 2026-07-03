import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { MunicipioDetalhe } from "./types";

export async function getMunicipioDetalhe(codigoIbge: number): Promise<MunicipioDetalhe | null> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Falha ao carregar os indicadores do município");
  return res.json();
}
