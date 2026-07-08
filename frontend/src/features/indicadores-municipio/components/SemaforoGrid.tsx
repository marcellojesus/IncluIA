// Grade dos "4 compromissos da lei" (eixos I–IV da PNEEI). Status/cor vêm prontos do backend
// (RN-01 de docs/business-rules/indicadores-municipio.md — nunca recalculado no cliente).
import type { EixoIndicador, StatusEixo } from "../types";

const ESTILO_POR_STATUS: Record<StatusEixo, { borda: string; texto: string; chip: string; chipTexto: string }> = {
  ok: { borda: "border-t-gov-green", texto: "text-gov-green", chip: "bg-green-50", chipTexto: "No caminho" },
  warn: { borda: "border-t-gov-orange", texto: "text-gov-orange", chip: "bg-orange-50", chipTexto: "Atenção" },
  nok: { borda: "border-t-gov-red", texto: "text-gov-red", chip: "bg-red-50", chipTexto: "Crítico" },
};

export function SemaforoGrid({ eixos }: { eixos: EixoIndicador[] }) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {eixos.map((eixo, i) => {
        const estilo = ESTILO_POR_STATUS[eixo.status];
        return (
          <div
            key={eixo.label}
            className={`rounded-2xl border-t-4 bg-paper p-4 shadow-sm ${estilo.borda}`}
          >
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[10px] font-extrabold uppercase tracking-wide text-gray-400">
                Eixo {["I", "II", "III", "IV"][i]}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-extrabold ${estilo.chip} ${estilo.texto}`}>
                {estilo.chipTexto}
              </span>
            </div>
            <div className="mb-2 text-sm font-bold leading-tight text-gov-blue-dark">
              {eixo.label}
            </div>
            <div className={`text-2xl font-extrabold ${estilo.texto}`}>{eixo.valor}</div>
            <div className="mt-0.5 text-[11px] text-gray-400">{eixo.subtexto}</div>
          </div>
        );
      })}
    </div>
  );
}
