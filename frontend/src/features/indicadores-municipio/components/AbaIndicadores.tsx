// Ver interface.md §5 — composição completa da aba Indicadores.
import type { MunicipioDetalhe } from "../types";
import { DadosGeraisPanel } from "./DadosGeraisPanel";
import { ScoreEixoPanel } from "./ScoreEixoPanel";
import { SemaforoGrid } from "./SemaforoGrid";
import { TabelaDecretoPanel } from "./TabelaDecretoPanel";

export function AbaIndicadores({ municipio }: { municipio: MunicipioDetalhe }) {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-5">
      <p className="text-xs text-gray-400">
        Situação em relação aos <strong>4 eixos da PNEEI (Decreto 12.686/2025)</strong>.
      </p>

      <SemaforoGrid eixos={municipio.eixos} />

      <div className="grid grid-cols-2 gap-4">
        <ScoreEixoPanel scoreEixos={municipio.scoreEixos} />
        <DadosGeraisPanel dadosGerais={municipio.dadosGerais} />
      </div>

      <TabelaDecretoPanel criterios={municipio.detalhamentoDecreto} />
    </div>
  );
}
