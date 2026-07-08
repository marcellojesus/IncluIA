"use client";

// Tela "Comparar": alterna entre ranking nacional de estados (novo — GET /ranking-nacional) e
// ranking de municípios dentro de um estado escolhido (reaproveita GET /uf/{uf}/municipios,
// já usado no GeoFiltroBar/Mapa). Antes era um placeholder (PaginaEmConstrucao); agora é real.
import { useEffect, useState } from "react";

import { getMunicipiosPorUf, getRankingNacional } from "@/features/mapa/api";
import { getUfPorSigla, UFS } from "@/features/mapa/lib/ufs";
import type { MunicipioResumo, UfRanking } from "@/features/mapa/types";
import { BarraScore } from "@/shared/components/BarraScore";
import { useAppStore } from "@/shared/store/useAppStore";

type Modo = "estados" | "municipios";

export function CompararView() {
  const [modo, setModo] = useState<Modo>("estados");
  const municipioSelecionado = useAppStore((s) => s.municipioSelecionado);

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-extrabold text-gov-blue-dark">Comparar</h1>
      <p className="mb-5 text-sm text-gray-500">
        Ranking pelo índice de inclusão, com base no Censo Escolar. Compare estados entre si ou
        municípios dentro de um estado.
      </p>

      <div className="mb-5 inline-flex rounded-full bg-[#eef1ec] p-1">
        <button
          type="button"
          onClick={() => setModo("estados")}
          className={`rounded-full px-4 py-1.5 text-sm font-bold transition-colors ${
            modo === "estados" ? "bg-paper text-gov-blue-dark shadow-sm" : "text-gray-500"
          }`}
        >
          Ranking de Estados
        </button>
        <button
          type="button"
          onClick={() => setModo("municipios")}
          className={`rounded-full px-4 py-1.5 text-sm font-bold transition-colors ${
            modo === "municipios" ? "bg-paper text-gov-blue-dark shadow-sm" : "text-gray-500"
          }`}
        >
          Ranking de Municípios
        </button>
      </div>

      {modo === "estados" ? (
        <RankingEstadosTabela ufAtual={municipioSelecionado?.uf} />
      ) : (
        <RankingMunicipiosTabela
          ufInicial={municipioSelecionado?.uf ?? "DF"}
          codigoIbgeAtual={municipioSelecionado?.codigoIbge}
        />
      )}
    </div>
  );
}

// A última coluna (índice/score) é mais larga porque exibe a barra de progresso + número
// (ver BarraScore); colunas numéricas intermediárias (ex.: "Municípios") ficam estreitas.
function LinhaCabecalho({ colunas }: { colunas: string[] }) {
  const intermediarias = colunas.slice(2, -1).map(() => "96px");
  return (
    <div
      className="grid items-center gap-3 border-b border-gray-100 bg-[#f0ece2] px-4 py-2.5 text-[11px] font-extrabold uppercase tracking-wide text-gray-400"
      style={{ gridTemplateColumns: `48px 1fr ${[...intermediarias, "210px"].join(" ")}` }}
    >
      {colunas.map((c) => (
        <span key={c} className={c === colunas[0] || c === colunas[1] ? "" : "text-right"}>
          {c}
        </span>
      ))}
    </div>
  );
}

function RankingEstadosTabela({ ufAtual }: { ufAtual?: string }) {
  const [ranking, setRanking] = useState<UfRanking[] | null>(null);

  useEffect(() => {
    getRankingNacional()
      .then(setRanking)
      .catch(() => setRanking([]));
  }, []);

  if (!ranking) return <p className="text-sm text-gray-400">Carregando…</p>;
  if (ranking.length === 0) return <p className="text-sm text-gray-400">Sem dados de ranking nacional.</p>;

  return (
    <div className="overflow-hidden rounded-2xl bg-paper shadow-sm">
      <LinhaCabecalho colunas={["#", "Estado", "Municípios", "Índice"]} />
      {ranking.map((r) => (
        <div
          key={r.sigla}
          className={`grid items-center gap-3 border-b border-gray-100 px-4 py-2.5 text-sm last:border-none ${
            r.sigla === ufAtual ? "bg-gov-blue-lt/40" : ""
          }`}
          style={{ gridTemplateColumns: "48px 1fr 96px 210px" }}
        >
          <span className="text-xs font-extrabold text-gray-400">{r.rankingNacional}º</span>
          <span className={r.sigla === ufAtual ? "font-extrabold text-gov-blue-dark" : "text-gray-700"}>
            {getUfPorSigla(r.sigla)?.nome ?? r.sigla}
            {r.sigla === ufAtual && (
              <span className="ml-1.5 rounded-full bg-gov-blue-lt px-2 py-0.5 text-[10px] font-extrabold text-gov-blue">
                você
              </span>
            )}
          </span>
          <span className="text-right text-xs text-gray-400">{r.qtdMunicipios}</span>
          <div className="flex justify-end">
            <BarraScore score={r.score} cor={r.cor} />
          </div>
        </div>
      ))}
    </div>
  );
}

function RankingMunicipiosTabela({
  ufInicial,
  codigoIbgeAtual,
}: {
  ufInicial: string;
  codigoIbgeAtual?: number;
}) {
  const [uf, setUf] = useState(ufInicial);
  const [municipios, setMunicipios] = useState<MunicipioResumo[] | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reseta a lista ao trocar de UF, antes da nova busca
    setMunicipios(null);
    getMunicipiosPorUf(uf)
      .then((lista) => setMunicipios([...lista].sort((a, b) => b.score - a.score)))
      .catch(() => setMunicipios([]));
  }, [uf]);

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <label className="text-xs font-extrabold uppercase tracking-wide text-gray-400">Estado:</label>
        <select
          value={uf}
          onChange={(e) => setUf(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-semibold text-gov-blue-dark"
        >
          {UFS.map((u) => (
            <option key={u.sigla} value={u.sigla}>
              {u.nome}
            </option>
          ))}
        </select>
      </div>

      {!municipios && <p className="text-sm text-gray-400">Carregando…</p>}
      {municipios?.length === 0 && <p className="text-sm text-gray-400">Nenhum município encontrado.</p>}
      {municipios && municipios.length > 0 && (
        <div className="overflow-hidden rounded-2xl bg-paper shadow-sm">
          <LinhaCabecalho colunas={["#", "Município", "Índice"]} />
          {municipios.map((m, i) => (
            <div
              key={m.codigoIbge}
              className={`grid items-center gap-3 border-b border-gray-100 px-4 py-2.5 text-sm last:border-none ${
                m.codigoIbge === codigoIbgeAtual ? "bg-gov-blue-lt/40" : ""
              }`}
              style={{ gridTemplateColumns: "48px 1fr 210px" }}
            >
              <span className="text-xs font-extrabold text-gray-400">{i + 1}º</span>
              <span className={m.codigoIbge === codigoIbgeAtual ? "font-extrabold text-gov-blue-dark" : "text-gray-700"}>
                {m.nome}
                {m.codigoIbge === codigoIbgeAtual && (
                  <span className="ml-1.5 rounded-full bg-gov-blue-lt px-2 py-0.5 text-[10px] font-extrabold text-gov-blue">
                    você
                  </span>
                )}
              </span>
              <div className="flex justify-end">
                <BarraScore score={m.score} cor={m.cor} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
