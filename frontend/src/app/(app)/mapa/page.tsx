import { getKpisNacionais, getMunicipiosPorUf, getRankingPorUf } from "@/features/mapa/api";
import { MapaClient } from "@/features/mapa/components/MapaClient";

const UF_PADRAO = "RJ";

// Os dados do mapa mudam por requisição (score recalculado, futura filtragem por perfil de
// usuário) — força renderização dinâmica em vez de pré-renderizar no build.
export const dynamic = "force-dynamic";

// Server Component: busca os dados iniciais no servidor (SSR) — ver interface.md §3 e
// arquitetura.md (justificativa de SSR do Next.js). Trocas de UF acontecem no cliente (MapaClient).
export default async function MapaPage() {
  const [kpis, municipios, ranking] = await Promise.all([
    getKpisNacionais(),
    getMunicipiosPorUf(UF_PADRAO),
    getRankingPorUf(UF_PADRAO),
  ]);

  return (
    <div className="h-full">
      <MapaClient
        kpisIniciais={kpis}
        ufInicial={UF_PADRAO}
        municipiosIniciais={municipios}
        rankingInicial={ranking}
      />
    </div>
  );
}
