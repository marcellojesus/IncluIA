// Ver interface.md §3.2 "Legenda do Score Escola Sem Barreiras" — explica as cores do mapa coroplético.
// Reaproveita a mesma classificação usada em todo o produto (RN-02 de docs/business-rules/mapa.md).
import { FAIXAS } from "@/shared/lib/score";

export function LegendaScore() {
  const faixasEmOrdem = [...FAIXAS].reverse(); // Crítico -> Referência (leitura natural)

  return (
    <div className="absolute bottom-3 left-3 z-[900] rounded bg-white/95 px-3 py-2 shadow-md">
      <div className="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-gray-400">
        Score Escola Sem Barreiras
      </div>
      <div className="flex flex-col gap-1">
        {faixasEmOrdem.map((f) => (
          <div key={f.faixa} className="flex items-center gap-1.5 text-xs text-gray-600">
            <span className="h-2.5 w-2.5 flex-shrink-0 rounded-sm" style={{ backgroundColor: f.cor }} />
            {f.faixa}
          </div>
        ))}
      </div>
    </div>
  );
}
