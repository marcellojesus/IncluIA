import { redirect } from "next/navigation";

import { getMunicipiosPorUf } from "@/features/mapa/api";

// Sistema é público — a porta de entrada é o dashboard de um município (Início), não mais o
// Mapa (removido da navegação principal nesta etapa). Sem um município selecionado ainda
// (primeira visita), cai num município padrão; o filtro geográfico no topo troca livremente.
const UF_PADRAO = "DF";

export const dynamic = "force-dynamic";

export default async function RootPage() {
  const municipios = await getMunicipiosPorUf(UF_PADRAO);
  const padrao = municipios[0];

  if (!padrao) {
    redirect("/sobre");
  }

  redirect(`/municipio/${padrao.codigoIbge}`);
}
