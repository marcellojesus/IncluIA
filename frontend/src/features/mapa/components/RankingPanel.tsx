// Ver interface.md §3.3 "Painel de Ranking".

import { formatarScore } from "@/shared/lib/score";
import type { MunicipioRanking, RankingUf } from "../types";

type RankingPanelProps = {
  ufNome: string;
  ranking: RankingUf;
  municipioFocado: number | null;
  onFocarMunicipio: (codigoIbge: number) => void;
};

function ItemRanking({
  municipio,
  posicao,
  ativo,
  onClick,
}: {
  municipio: MunicipioRanking;
  posicao: number;
  ativo: boolean;
  onClick: () => void;
}) {
  const percentual = Math.max(0, Math.min(100, (municipio.score / 10) * 100));
  return (
    <div
      onClick={onClick}
      className={`flex cursor-pointer items-center gap-2 border-b border-gray-100 px-4 py-2 hover:bg-gov-blue-lt ${
        ativo ? "bg-gov-blue-lt" : ""
      }`}
    >
      <div
        className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
        style={{ backgroundColor: `${municipio.cor}22`, color: municipio.cor }}
      >
        {posicao}
      </div>
      <span className="flex-1 truncate text-sm">{municipio.nome}</span>
      <div className="h-1 w-12 rounded bg-gray-200">
        <div
          className="h-1 rounded"
          style={{ width: `${percentual}%`, backgroundColor: municipio.cor }}
        />
      </div>
      <span className="w-8 text-right text-sm font-bold" style={{ color: municipio.cor }}>
        {formatarScore(municipio.score)}
      </span>
    </div>
  );
}

export function RankingPanel({
  ufNome,
  ranking,
  municipioFocado,
  onFocarMunicipio,
}: RankingPanelProps) {
  return (
    <div className="flex min-h-0 flex-col overflow-hidden bg-white">
      <div className="flex-shrink-0 border-b border-gray-200 px-4 py-2">
        <span className="text-sm font-bold text-gov-blue-dark">Ranking — {ufNome}</span>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="px-4 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wide text-gray-400">
          🏆 Melhores
        </div>
        {ranking.melhores.map((m) => (
          <ItemRanking
            key={m.codigoIbge}
            municipio={m}
            posicao={m.rankingNoEstado}
            ativo={municipioFocado === m.codigoIbge}
            onClick={() => onFocarMunicipio(m.codigoIbge)}
          />
        ))}

        {ranking.criticos.length > 0 && (
          <>
            <div className="px-4 pb-1 pt-3 text-[10px] font-bold uppercase tracking-wide text-gray-400">
              ⚠️ Críticos (Score &lt; 3,0)
            </div>
            {ranking.criticos.map((m) => (
              <ItemRanking
                key={m.codigoIbge}
                municipio={m}
                posicao={m.rankingNoEstado}
                ativo={municipioFocado === m.codigoIbge}
                onClick={() => onFocarMunicipio(m.codigoIbge)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
