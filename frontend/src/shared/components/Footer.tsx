import Link from "next/link";

// Rodapé presente em todas as telas (login e pós-login).
export function Footer() {
  return (
    <div className="flex flex-shrink-0 flex-wrap items-center justify-center gap-x-3 gap-y-1 bg-gov-blue-dark px-4 py-3 text-center text-xs text-white/50">
      <span>Escola Sem Barreiras · Iniciativa da sociedade civil, sem vínculo governamental</span>
      <span className="text-white/20">|</span>
      <span>Censo Escolar 2025 — INEP/MEC · PNEEI (Decreto 12.686/2025)</span>
      <span className="text-white/20">|</span>
      <Link href="/metodologia" className="underline-offset-2 hover:text-white/80 hover:underline">
        Metodologia do score
      </Link>
      <span className="text-white/20">|</span>
      <Link href="/sobre" className="underline-offset-2 hover:text-white/80 hover:underline">
        Sobre o projeto
      </Link>
    </div>
  );
}
