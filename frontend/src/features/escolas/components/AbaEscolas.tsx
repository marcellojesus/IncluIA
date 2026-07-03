"use client";

// Ver interface.md §6 — composição completa da aba Escolas.
import { useEffect, useState } from "react";

import { getEscolasPorMunicipio } from "../api";
import type { Escola } from "../types";
import { LegendaIconesEscola } from "./LegendaIconesEscola";
import { ModalEscola } from "./ModalEscola";
import { TabelaEscolas } from "./TabelaEscolas";

type Filtro = "" | "critica" | "sem-aee";

// RN-03 de docs/business-rules/escolas.md: filtros mutuamente exclusivos, sem combinação.
function aplicarFiltro(escolas: Escola[], filtro: Filtro): Escola[] {
  if (filtro === "critica") return escolas.filter((e) => e.score < 3);
  if (filtro === "sem-aee") return escolas.filter((e) => e.statusEixoI === "nok");
  return escolas;
}

export function AbaEscolas({ codigoIbge }: { codigoIbge: number }) {
  const [escolas, setEscolas] = useState<Escola[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("");
  const [escolaSelecionada, setEscolaSelecionada] = useState<Escola | null>(null);

  useEffect(() => {
    getEscolasPorMunicipio(codigoIbge)
      .then(setEscolas)
      .catch(() => setErro("Não foi possível carregar as escolas deste município."));
  }, [codigoIbge]);

  if (erro) {
    return <p className="p-5 text-sm text-gov-red">{erro}</p>;
  }
  if (!escolas) {
    return <p className="p-5 text-sm text-gray-400">Carregando escolas…</p>;
  }

  const escolasFiltradas = aplicarFiltro(escolas, filtro);

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-400">
          Score e situação de cada escola nos eixos da PNEEI (Decreto 12.686/2025).
        </p>
        <div className="flex gap-2">
          <select
            value={filtro}
            onChange={(e) => setFiltro(e.target.value as Filtro)}
            className="rounded border border-gray-300 px-2 py-1 text-xs"
          >
            <option value="">Todas as escolas</option>
            <option value="critica">Situação crítica</option>
            <option value="sem-aee">Sem AEE</option>
          </select>
          <button
            disabled
            title="Disponível em uma fase futura"
            className="cursor-not-allowed rounded border border-gray-300 px-3 py-1 text-xs text-gray-400"
          >
            📄 Exportar (em breve)
          </button>
        </div>
      </div>

      <LegendaIconesEscola />

      <TabelaEscolas escolas={escolasFiltradas} onSelecionar={setEscolaSelecionada} />

      {escolaSelecionada && (
        <ModalEscola escola={escolaSelecionada} onFechar={() => setEscolaSelecionada(null)} />
      )}
    </div>
  );
}
