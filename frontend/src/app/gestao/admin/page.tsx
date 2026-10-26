"use client";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { ProvisionarSecretario } from "@/features/gestao-ativa/components/ProvisionarSecretario";

export default function AdminPage() {
  return <AreaRestrita papel="admin">{() => <ProvisionarSecretario />}</AreaRestrita>;
}
