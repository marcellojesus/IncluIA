import Link from "next/link";

// Barra discreta presente em todas as telas do sistema (login e pós-login) — ver
// docs/requirements/metodologia.md RF-01.
export function Footer() {
  return (
    <div className="flex flex-shrink-0 items-center justify-center gap-3 bg-gov-blue-dark py-2.5 text-center text-xs text-white/40">
      <span>IncluIA · Censo Escolar 2025 — INEP/MEC · PNEEI (Decreto 12.686/2025)</span>
      <span className="text-white/20">|</span>
      <Link href="/metodologia" className="text-white/50 underline-offset-2 hover:text-white/80 hover:underline">
        Metodologia do Score IncluIA
      </Link>
    </div>
  );
}
