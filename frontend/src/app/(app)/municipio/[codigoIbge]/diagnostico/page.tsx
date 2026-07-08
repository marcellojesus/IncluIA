import { getMunicipioDetalhe } from "@/features/indicadores-municipio/api";
import { DiagnosticoClient } from "./DiagnosticoClient";

export const dynamic = "force-dynamic";

export default async function DiagnosticoMunicipioPage({
  params,
}: {
  params: Promise<{ codigoIbge: string }>;
}) {
  const { codigoIbge } = await params;
  const municipio = await getMunicipioDetalhe(Number(codigoIbge));

  if (!municipio) return null;

  return <DiagnosticoClient codigoIbge={municipio.codigoIbge} nome={municipio.nome} />;
}
