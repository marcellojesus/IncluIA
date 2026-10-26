"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { DeclaracaoObstaculos } from "@/features/gestao-ativa/components/DeclaracaoObstaculos";

function Conteudo() {
  // ?eixo=II registra só um eixo (atalho dos cartões do dashboard); sem ele, todos os eixos.
  const eixo = useSearchParams().get("eixo");
  return <DeclaracaoObstaculos eixo={eixo && ["I", "II", "III", "IV"].includes(eixo) ? eixo : null} />;
}

export default function DeclaracaoPage() {
  return (
    <AreaRestrita papel="diretor">
      {() => (
        <Suspense>
          <Conteudo />
        </Suspense>
      )}
    </AreaRestrita>
  );
}
