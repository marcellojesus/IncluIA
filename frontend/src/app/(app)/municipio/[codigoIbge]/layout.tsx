import { getMunicipioDetalhe } from "@/features/indicadores-municipio/api";
import { MunicipioSync } from "@/shared/components/MunicipioSync";

// Casca compartilhada pelas 3 telas do município (Início, Escolas, Diagnóstico IA) — busca o
// município uma vez (o Next.js dedupe automaticamente chamadas fetch idênticas feitas também
// pelas páginas filhas dentro da mesma requisição) e mantém o GeoFiltroBar/AppHeader em dia via
// MunicipioSync.
export default async function MunicipioLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ codigoIbge: string }>;
}) {
  const { codigoIbge } = await params;
  const municipio = await getMunicipioDetalhe(Number(codigoIbge));

  if (!municipio) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center">
        <h1 className="text-xl font-bold text-gov-blue-dark">Município não encontrado</h1>
        <p className="text-sm text-gray-400">
          Não há dados do Score Escola Sem Barreiras para o código {codigoIbge}.
        </p>
      </div>
    );
  }

  return (
    <>
      <MunicipioSync
        municipio={{
          codigoIbge: municipio.codigoIbge,
          nome: municipio.nome,
          uf: municipio.uf,
          score: municipio.score,
        }}
      />
      {children}
    </>
  );
}
