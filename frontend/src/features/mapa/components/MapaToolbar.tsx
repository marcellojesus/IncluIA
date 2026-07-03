// Ver interface.md §3.2 "Toolbar" (seletor de UF + seletor de município + legenda de score).

import { Badge } from "@/shared/components/Badge";
import { formatarScore } from "@/shared/lib/score";
import { UFS } from "../lib/ufs";
import type { MunicipioResumo } from "../types";

type MapaToolbarProps = {
  ufSelecionada: string;
  municipios: MunicipioResumo[];
  municipioFocado: MunicipioResumo | null;
  onMudarUf: (sigla: string) => void;
  onSelecionarMunicipio: (codigoIbge: number) => void;
};

export function MapaToolbar({
  ufSelecionada,
  municipios,
  municipioFocado,
  onMudarUf,
  onSelecionarMunicipio,
}: MapaToolbarProps) {
  const municipiosOrdenados = [...municipios].sort((a, b) => a.nome.localeCompare(b.nome, "pt"));

  return (
    <div className="flex flex-shrink-0 items-center gap-2 border-b border-gray-200 bg-white px-4 py-2 text-sm">
      <span className="font-semibold text-gray-600">Estado:</span>
      <select
        className="rounded border border-gray-300 px-2 py-1"
        value={ufSelecionada}
        onChange={(e) => onMudarUf(e.target.value)}
      >
        {UFS.map((uf) => (
          <option key={uf.sigla} value={uf.sigla}>
            {uf.sigla} — {uf.nome}
          </option>
        ))}
      </select>

      <span className="ml-1 font-semibold text-gray-600">Município:</span>
      <select
        className="min-w-[200px] rounded border border-gray-300 px-2 py-1"
        value={municipioFocado?.codigoIbge ?? ""}
        onChange={(e) => {
          if (e.target.value) onSelecionarMunicipio(Number(e.target.value));
        }}
      >
        <option value="">— selecione —</option>
        {municipiosOrdenados.map((m) => (
          <option key={m.codigoIbge} value={m.codigoIbge}>
            {m.nome}
          </option>
        ))}
      </select>

      {/* RF-11 de docs/requirements/mapa.md: só aparece depois de focar um município (mapa,
          ranking ou este próprio seletor) — RN-08 de docs/business-rules/mapa.md: reaproveita
          score/faixa/cor vindos do backend, nunca recalculado aqui. */}
      {municipioFocado && (
        <span className="flex items-center gap-1.5 text-xs text-gray-500">
          Score do município:
          <Badge texto={formatarScore(municipioFocado.score)} cor={municipioFocado.cor} />
        </span>
      )}

      <span className="ml-auto text-xs text-gray-400">ou clique no mapa</span>
    </div>
  );
}
