"use client";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { PainelSecretario } from "@/features/gestao-ativa/components/PainelSecretario";

export default function SecretarioPage() {
  return <AreaRestrita papel="secretario">{(eu) => <PainelSecretario eu={eu} />}</AreaRestrita>;
}
