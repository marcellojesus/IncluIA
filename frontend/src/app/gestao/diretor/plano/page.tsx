"use client";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { PlanoAcao } from "@/features/gestao-ativa/components/PlanoAcao";

export default function PlanoPage() {
  return <AreaRestrita papel="diretor">{() => <PlanoAcao />}</AreaRestrita>;
}
