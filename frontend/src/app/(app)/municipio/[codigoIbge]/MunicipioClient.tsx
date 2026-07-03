"use client";

// Casca da tela de município — ver interface.md §4. As 3 abas (Indicadores, Escolas,
// Diagnóstico IA) têm conteúdo real. RN-06 de docs/business-rules/login.md: só a aba
// Diagnóstico IA exige login — Indicadores e Escolas são públicas.
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AbaDiagnosticoIA } from "@/features/diagnostico-ia/components/AbaDiagnosticoIA";
import { AbaEscolas } from "@/features/escolas/components/AbaEscolas";
import { AbaIndicadores } from "@/features/indicadores-municipio/components/AbaIndicadores";
import type { MunicipioDetalhe } from "@/features/indicadores-municipio/types";
import { AbaMunicipio, ContextoMunicipioBar } from "@/shared/components/ContextoMunicipioBar";
import { useAppStore } from "@/shared/store/useAppStore";

function linkLoginParaDiagnostico(codigoIbge: number): string {
  return `/login?redirect=${encodeURIComponent(`/municipio/${codigoIbge}?aba=diagnostico`)}`;
}

export function MunicipioClient({
  municipio,
  abaInicial,
}: {
  municipio: MunicipioDetalhe;
  abaInicial?: AbaMunicipio;
}) {
  const router = useRouter();
  const usuario = useAppStore((s) => s.usuario);
  const precisaLoginParaAbaInicial = abaInicial === "diagnostico" && !usuario;
  const [abaAtiva, setAbaAtiva] = useState<AbaMunicipio>(
    precisaLoginParaAbaInicial ? "indicadores" : (abaInicial ?? "indicadores"),
  );

  // Alguém chegou direto em ?aba=diagnostico (link salvo, digitado à mão) sem estar logado —
  // manda para o login em vez de silenciosamente cair em "indicadores".
  useEffect(() => {
    if (precisaLoginParaAbaInicial) {
      router.replace(linkLoginParaDiagnostico(municipio.codigoIbge));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // RF-07 de docs/requirements/mapa.md: tenta manter a UF de origem usando o histórico do
  // navegador em vez de um link fixo para /mapa (que sempre voltaria à UF padrão).
  function voltarAoMapa() {
    router.back();
  }

  function tentarMudarAba(aba: AbaMunicipio) {
    if (aba === "diagnostico" && !usuario) {
      router.push(linkLoginParaDiagnostico(municipio.codigoIbge));
      return;
    }
    setAbaAtiva(aba);
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <ContextoMunicipioBar
        nome={municipio.nome}
        uf={municipio.uf}
        score={municipio.score}
        faixa={municipio.faixa}
        cor={municipio.cor}
        abaAtiva={abaAtiva}
        onMudarAba={tentarMudarAba}
        onVoltar={voltarAoMapa}
      />

      {/* min-h-0: mesmo motivo do (app)/layout.tsx — sem isso, abas com conteúdo mais alto que
          a tela (ex.: tabela do Decreto com muitas linhas) ficam cortadas em vez de rolar. */}
      <div className="min-h-0 flex-1 overflow-hidden bg-gray-50">
        {abaAtiva === "indicadores" && <AbaIndicadores municipio={municipio} />}
        {abaAtiva === "escolas" && <AbaEscolas codigoIbge={municipio.codigoIbge} />}
        {abaAtiva === "diagnostico" && <AbaDiagnosticoIA codigoIbge={municipio.codigoIbge} />}
      </div>
    </div>
  );
}
