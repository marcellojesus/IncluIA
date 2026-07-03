"use client";

// Ver interface.md §3 — orquestra KPIs, toolbar, mapa e ranking; assume as trocas de UF no cliente.
import dynamic from "next/dynamic";
import { useRef, useState } from "react";

import { getMunicipiosPorUf, getRankingPorUf } from "../api";
import { getUfPorSigla } from "../lib/ufs";
import type { KpisNacionais, MunicipioResumo, RankingUf } from "../types";
import { KpiStrip } from "./KpiStrip";
import { LegendaScore } from "./LegendaScore";
import { MapaToolbar } from "./MapaToolbar";
import { RankingPanel } from "./RankingPanel";
import type { FocoSolicitado } from "./MapaLeaflet";

// Leaflet acessa `window`/`document` no import — precisa ficar fora do SSR (ver mapa.md decisão 6).
const MapaLeaflet = dynamic(() => import("./MapaLeaflet").then((m) => m.MapaLeaflet), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-gray-400">
      Carregando mapa…
    </div>
  ),
});

type MapaClientProps = {
  kpisIniciais: KpisNacionais;
  ufInicial: string;
  municipiosIniciais: MunicipioResumo[];
  rankingInicial: RankingUf;
};

export function MapaClient({
  kpisIniciais,
  ufInicial,
  municipiosIniciais,
  rankingInicial,
}: MapaClientProps) {
  const [ufSigla, setUfSigla] = useState(ufInicial);
  const [municipios, setMunicipios] = useState(municipiosIniciais);
  const [ranking, setRanking] = useState(rankingInicial);
  const [municipioAtivo, setMunicipioAtivo] = useState<number | null>(null);
  const [focoSolicitado, setFocoSolicitado] = useState<FocoSolicitado | null>(null);
  const nonceRef = useRef(0);

  const uf = getUfPorSigla(ufSigla);
  const municipioFocadoObjeto =
    municipios.find((m) => m.codigoIbge === municipioAtivo) ?? null;

  async function mudarUf(sigla: string) {
    setUfSigla(sigla);
    setMunicipioAtivo(null);
    setFocoSolicitado(null);
    const [novosMunicipios, novoRanking] = await Promise.all([
      getMunicipiosPorUf(sigla),
      getRankingPorUf(sigla),
    ]);
    setMunicipios(novosMunicipios);
    setRanking(novoRanking);
  }

  function focarMunicipio(codigoIbge: number) {
    nonceRef.current += 1;
    setMunicipioAtivo(codigoIbge);
    setFocoSolicitado({ codigoIbge, nonce: nonceRef.current });
  }

  if (!uf) return null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <KpiStrip kpis={kpisIniciais} />
      <div className="grid min-h-0 flex-1 grid-cols-[1fr_300px] overflow-hidden">
        <div className="flex flex-col overflow-hidden border-r border-gray-200">
          <MapaToolbar
            ufSelecionada={ufSigla}
            municipios={municipios}
            municipioFocado={municipioFocadoObjeto}
            onMudarUf={mudarUf}
            onSelecionarMunicipio={focarMunicipio}
          />
          <div className="relative flex-1 overflow-hidden">
            <MapaLeaflet
              uf={uf}
              municipios={municipios}
              focoSolicitado={focoSolicitado}
              onFocarMunicipio={focarMunicipio}
            />
            <LegendaScore />
          </div>
        </div>
        <RankingPanel
          ufNome={uf.nome}
          ranking={ranking}
          municipioFocado={municipioAtivo}
          onFocarMunicipio={focarMunicipio}
        />
      </div>
    </div>
  );
}
