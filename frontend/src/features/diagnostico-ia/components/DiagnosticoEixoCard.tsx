// Ver interface.md §7 "Corpo do diagnóstico" — título, análise, alerta legal e referência.
import type { NarrativaEixo } from "../types";

const TITULO_POR_EIXO: Record<NarrativaEixo["eixo"], string> = {
  I: "⚖️ Eixo I — Oferta de Atendimento Educacional Especializado (AEE)",
  II: "♿ Eixo II — Acessibilidade Física",
  III: "👩‍🏫 Eixo III — Profissionais Especializados",
  IV: "🏫 Eixo IV — Inclusão em Classe Comum",
};

export function DiagnosticoEixoCard({ diagnostico }: { diagnostico: NarrativaEixo }) {
  return (
    <div className="mb-5">
      <div className="mb-2 flex items-center justify-between border-b border-gov-blue-lt pb-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-gov-blue">{TITULO_POR_EIXO[diagnostico.eixo]}</span>
      </div>

      <p className="mb-2 text-sm leading-relaxed text-gray-600">{diagnostico.analise}</p>

      {diagnostico.alertaLegal && (
        <div className="my-2 rounded-r border-l-[3px] border-gov-red bg-red-50 px-3.5 py-2.5 text-xs text-red-900">
          🚨 <strong>Alerta:</strong> {diagnostico.alertaLegal}
        </div>
      )}

      {diagnostico.referenciaMunicipio && <p className="mt-2 text-xs text-gray-400">📍 {diagnostico.referenciaMunicipio}</p>}
    </div>
  );
}
