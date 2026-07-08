"use client";

// Mantém useAppStore.municipioSelecionado em dia sempre que uma tela de município é aberta —
// é essa informação que o AppHeader (links de Escolas/Diagnóstico IA) e o GeoFiltroBar (texto
// "Exibindo X · UF") usam para saber qual é o município atual. Não renderiza nada.
import { useEffect } from "react";

import { useAppStore, type MunicipioSelecionado } from "@/shared/store/useAppStore";

export function MunicipioSync({ municipio }: { municipio: MunicipioSelecionado }) {
  const setMunicipioSelecionado = useAppStore((s) => s.setMunicipioSelecionado);

  useEffect(() => {
    setMunicipioSelecionado(municipio);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipio.codigoIbge]);

  return null;
}
