"use client";

// Botão "Registrar barreira" reutilizado em 3 lugares (AppHeader, hero e card da Início) —
// precisa ser "use client" porque tem onClick, e InicioMunicipio.tsx é Server Component (não
// pode receber handlers de evento diretamente).
import type { ReactNode } from "react";

import { alertarFuncionalidadeFutura } from "@/shared/lib/alertas";

export function BotaoRegistrarBarreira({
  className,
  children,
}: {
  className: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={() => alertarFuncionalidadeFutura("O registro de barreiras")}
      className={className}
    >
      {children}
    </button>
  );
}
