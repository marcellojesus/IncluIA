// Ver interface.md §5.2 "Painel Score por Eixo".
import { Panel } from "@/shared/components/Panel";
import type { ScoreEixo } from "../types";

export function ScoreEixoPanel({ scoreEixos }: { scoreEixos: ScoreEixo[] }) {
  return (
    <Panel titulo="Score por Eixo">
      <div className="flex flex-col gap-2.5">
        {scoreEixos.map((eixo) => (
          <div key={eixo.label}>
            <div className="mb-1 flex justify-between text-xs text-gray-500">
              <span>{eixo.label}</span>
              <span className="font-bold" style={{ color: eixo.cor }}>
                {eixo.valor}
              </span>
            </div>
            <div className="h-1.5 rounded bg-gray-200">
              <div
                className="h-1.5 rounded"
                style={{ width: `${eixo.percentual}%`, backgroundColor: eixo.cor }}
              />
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
