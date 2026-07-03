// Ver interface.md §3.1 "Faixa de KPIs nacionais".

import { Kpi } from "@/shared/components/Kpi";
import { formatarNumero } from "@/shared/lib/formatters";
import { formatarScore } from "@/shared/lib/score";
import type { KpisNacionais } from "../types";

export function KpiStrip({ kpis }: { kpis: KpisNacionais }) {
  return (
    <div className="grid flex-shrink-0 grid-cols-5 divide-x divide-gray-200 border-b border-gray-200 bg-white">
      <Kpi
        rotulo="Municípios Críticos"
        valor={formatarNumero(kpis.municipiosCriticos)}
        subtitulo="Score < 3,0 · Brasil"
        cor="vermelho"
      />
      <Kpi
        rotulo="Escolas sem AEE"
        valor={formatarNumero(kpis.escolasSemAee)}
        subtitulo="Sem atendimento educacional especializado"
        cor="laranja"
      />
      <Kpi
        rotulo="Score Médio Nacional"
        valor={formatarScore(kpis.scoreMedioNacional)}
        subtitulo="Escala 0–10 · IncluIA"
      />
      <Kpi
        rotulo="Score Desejado"
        valor={formatarScore(kpis.scoreDesejado)}
        subtitulo="Limiar da faixa Adequado"
      />
      <Kpi
        rotulo="Municípios Mapeados"
        valor={formatarNumero(kpis.municipiosMapeados)}
        subtitulo="Censo Escolar 2025"
        cor="verde"
      />
    </div>
  );
}
