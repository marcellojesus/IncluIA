"use client";

// Ver interface.md §4 "Barra de Contexto do Município" — compartilhada pelas 3 abas
// (indicadores-municipio, escolas, diagnostico-ia).
import { Badge } from "@/shared/components/Badge";
import { formatarScore } from "@/shared/lib/score";

export type AbaMunicipio = "indicadores" | "escolas" | "diagnostico";

const ABAS: Array<{ id: AbaMunicipio; label: string }> = [
  { id: "indicadores", label: "📋 Indicadores" },
  { id: "escolas", label: "🏫 Escolas" },
  { id: "diagnostico", label: "🤖 Diagnóstico IA" },
];

type ContextoMunicipioBarProps = {
  nome: string;
  uf: string;
  score: number;
  faixa: string;
  cor: string;
  abaAtiva: AbaMunicipio;
  onMudarAba: (aba: AbaMunicipio) => void;
  onVoltar: () => void;
};

export function ContextoMunicipioBar({
  nome,
  uf,
  score,
  faixa,
  cor,
  abaAtiva,
  onMudarAba,
  onVoltar,
}: ContextoMunicipioBarProps) {
  return (
    <div className="flex flex-shrink-0 items-center gap-5 bg-gov-blue-dark px-6">
      <button
        onClick={onVoltar}
        className="flex items-center gap-1.5 rounded border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white/85 hover:bg-white/20"
      >
        ← Mapa
      </button>

      <div>
        <div className="text-base font-bold text-white">{nome}</div>
        <div className="text-[11px] text-white/50">{uf}</div>
      </div>

      <div className="ml-auto flex flex-col items-end py-2.5">
        <div className="text-2xl font-bold text-white">{formatarScore(score)}</div>
        <div className="text-[10px] text-white/45">Score IncluIA</div>
        <Badge texto={faixa} cor={cor} />
      </div>

      <div className="flex h-full items-end gap-0">
        {ABAS.map((aba) => (
          <button
            key={aba.id}
            onClick={() => onMudarAba(aba.id)}
            className={`h-14 border-b-[3px] px-5 text-sm font-semibold transition-colors ${
              abaAtiva === aba.id
                ? "border-yellow-400 text-white"
                : "border-transparent text-white/55 hover:text-white/85"
            }`}
          >
            {aba.label}
          </button>
        ))}
      </div>
    </div>
  );
}
