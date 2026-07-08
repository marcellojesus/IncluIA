"use client";

// Decide entre o layout institucional genérico (2 colunas, credenciais de demonstração) e a
// tela contextual do Diagnóstico IA (RN-06 de docs/business-rules/login.md) — a segunda só
// aparece quando o `redirect` recebido aponta para uma rota de Diagnóstico IA.
import { useSearchParams } from "next/navigation";

import { BarraAcessibilidade } from "@/shared/components/BarraAcessibilidade";
import { Footer } from "@/shared/components/Footer";
import { AuthDiagnosticoIA } from "./AuthDiagnosticoIA";
import { LoginForm } from "./LoginForm";
import { LoginStats } from "./LoginStats";

function ehRedirectDiagnostico(redirect: string | null): boolean {
  return !!redirect && redirect.includes("/diagnostico");
}

export function LoginPage() {
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");

  if (ehRedirectDiagnostico(redirect)) {
    return <AuthDiagnosticoIA redirect={redirect} />;
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-cream">
      <BarraAcessibilidade />
      <div className="grid flex-1 grid-cols-2 overflow-hidden">
        <div className="flex flex-col justify-center bg-gradient-to-br from-gov-blue-dark via-gov-blue-mid to-gov-blue px-14 py-16">
          <div className="mb-2 text-5xl font-extrabold text-white">Escola Sem Barreiras</div>
          <div className="mb-10 text-sm leading-relaxed text-white/60">
            Dados do Censo Escolar 2025 transformados em
            <br />
            controle social da educação inclusiva.
          </div>
          <div className="mb-12 flex w-fit items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3.5 py-1.5 text-xs font-semibold text-accent">
            ⚖️ Alinhado à PNEEI (Decreto 12.686/2025)
          </div>
          <LoginStats />
        </div>
        <div className="flex items-center justify-center bg-paper px-14 py-16">
          <LoginForm />
        </div>
      </div>
      <Footer />
    </div>
  );
}
