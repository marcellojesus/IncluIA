"use client";

// Ver interface.md §3.2 "Painel do mapa" — replica loadGeoJSON/abrirPopup/focusMuni do protótipo.
// Importar o CSS do Leaflet aqui é o padrão suportado pelo Next.js App Router para CSS de
// pacotes de terceiros usados só num componente cliente específico.
import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";

import { formatarScore } from "@/shared/lib/score";
import { fetchGeoJsonUf } from "../lib/ibge";
import type { Uf } from "../lib/ufs";
import type { MunicipioResumo } from "../types";

export type FocoSolicitado = {
  codigoIbge: number;
  nonce: number;
};

type EstadoCarga = {
  carregando: boolean;
  erro: string | null;
};

type CamadaMunicipiosProps = {
  uf: Uf;
  municipiosPorCodigo: Record<number, MunicipioResumo>;
  focoSolicitado: FocoSolicitado | null;
  onFocarMunicipio: (codigoIbge: number) => void;
  onEstadoChange: (estado: EstadoCarga) => void;
};

function construirPopup(municipio: MunicipioResumo, router: ReturnType<typeof useRouter>) {
  const container = document.createElement("div");
  container.className = "text-sm";
  container.innerHTML = `
    <div class="font-bold text-gov-blue-dark">${municipio.nome}</div>
    <div class="mb-2 text-xs text-gray-400">${municipio.uf}</div>
    <div class="mb-2 flex items-baseline gap-2">
      <span class="text-2xl font-bold" style="color:${municipio.cor}">${formatarScore(municipio.score)}</span>
      <span class="text-xs text-gray-400">Score Escola Sem Barreiras</span>
    </div>
    <span class="inline-block rounded-full px-2 py-0.5 text-xs font-bold" style="background:${municipio.cor}22;color:${municipio.cor}">${municipio.faixa}</span>
  `;
  const botao = document.createElement("button");
  botao.className = "mt-2 block w-full rounded bg-gov-blue px-3 py-2 text-xs font-bold text-white";
  botao.textContent = "Ver indicadores do município →";
  botao.addEventListener("click", () => router.push(`/municipio/${municipio.codigoIbge}`));
  container.appendChild(botao);
  return container;
}

function CamadaMunicipios({
  uf,
  municipiosPorCodigo,
  focoSolicitado,
  onFocarMunicipio,
  onEstadoChange,
}: CamadaMunicipiosProps) {
  const map = useMap();
  const router = useRouter();
  const layersRef = useRef<Record<number, L.Polygon>>({});
  const geoJsonRef = useRef<L.GeoJSON | null>(null);
  // Guardado com a UF de origem: ao trocar de UF, o mapa anterior some sem setState dentro do efeito.
  const [carregado, setCarregado] = useState<{ uf: number; dados: GeoJSON.FeatureCollection } | null>(null);
  const geojson = carregado?.uf === uf.codigoIbge ? carregado.dados : null;

  useEffect(() => {
    let cancelado = false;
    layersRef.current = {};
    onEstadoChange({ carregando: true, erro: null });

    fetchGeoJsonUf(uf.codigoIbge)
      .then((data) => {
        if (cancelado) return;
        setCarregado({ uf: uf.codigoIbge, dados: data });
        onEstadoChange({ carregando: false, erro: null });
      })
      .catch(() => {
        if (cancelado) return;
        onEstadoChange({ carregando: false, erro: "Erro ao carregar mapa IBGE." });
      });

    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uf.codigoIbge]);

  useEffect(() => {
    if (!focoSolicitado) return;
    const layer = layersRef.current[focoSolicitado.codigoIbge];
    const municipio = municipiosPorCodigo[focoSolicitado.codigoIbge];
    if (!layer || !municipio) return;
    map.fitBounds(layer.getBounds(), { maxZoom: 11, padding: [40, 40] });
    layer.bindPopup(construirPopup(municipio, router), { maxWidth: 240 }).openPopup();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focoSolicitado]);

  if (!geojson) return null;

  return (
    <GeoJSON
      key={uf.codigoIbge}
      ref={geoJsonRef}
      data={geojson}
      style={(feature) => {
        const codigo = Number(feature?.properties?.codarea);
        const municipio = municipiosPorCodigo[codigo];
        return {
          fillColor: municipio?.cor ?? "#999999",
          fillOpacity: 0.65,
          color: "#fff",
          weight: 0.8,
        };
      }}
      onEachFeature={(feature, layer) => {
        const codigo = Number(feature.properties?.codarea);
        layersRef.current[codigo] = layer as L.Polygon;
        layer.on({
          mouseover: (e) => {
            (e.target as L.Path).setStyle({ weight: 2, color: "#071d41", fillOpacity: 0.88 });
            (e.target as L.Polygon).bringToFront();
          },
          mouseout: (e) => {
            geoJsonRef.current?.resetStyle(e.target);
          },
          click: () => onFocarMunicipio(codigo),
        });
      }}
      eventHandlers={{
        add: (e) => {
          try {
            map.fitBounds((e.target as L.GeoJSON).getBounds(), { padding: [10, 10] });
          } catch {
            // UF sem geometria carregada ainda — ignora.
          }
        },
      }}
    />
  );
}

type MapaLeafletProps = {
  uf: Uf;
  municipios: MunicipioResumo[];
  focoSolicitado: FocoSolicitado | null;
  onFocarMunicipio: (codigoIbge: number) => void;
};

export function MapaLeaflet({ uf, municipios, focoSolicitado, onFocarMunicipio }: MapaLeafletProps) {
  const municipiosPorCodigo = useMemo(
    () => Object.fromEntries(municipios.map((m) => [m.codigoIbge, m])),
    [municipios],
  );
  const [estadoCarga, setEstadoCarga] = useState<EstadoCarga>({ carregando: true, erro: null });

  return (
    <div className="relative h-full w-full">
      <MapContainer center={[-15, -55]} zoom={4} className="h-full w-full" zoomControl>
        <TileLayer
          attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={18}
        />
        <CamadaMunicipios
          uf={uf}
          municipiosPorCodigo={municipiosPorCodigo}
          focoSolicitado={focoSolicitado}
          onFocarMunicipio={onFocarMunicipio}
          onEstadoChange={setEstadoCarga}
        />
      </MapContainer>

      {estadoCarga.carregando && (
        <div className="absolute inset-0 z-[999] flex items-center justify-center bg-white/70">
          <div className="rounded bg-white px-6 py-4 text-sm text-gray-600 shadow">
            Carregando mapa IBGE…
          </div>
        </div>
      )}
      {estadoCarga.erro && (
        <div className="absolute inset-0 z-[999] flex items-center justify-center bg-white/70">
          <div className="rounded bg-white px-6 py-4 text-sm text-red-600 shadow">
            ⚠️ {estadoCarga.erro}
          </div>
        </div>
      )}
    </div>
  );
}
