// Narrativa pública do município: sem login, só leitura (impacto-fase-1.md, opção 2).
import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { NarrativaMunicipio } from "./types";

export async function getNarrativa(codigoIbge: number): Promise<NarrativaMunicipio> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/narrativa`);
  if (res.status === 429) throw new Error("Muitas leituras novas em pouco tempo. Aguarde alguns minutos e tente de novo.");
  if (!res.ok) throw new Error("Não foi possível carregar a leitura deste município agora. Tente novamente em instantes.");
  return res.json();
}
