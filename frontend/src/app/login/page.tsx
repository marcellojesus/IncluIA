import { Suspense } from "react";

import { LoginPage } from "@/features/login/components/LoginPage";

// A tela de Login não tem o AppHeader/GeoFiltroBar — esses só aparecem dentro do grupo de rotas
// (app). Layout real (institucional vs. contextual do Diagnóstico IA) decidido em LoginPage, que
// lê `?redirect=` via useSearchParams (por isso o Suspense aqui).
export default function Page() {
  return (
    <Suspense>
      <LoginPage />
    </Suspense>
  );
}
