"use client";

// Filtro geográfico em cascata Região → UF → Município, fixo em todas as telas — substitui o
// mapa nacional como forma de navegar entre municípios (ver decisão de produto: mapa removido
// da navegação principal por ora). Ao trocar de município, mantém a subtela atual (Escolas ou
// Diagnóstico IA) quando possível, senão volta para o Início do novo município.
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getMunicipiosPorUf } from "@/features/mapa/api";
import { getUfsPorRegiao, REGIOES, type Regiao } from "@/features/mapa/lib/ufs";
import type { MunicipioResumo } from "@/features/mapa/types";
import { useAppStore } from "@/shared/store/useAppStore";

function subtelaAtual(pathname: string): "" | "/escolas" | "/diagnostico" {
  if (pathname.endsWith("/escolas")) return "/escolas";
  if (pathname.endsWith("/diagnostico")) return "/diagnostico";
  return "";
}

// Telas nacionais, sem escopo de município — o filtro Região→UF→Município não se aplica a elas.
const ROTAS_SEM_FILTRO = ["/dados-abertos"];

export function GeoFiltroBar() {
  const router = useRouter();
  const pathname = usePathname() ?? "";
  const municipioSelecionado = useAppStore((s) => s.municipioSelecionado);

  const [regiao, setRegiao] = useState<Regiao | "todas">("todas");
  const [uf, setUf] = useState("");
  const [municipios, setMunicipios] = useState<MunicipioResumo[]>([]);
  const [carregando, setCarregando] = useState(false);

  // useAppStore.municipioSelecionado só fica pronto depois de duas etapas assíncronas (hidratação
  // do zustand-persist + useEffect do MunicipioSync) — não dá pra confiar no valor inicial do
  // useState acima (rodaria antes de qualquer uma delas). Sincroniza Região/UF sempre que o
  // município selecionado mudar, para os selects nunca ficarem "presos" em branco.
  useEffect(() => {
    if (!municipioSelecionado || municipioSelecionado.uf === uf) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- sincroniza com o store externo (zustand), não deriva de props/state local
    setUf(municipioSelecionado.uf);
    setRegiao(getUfsPorRegiao("todas").find((u) => u.sigla === municipioSelecionado.uf)?.regiao ?? "todas");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipioSelecionado?.uf]);

  useEffect(() => {
    if (!uf) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- estado de carregamento da própria busca abaixo
    setCarregando(true);
    getMunicipiosPorUf(uf)
      .then(setMunicipios)
      .catch(() => setMunicipios([]))
      .finally(() => setCarregando(false));
  }, [uf]);

  const ufsDaRegiao = getUfsPorRegiao(regiao);
  const municipiosOrdenados = [...municipios].sort((a, b) => a.nome.localeCompare(b.nome, "pt"));

  function mudarRegiao(novaRegiao: Regiao | "todas") {
    setRegiao(novaRegiao);
    const primeiraUf = getUfsPorRegiao(novaRegiao)[0]?.sigla ?? "";
    setUf(primeiraUf);
  }

  function irParaMunicipio(codigoIbge: number) {
    router.push(`/municipio/${codigoIbge}${subtelaAtual(pathname)}`);
  }

  if (ROTAS_SEM_FILTRO.includes(pathname)) return null;

  return (
    <div className="flex flex-shrink-0 flex-wrap items-end gap-4 border-b border-black/5 bg-[#eef1ec] px-6 py-3">
      <div className="flex flex-col gap-1">
        <label className="text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
          Região
        </label>
        <select
          value={regiao}
          onChange={(e) => mudarRegiao(e.target.value as Regiao | "todas")}
          className="min-w-[150px] rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gov-blue-dark"
        >
          <option value="todas">Todas as regiões</option>
          {REGIOES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
          Estado (UF)
        </label>
        <select
          value={uf}
          onChange={(e) => setUf(e.target.value)}
          className="min-w-[170px] rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gov-blue-dark"
        >
          <option value="">— selecione —</option>
          {ufsDaRegiao.map((u) => (
            <option key={u.sigla} value={u.sigla}>
              {u.sigla} — {u.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
          Município
        </label>
        <select
          value={municipioSelecionado?.uf === uf ? municipioSelecionado.codigoIbge : ""}
          onChange={(e) => e.target.value && irParaMunicipio(Number(e.target.value))}
          disabled={!uf || carregando}
          className="min-w-[220px] rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gov-blue-dark disabled:opacity-50"
        >
          <option value="">{carregando ? "carregando…" : "— selecione —"}</option>
          {municipiosOrdenados.map((m) => (
            <option key={m.codigoIbge} value={m.codigoIbge}>
              {m.nome}
            </option>
          ))}
        </select>
      </div>

      <div className="ml-auto pb-2 text-xs text-gray-500">
        {municipioSelecionado ? (
          <>
            Exibindo <strong className="text-gov-blue-dark">{municipioSelecionado.nome}</strong> ·{" "}
            {municipioSelecionado.uf}
          </>
        ) : (
          "Selecione um município"
        )}
      </div>
    </div>
  );
}
