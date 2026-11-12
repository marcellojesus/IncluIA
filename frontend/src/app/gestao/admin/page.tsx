"use client";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { ContasGestao } from "@/features/gestao-ativa/components/ContasGestao";
import { ProvisionarSecretario } from "@/features/gestao-ativa/components/ProvisionarSecretario";

export default function AdminPage() {
  return (
    <AreaRestrita papel="admin">
      {() => (
        <>
          <ContasGestao />
          <ProvisionarSecretario />
        </>
      )}
    </AreaRestrita>
  );
}
