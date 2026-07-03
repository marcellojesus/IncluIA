// Ver interface.md §6 "Tabela de escolas".
import { Badge } from "@/shared/components/Badge";
import { formatarScore } from "@/shared/lib/score";
import type { Escola, StatusEixo } from "../types";

const ICONE_POR_STATUS: Record<StatusEixo, string> = {
  ok: "✅",
  warn: "⚠️",
  nok: "❌",
  na: "N/A",
};

function IconeStatus({ status }: { status: StatusEixo }) {
  return (
    <span className={status === "na" ? "text-[10px] text-gray-400" : "text-base"}>
      {ICONE_POR_STATUS[status]}
    </span>
  );
}

export function TabelaEscolas({
  escolas,
  onSelecionar,
}: {
  escolas: Escola[];
  onSelecionar: (escola: Escola) => void;
}) {
  if (escolas.length === 0) {
    return (
      <div className="rounded bg-white p-8 text-center text-sm text-gray-400 shadow-sm">
        Nenhuma escola nesta situação.
      </div>
    );
  }

  return (
    // overflow-x-auto como rede de segurança em telas muito estreitas — mas table-fixed +
    // colgroup com larguras fixas garante que as colunas de eixo nunca fiquem espremidas a
    // ponto de sumir (o bug real: table-layout:auto dava toda a largura ao nome da escola).
    <div className="overflow-x-auto rounded bg-white shadow-sm">
      <table className="w-full table-fixed text-xs">
        <colgroup>
          <col className="w-[220px]" />
          <col className="w-[90px]" />
          <col className="w-[80px]" />
          <col className="w-[68px]" />
          <col className="w-[68px]" />
          <col className="w-[68px]" />
          <col className="w-[68px]" />
          <col className="w-[70px]" />
        </colgroup>
        <thead className="sticky top-0 z-10">
          <tr className="bg-gov-blue text-left text-white">
            <th className="px-3.5 py-2 font-bold">Escola</th>
            <th className="px-2 py-2 font-bold">Rede</th>
            <th className="px-2 py-2 text-center font-bold">Alunos ESP</th>
            <th className="px-1 py-2 text-center font-bold">Eixo I AEE</th>
            <th className="px-1 py-2 text-center font-bold">Eixo II Acessib.</th>
            <th className="px-1 py-2 text-center font-bold">Eixo III Prof.</th>
            <th className="px-1 py-2 text-center font-bold">Eixo IV CC</th>
            <th className="px-2 py-2 text-center font-bold">Score</th>
          </tr>
        </thead>
        <tbody>
          {escolas.map((escola) => (
            <tr
              key={escola.coEntidade}
              onClick={() => onSelecionar(escola)}
              className="cursor-pointer border-b border-gray-100 last:border-none hover:bg-gov-blue-lt"
            >
              <td className="truncate px-3.5 py-2">
                <div className="truncate font-semibold text-gray-700">{escola.nome}</div>
                <div className="truncate text-[10px] text-gray-400">{escola.bairro}</div>
              </td>
              <td className="px-2 py-2">
                <span className="rounded bg-gov-blue-lt px-1.5 py-0.5 text-[10px] font-bold text-gov-blue">
                  {escola.rede}
                </span>
              </td>
              <td className="px-2 py-2 text-center font-bold text-gray-600">{escola.alunosEsp}</td>
              <td className="px-1 py-2 text-center">
                <IconeStatus status={escola.statusEixoI} />
              </td>
              <td className="px-1 py-2 text-center">
                <IconeStatus status={escola.statusEixoII} />
              </td>
              <td className="px-1 py-2 text-center">
                <IconeStatus status={escola.statusEixoIII} />
              </td>
              <td className="px-1 py-2 text-center">
                <IconeStatus status={escola.statusEixoIV} />
              </td>
              <td className="px-2 py-2 text-center">
                <Badge texto={formatarScore(escola.score)} cor={escola.cor} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
