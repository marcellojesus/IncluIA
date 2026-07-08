import { getMunicipioDetalhe } from "@/features/indicadores-municipio/api";
import { InicioMunicipio } from "@/features/indicadores-municipio/components/InicioMunicipio";

// Dados dependem do :codigoIbge da URL — não faz sentido pré-renderizar no build. A checagem de
// "município não encontrado" já acontece no layout.tsx (municipio/[codigoIbge]/layout.tsx);
// aqui assumimos que ele existe (fetch deduplicado pelo Next.js, mesma URL do layout).
export const dynamic = "force-dynamic";

export default async function MunicipioInicioPage({
  params,
}: {
  params: Promise<{ codigoIbge: string }>;
}) {
  const { codigoIbge } = await params;
  const municipio = await getMunicipioDetalhe(Number(codigoIbge));

  if (!municipio) return null; // layout.tsx já mostrou a mensagem de "não encontrado"

  return <InicioMunicipio municipio={municipio} />;
}
