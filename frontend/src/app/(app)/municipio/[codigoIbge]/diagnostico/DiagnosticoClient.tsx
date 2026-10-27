// Leitura pública do município com apoio de IA: sem login desde 2026-10-27 (impacto-fase-1.md, opção 2).
import { AbaDiagnosticoIA } from "@/features/diagnostico-ia/components/AbaDiagnosticoIA";

export function DiagnosticoClient({ codigoIbge, nome }: { codigoIbge: number; nome: string }) {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-extrabold text-gov-blue-dark">Diagnóstico com IA · {nome}</h1>
      <p className="mb-5 text-sm text-gray-500">
        Uma explicação de cada eixo da PNEEI em linguagem simples, a partir dos dados do Censo Escolar do INEP.
      </p>
      <AbaDiagnosticoIA codigoIbge={codigoIbge} />
    </div>
  );
}
