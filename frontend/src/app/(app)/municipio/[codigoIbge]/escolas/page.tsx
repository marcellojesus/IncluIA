import { getMunicipioDetalhe } from "@/features/indicadores-municipio/api";
import { AbaEscolas } from "@/features/escolas/components/AbaEscolas";

export const dynamic = "force-dynamic";

export default async function EscolasMunicipioPage({
  params,
}: {
  params: Promise<{ codigoIbge: string }>;
}) {
  const { codigoIbge } = await params;
  const municipio = await getMunicipioDetalhe(Number(codigoIbge));

  if (!municipio) return null;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-extrabold text-gov-blue-dark">
        Escolas de {municipio.nome}
      </h1>
      <p className="mb-5 text-sm text-gray-500">
        Situação de cada escola nos 4 eixos da PNEEI, conforme o Censo Escolar. Clique para ver a
        ficha completa com metas e prazos.
      </p>
      <AbaEscolas codigoIbge={municipio.codigoIbge} />
    </div>
  );
}
