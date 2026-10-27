"use client";

// Barreiras da escola identificadas no Censo (impacto-fase-1.md PUB-01; metodologia_barreiras.md).
// São dado observado, não relato da escola: o relato, quando publicado, vem na Declaração logo abaixo.
import Link from "next/link";
import { useEffect, useState } from "react";

import { type BarreirasDaEscola, getBarreirasDaEscola } from "../api";

const pontos = (valor: number) => valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 });

export function BarreirasEscola({ coEntidade }: { coEntidade: number }) {
  const [dados, setDados] = useState<BarreirasDaEscola | null | undefined>(undefined);

  useEffect(() => {
    let ativo = true;
    getBarreirasDaEscola(coEntidade)
      .then((resposta) => ativo && setDados(resposta))
      .catch(() => ativo && setDados(null));
    return () => {
      ativo = false;
    };
  }, [coEntidade]);

  if (!dados) return null;

  return (
    <section className="mt-5 border-t border-gray-100 pt-4" aria-labelledby={`barreiras-${coEntidade}`}>
      <div className="flex items-center justify-between gap-2">
        <h3 id={`barreiras-${coEntidade}`} className="text-[13px] font-bold text-gov-blue-dark">Barreiras identificadas no Censo</h3>
        <span className="rounded-full bg-black/[.05] px-2.5 py-0.5 text-[11px] font-bold text-gray-600">
          {dados.barreiras.length} · Censo {dados.censoVersao}
        </span>
      </div>
      {dados.barreiras.length === 0 ? (
        <p className="mt-2 text-[12px] text-gray-600">O Censo {dados.censoVersao} não indica barreiras para esta escola.</p>
      ) : (
        <ul className="mt-2 divide-y divide-gray-100">
          {dados.barreiras.map((b) => (
            <li key={b.codigo} className="py-2">
              <div className="flex items-start justify-between gap-3">
                <span className="text-[13px] font-semibold text-gray-800">
                  <span className="mr-1.5 text-[11px] font-bold text-gray-400">Eixo {b.eixo}</span>
                  {b.nome}
                </span>
                {b.pontos !== null && <span className="shrink-0 text-[11px] text-gray-500">{pontos(b.pontos)} pts</span>}
              </div>
              <p className="mt-0.5 text-[12px] text-gray-600">{b.dadoCenso}</p>
              {b.nota && <p className="mt-0.5 text-[11px] text-gray-500">Nota: {b.nota}.</p>}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-[11px] text-gray-500">
        Dado do Censo Escolar, pela{" "}
        <Link href="/metodologia/barreiras" className="font-semibold text-gov-blue underline underline-offset-2">
          metodologia de barreiras v{dados.metodologiaVersao}
        </Link>
        . A escola pode explicar cada barreira na Declaração de Obstáculos.
      </p>
    </section>
  );
}
