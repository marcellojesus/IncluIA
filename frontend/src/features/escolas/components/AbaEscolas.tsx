"use client";

// Ver interface.md §6 — composição completa da aba Escolas.
import { useEffect, useState } from "react";

import { getEscolasPorMunicipio } from "../api";
import type { Escola } from "../types";
import { ListaEscolas } from "./ListaEscolas";
import { ModalEscola } from "./ModalEscola";

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
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-end gap-2">
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value as Filtro)}
          className="rounded-lg border border-gray-300 bg-paper px-2.5 py-1.5 text-xs font-semibold text-gov-blue-dark"
        >
          <option value="">Todas as escolas</option>
          <option value="critica">Situação crítica</option>
          <option value="sem-aee">Sem AEE</option>
        </select>
        <button
          disabled
          title="Disponível em uma fase futura"
          className="cursor-not-allowed rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-400"
        >
          📄 Exportar (em breve)
        </button>
      </div>

      <ListaEscolas escolas={escolasFiltradas} onSelecionar={setEscolaSelecionada} />

      {escolaSelecionada && (
        <ModalEscola escola={escolaSelecionada} onFechar={() => setEscolaSelecionada(null)} />
      )}
    </div>
  );
}
