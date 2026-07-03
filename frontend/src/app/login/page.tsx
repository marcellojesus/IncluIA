import { Suspense } from "react";

import { LoginForm } from "@/features/login/components/LoginForm";
import { LoginStats } from "@/features/login/components/LoginStats";
import { Footer } from "@/shared/components/Footer";
import { GovTopBar } from "@/shared/components/GovTopBar";

// Ver interface.md §2 — layout de 2 colunas (esquerda: institucional/stats; direita: formulário).
// A tela de Login só tem o GovTopBar, sem o AppHeader (usuário/logout) — esse só aparece
// depois de autenticado, dentro do grupo de rotas (app).
export default function LoginPage() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <GovTopBar />
      <div className="grid flex-1 grid-cols-2 overflow-hidden">
        <div className="flex flex-col justify-center bg-gradient-to-br from-gov-blue-dark via-gov-blue-mid to-gov-blue px-14 py-16">
          <div className="mb-2 text-5xl font-bold text-white">IncluIA</div>
          <div className="mb-10 text-sm leading-relaxed text-white/55">
            Dados do Censo Escolar 2025 transformados em
            <br />
            decisões de inclusão para gestores públicos.
          </div>
          <div className="mb-12 flex w-fit items-center gap-2 rounded-full border border-yellow-400/30 bg-yellow-400/10 px-3.5 py-1.5 text-xs font-semibold text-yellow-400">
            ⚖️ Alinhado à PNEEI (Decreto 12.686/2025)
          </div>
          <LoginStats />
        </div>
        <div className="flex items-center justify-center bg-white px-14 py-16">
          <Suspense>
            <LoginForm />
          </Suspense>
        </div>
      </div>
      <Footer />
    </div>
  );
}
