// Ver interface.md §5.4 "Painel Detalhamento — PNEEI (Decreto 12.686/2025)".
// RN-02 de docs/business-rules/indicadores-municipio.md: o aviso jurídico é permanente,
// nunca removido nem condicionado a nada.
import { Panel } from "@/shared/components/Panel";
import type { Conformidade, CriterioDecreto } from "../types";

const ESTILO_CONFORMIDADE: Record<Conformidade, { texto: string; cor: string }> = {
  conforme: { texto: "✅ Conforme", cor: "#168821" },
  parcial: { texto: "⚠️ Parcial", cor: "#E05C00" },
  nao_conforme: { texto: "❌ Não conforme", cor: "#E52207" },
};

// Os critérios já vêm agrupados consecutivamente por eixo (ver backend/app/features/
// indicadores_municipio/service.py::_CRITERIOS_DECRETO) — aqui só calculamos, para cada linha,
// se ela é a 1ª do seu grupo (recebe rowSpan) ou uma continuação (célula "Eixo" omitida),
// para deixar claro de relance que são 4 blocos, mesmo com quantidades de linhas bem diferentes.
function calcularGrupos(criterios: CriterioDecreto[]) {
  return criterios.map((criterio, i) => {
    const ehPrimeiraDoGrupo = i === 0 || criterios[i - 1].eixo !== criterio.eixo;
    const tamanhoGrupo = ehPrimeiraDoGrupo
      ? criterios.filter((c, j) => j >= i && c.eixo === criterio.eixo).length
      : 0;
    return { criterio, ehPrimeiraDoGrupo, tamanhoGrupo };
  });
}

export function TabelaDecretoPanel({ criterios }: { criterios: CriterioDecreto[] }) {
  const linhas = calcularGrupos(criterios);

  return (
    <Panel
      titulo="Detalhamento — PNEEI (Decreto 12.686/2025)"
      acao={<span className="text-[11px] font-semibold text-gov-orange">⚠️ Em validação jurídica</span>}
      semPadding
    >
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gov-blue text-left text-white">
            <th className="px-3.5 py-2 font-bold">Eixo</th>
            <th className="px-3.5 py-2 font-bold">Critério do Decreto</th>
            <th className="px-3.5 py-2 font-bold">Variável Censo 2025</th>
            <th className="px-3.5 py-2 font-bold">Resultado</th>
            <th className="px-3.5 py-2 font-bold">Conformidade</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map(({ criterio, ehPrimeiraDoGrupo, tamanhoGrupo }, i) => {
            const estilo = ESTILO_CONFORMIDADE[criterio.conformidade];
            return (
              <tr key={i} className="border-b border-gray-100 last:border-none hover:bg-gov-blue-lt">
                {ehPrimeiraDoGrupo && (
                  <td
                    rowSpan={tamanhoGrupo}
                    className="whitespace-nowrap border-r border-gray-100 bg-gray-50 px-3.5 py-2 align-top font-bold text-gov-blue-dark"
                  >
                    {criterio.eixo}
                  </td>
                )}
                <td className="px-3.5 py-2">{criterio.criterio}</td>
                <td className="whitespace-nowrap px-3.5 py-2 font-mono text-[11px] text-gray-500">
                  {criterio.variavelCenso}
                </td>
                <td className="whitespace-nowrap px-3.5 py-2">{criterio.resultado}</td>
                <td className="whitespace-nowrap px-3.5 py-2 font-bold" style={{ color: estilo.cor }}>
                  {estilo.texto}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}
