import { getMunicipioDetalhe } from "@/features/indicadores-municipio/api";
import type { AbaMunicipio } from "@/shared/components/ContextoMunicipioBar";
import { MunicipioClient } from "./MunicipioClient";

// Dados dependem do :codigoIbge da URL — não faz sentido pré-renderizar no build.
export const dynamic = "force-dynamic";

const ABAS_VALIDAS: AbaMunicipio[] = ["indicadores", "escolas", "diagnostico"];

export default async function MunicipioPage({
  params,
  searchParams,
}: {
  params: Promise<{ codigoIbge: string }>;
  searchParams: Promise<{ aba?: string }>;
}) {
  const { codigoIbge } = await params;
  const { aba } = await searchParams;
  const municipio = await getMunicipioDetalhe(Number(codigoIbge));

  if (!municipio) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
        <h1 className="text-xl font-bold text-gov-blue-dark">Município não encontrado</h1>
        <p className="text-sm text-gray-400">
          Não há dados do Score IncluIA para o código {codigoIbge}.
        </p>
      </div>
    );
  }

  // RF de docs/requirements/login.md: ?aba=diagnostico reabre a aba certa após o redirect de
  // volta do login (ver linkLoginParaDiagnostico em MunicipioClient.tsx).
  const abaInicial = ABAS_VALIDAS.includes(aba as AbaMunicipio) ? (aba as AbaMunicipio) : undefined;

  return <MunicipioClient municipio={municipio} abaInicial={abaInicial} />;
}
