// Barra de progresso + número do score, usada nas linhas de ranking (Início e Comparar) — mesmo
// visual do protótipo de referência (barra bege de fundo, preenchimento e número na cor da faixa).
import { formatarScore } from "@/shared/lib/score";

export function BarraScore({ score, cor, largura = 140 }: { score: number; cor: string; largura?: number }) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 shrink-0 overflow-hidden rounded-full bg-[#eee7da]" style={{ width: largura }}>
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: cor }} />
      </div>
      <span className="w-11 shrink-0 text-right text-base font-extrabold" style={{ color: cor }}>
        {formatarScore(score)}
      </span>
    </div>
  );
}
