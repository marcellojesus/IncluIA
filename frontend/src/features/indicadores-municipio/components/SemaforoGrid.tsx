// Ver interface.md §5.1 "Grade de Semáforos". Status/cor vêm prontos do backend (RN-01 de
// docs/business-rules/indicadores-municipio.md — nunca recalculado no cliente).
import type { EixoIndicador, StatusEixo } from "../types";

const ESTILO_POR_STATUS: Record<StatusEixo, { fundo: string; borda: string; texto: string }> = {
  ok: { fundo: "bg-green-50", borda: "border-green-200", texto: "text-gov-green" },
  warn: { fundo: "bg-orange-50", borda: "border-orange-200", texto: "text-gov-orange" },
  nok: { fundo: "bg-red-50", borda: "border-red-200", texto: "text-gov-red" },
};

export function SemaforoGrid({ eixos }: { eixos: EixoIndicador[] }) {
  return (
    <div className="mb-4 grid grid-cols-4 gap-3">
      {eixos.map((eixo) => {
        const estilo = ESTILO_POR_STATUS[eixo.status];
        return (
          <div
            key={eixo.label}
            className={`rounded border ${estilo.borda} ${estilo.fundo} p-3.5 shadow-sm`}
          >
            <div className="mb-1.5 text-xl">{eixo.icone}</div>
            <div className={`mb-1 text-[10px] font-bold uppercase tracking-wide ${estilo.texto}`}>
              {eixo.label}
            </div>
            <div className={`text-lg font-bold ${estilo.texto}`}>{eixo.valor}</div>
            <div className="mt-0.5 text-[10px] text-gray-400">{eixo.subtexto}</div>
          </div>
        );
      })}
    </div>
  );
}
