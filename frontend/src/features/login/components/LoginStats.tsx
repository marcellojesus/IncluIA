"use client";

// Ver interface.md §2 "3 estatísticas de impacto". Busca os KPIs reais (feature mapa) em vez de
// hardcodar os números do protótipo — mesma fonte de verdade usada na tela de Mapa.
import { useEffect, useState } from "react";

import { getKpisNacionais } from "@/features/mapa/api";
import type { KpisNacionais } from "@/features/mapa/types";
import { formatarCompacto, formatarNumero } from "@/shared/lib/formatters";

export function LoginStats() {
  const [kpis, setKpis] = useState<KpisNacionais | null>(null);

  useEffect(() => {
    getKpisNacionais()
      .then(setKpis)
      .catch(() => setKpis(null));
  }, []);

  const itens = [
    {
      valor: kpis ? formatarCompacto(kpis.totalAlunosEsp) : "—",
      label: "alunos com deficiência matriculados no Brasil",
    },
    {
      valor: kpis ? formatarNumero(kpis.escolasSemAee) : "—",
      label: "escolas sem nenhum AEE registrado no Censo",
    },
    {
      valor: kpis ? formatarNumero(kpis.municipiosMapeados) : "—",
      label: "municípios mapeados com Score IncluIA",
    },
  ];

  return (
    <div className="flex flex-col gap-5">
      {itens.map((item) => (
        <div key={item.label} className="flex items-baseline gap-3 border-l-2 border-white/20 pl-4">
          <div className="flex-shrink-0 text-2xl font-bold text-white">{item.valor}</div>
          <div className="text-sm leading-tight text-white/50">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
