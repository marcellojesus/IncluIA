"use client";

import { AreaRestrita } from "@/features/gestao-ativa/components/AreaRestrita";
import { DashboardDiretor } from "@/features/gestao-ativa/components/DashboardDiretor";

export default function DiretorPage() {
  return <AreaRestrita papel="diretor">{() => <DashboardDiretor />}</AreaRestrita>;
}
