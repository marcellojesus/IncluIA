"use client";

// Só a tela de Diagnóstico IA exige login. Se alguém chega direto em /municipio/x/diagnostico
// sem estar autenticado (link salvo, digitado à mão), manda para o login em vez de deixar a
// chamada à API estourar 401 primeiro.
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { AbaDiagnosticoIA } from "@/features/diagnostico-ia/components/AbaDiagnosticoIA";
import { useAppStore } from "@/shared/store/useAppStore";

export function DiagnosticoClient({ codigoIbge, nome }: { codigoIbge: number; nome: string }) {
  const router = useRouter();
  const usuario = useAppStore((s) => s.usuario);

  useEffect(() => {
    if (!usuario) {
      router.replace(`/login?redirect=${encodeURIComponent(`/municipio/${codigoIbge}/diagnostico`)}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usuario]);

  if (!usuario) return null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-extrabold text-gov-blue-dark">
        Diagnóstico com IA · {nome}
      </h1>
      <p className="mb-5 text-sm text-gray-500">
        A IA lê os dados do Censo Escolar do INEP e gera uma análise por eixo da PNEEI.
      </p>
      <AbaDiagnosticoIA codigoIbge={codigoIbge} />
    </div>
  );
}
