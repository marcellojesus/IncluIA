// Ver interface.md §5.3 "Painel Dados Gerais".
import { Panel } from "@/shared/components/Panel";

export function DadosGeraisPanel({ dadosGerais }: { dadosGerais: Array<[string, string]> }) {
  return (
    <Panel titulo="Dados Gerais">
      <table className="w-full text-xs">
        <tbody>
          {dadosGerais.map(([label, valor]) => (
            <tr key={label} className="border-b border-gray-100 last:border-none">
              <td className="py-1.5 text-gray-500">{label}</td>
              <td className="py-1.5 text-right font-bold text-gray-700">{valor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
