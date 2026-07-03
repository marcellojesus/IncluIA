"use client";

// Ver interface.md §7 — composição completa da aba Diagnóstico IA.
import Link from "next/link";
import { useEffect, useState } from "react";

import { Panel } from "@/shared/components/Panel";
import { ErroAutenticacao, getDiagnostico } from "../api";
import type { DiagnosticoEixo, RecomendacaoIA } from "../types";
import { DiagnosticoEixoCard } from "./DiagnosticoEixoCard";

function tempoDecorrido(geradoEm: string): string {
  const minutos = Math.max(0, Math.round((Date.now() - new Date(geradoEm).getTime()) / 60000));
  if (minutos < 1) return "agora mesmo";
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.round(minutos / 60);
  return `há ${horas}h`;
}

export function AbaDiagnosticoIA({ codigoIbge }: { codigoIbge: number }) {
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoEixo[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [precisaLogin, setPrecisaLogin] = useState(false);
  const [gerando, setGerando] = useState(false);

  function carregar(forcar: boolean) {
    setGerando(true);
    setErro(null);
    getDiagnostico(codigoIbge, forcar)
      .then((d) => {
        setDiagnosticos(d);
        setGerando(false);
      })
      .catch((e) => {
        if (e instanceof ErroAutenticacao) {
          setPrecisaLogin(true);
        } else {
          setErro("Não foi possível gerar o diagnóstico agora. Tente novamente em instantes.");
        }
        setGerando(false);
      });
  }

  useEffect(() => {
    carregar(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigoIbge]);

  if (precisaLogin) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-5 text-center">
        <p className="text-sm text-gray-500">
          Sua sessão expirou. Faça login novamente para acessar o Diagnóstico IA.
        </p>
        <Link
          href={`/login?redirect=${encodeURIComponent(`/municipio/${codigoIbge}?aba=diagnostico`)}`}
          className="rounded bg-gov-blue px-4 py-2 text-sm font-bold text-white"
        >
          Fazer login
        </Link>
      </div>
    );
  }

  if (erro) {
    return <p className="p-5 text-sm text-gov-red">{erro}</p>;
  }

  if (!diagnosticos) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-gray-400">
        <div>🤖 Gerando diagnóstico por IA — pode levar alguns segundos…</div>
      </div>
    );
  }

  const modelos = Array.from(new Set(diagnosticos.map((d) => d.modeloUsado)));
  const geradoEm = diagnosticos[0]?.geradoEm;

  function atualizarRecomendacoes(eixo: DiagnosticoEixo["eixo"], recomendacoes: RecomendacaoIA[]) {
    setDiagnosticos((atual) =>
      (atual ?? []).map((d) =>
        d.eixo === eixo
          ? { ...d, recomendacoes, recomendacaoAjustadaEm: new Date().toISOString() }
          : d,
      ),
    );
  }

  function substituirDiagnostico(eixo: DiagnosticoEixo["eixo"], novoDiagnostico: DiagnosticoEixo) {
    setDiagnosticos((atual) => (atual ?? []).map((d) => (d.eixo === eixo ? novoDiagnostico : d)));
  }

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-400">
          Análise gerada por <strong>{modelos.join(", ")}</strong> com base nos dados do Censo
          Escolar 2025 · Cache de 24h.
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => carregar(true)}
            disabled={gerando}
            className="rounded bg-gov-blue px-3 py-1.5 text-xs font-bold text-white disabled:opacity-60"
          >
            {gerando ? "⏳ Gerando…" : "🔄 Regenerar"}
          </button>
          <button
            disabled
            title="Disponível em uma fase futura"
            className="cursor-not-allowed rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-400"
          >
            📄 Exportar PDF (em breve)
          </button>
        </div>
      </div>

      <Panel
        titulo="Diagnóstico por Eixo da PNEEI"
        acao={
          geradoEm && (
            <span className="text-[11px] text-gray-400">atualizado {tempoDecorrido(geradoEm)}</span>
          )
        }
      >
        {diagnosticos.map((d) => (
          <DiagnosticoEixoCard
            key={d.eixo}
            diagnostico={d}
            codigoIbge={codigoIbge}
            onRecomendacoesAtualizadas={atualizarRecomendacoes}
            onDiagnosticoReprocessado={substituirDiagnostico}
          />
        ))}
      </Panel>
    </div>
  );
}
