"use client";

// Ranking nacional dos estados (endpoint /ranking-nacional, score agregado por UF) exibido na
// home do município — mostra os 6 primeiros e, se o estado do município atual não estiver
// entre eles, acrescenta uma 7ª linha destacada com a posição real dele. Layout replica o
// protótipo de referência: título grande + link "Ver ranking completo" na mesma linha, cartão
// com as linhas por baixo (não usa o Panel genérico, que tem um cabeçalho pequeno demais aqui).
import Link from "next/link";
import { useEffect, useState } from "react";

import { getRankingNacional } from "@/features/mapa/api";
import { getUfPorSigla } from "@/features/mapa/lib/ufs";
import type { UfRanking } from "@/features/mapa/types";
import { BarraScore } from "@/shared/components/BarraScore";

const QTD_EXIBIDA = 6;

export function RankingEstados({ ufAtual }: { ufAtual: string }) {
  const [ranking, setRanking] = useState<UfRanking[] | null>(null);

  useEffect(() => {
    getRankingNacional()
      .then(setRanking)
      .catch(() => setRanking([]));
  }, []);

  const nomeAtual = getUfPorSigla(ufAtual)?.nome ?? ufAtual;
  const top = ranking?.slice(0, QTD_EXIBIDA) ?? [];
  const estadoAtual = ranking?.find((r) => r.sigla === ufAtual);
  const estadoAtualForaDoTop = estadoAtual && !top.some((r) => r.sigla === ufAtual);
  const linhas = estadoAtualForaDoTop ? [...top, estadoAtual] : top;

  return (
    <section>
      <div className="mb-3.5 flex items-baseline justify-between">
        <h2 className="text-xl font-extrabold text-gov-blue-dark">Como {nomeAtual} se compara</h2>
        <Link href="/comparar" className="text-sm font-bold text-gov-blue hover:underline">
          Ver ranking completo →
        </Link>
      </div>

      <div className="overflow-hidden rounded-2xl bg-paper shadow-sm">
        {!ranking && <p className="p-4 text-sm text-gray-400">Carregando…</p>}
        {ranking?.length === 0 && <p className="p-4 text-sm text-gray-400">Sem dados de ranking nacional.</p>}
        <div className="flex flex-col px-4">
          {linhas.map((r, i) => (
            <div key={r.sigla}>
              {estadoAtualForaDoTop && i === linhas.length - 1 && (
                <div className="border-t border-dashed border-gray-200" />
              )}
              <div
                className={`flex items-center gap-4 py-3 text-sm ${
                  r.sigla === ufAtual
                    ? "-mx-4 rounded-xl bg-gov-blue-lt/40 px-4"
                    : i === linhas.length - 1
                      ? ""
                      : "border-b border-gray-200"
                }`}
              >
                <span className="w-7 shrink-0 text-base font-extrabold text-gray-400">{r.rankingNacional}º</span>
                <span
                  className={`flex-1 truncate ${
                    r.sigla === ufAtual ? "font-extrabold text-gov-blue-dark" : "text-gray-700"
                  }`}
                >
                  {getUfPorSigla(r.sigla)?.nome ?? r.sigla}
                  {r.sigla === ufAtual && (
                    <span className="ml-1.5 rounded-full bg-gov-blue-lt px-2 py-0.5 text-[10px] font-extrabold text-gov-blue">
                      você
                    </span>
                  )}
                </span>
                <BarraScore score={r.score} cor={r.cor} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
