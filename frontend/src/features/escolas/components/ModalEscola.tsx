// Ver interface.md §6.1 "Modal de Detalhamento da Escola" e docs/requirements/escolas.md RF-04.
import { formatarMatriculasEsp } from "@/shared/lib/formatters";
import { Badge } from "@/shared/components/Badge";
import { Modal } from "@/shared/components/Modal";
import { formatarScore } from "@/shared/lib/score";
import type { Escola, StatusEixo } from "../types";
import { BarreirasEscola } from "./BarreirasEscola";
import { DeclaracaoPublicaEscola } from "./DeclaracaoPublicaEscola";

const CARDS_EIXO: Array<{ campo: keyof Escola; label: string }> = [
  { campo: "statusEixoI", label: "Eixo I — AEE" },
  { campo: "statusEixoII", label: "Eixo II — Acessib." },
  { campo: "statusEixoIII", label: "Eixo III — Prof." },
  { campo: "statusEixoIV", label: "Eixo IV — CC" },
];

const ICONE_POR_STATUS: Record<StatusEixo, string> = {
  ok: "✅",
  warn: "⚠️",
  nok: "❌",
  na: "—",
  omitido: "—",
};

export function ModalEscola({ escola, onFechar }: { escola: Escola; onFechar: () => void }) {
  return (
    <Modal
      titulo={escola.nome}
      subtitulo={`Rede ${escola.rede} · ${escola.bairro} · INEP ${escola.coEntidade}`}
      onFechar={onFechar}
    >
      <div className="mb-4 grid grid-cols-4 gap-2">
        {CARDS_EIXO.map(({ campo, label }) => {
          const status = escola[campo] as StatusEixo;
          return (
            <div key={label} className="rounded border border-gray-200 bg-gray-50 py-3 text-center">
              <div className="mb-1 text-2xl">{ICONE_POR_STATUS[status]}</div>
              <div className="text-[10px] leading-tight text-gray-400">{label}</div>
            </div>
          );
        })}
      </div>

      {escola.dadosProtegidos && (
        <p className="mb-4 rounded bg-gov-blue-lt px-3 py-2 text-xs text-gov-blue-dark">
          Esta escola tem menos de 5 matrículas da educação especial. Para não identificar estudantes, o Eixo IV fica omitido e o
          índice público usa a taxa de inclusão em classe comum média das escolas do município.
        </p>
      )}

      {escola.especialExclusiva && (
        <p className="mb-4 rounded bg-gov-blue-lt px-3 py-2 text-xs text-gov-blue-dark">
          Escola especial exclusiva — o Eixo IV (Inclusão em Classe Comum) não se aplica.
        </p>
      )}

      <table className="w-full text-[13px]">
        <tbody>
          <tr className="border-b border-gray-100">
            <td className="py-1.5 text-gray-500">Alunos com deficiência (ESP)</td>
            <td className="py-1.5 text-right font-bold text-gray-700">{formatarMatriculasEsp(escola.alunosEsp)}</td>
          </tr>
          <tr className="border-b border-gray-100">
            <td className="py-1.5 text-gray-500">Bairro</td>
            <td className="py-1.5 text-right font-bold text-gray-700">{escola.bairro}</td>
          </tr>
          <tr className="border-b border-gray-100">
            <td className="py-1.5 text-gray-500">Rede de ensino</td>
            <td className="py-1.5 text-right font-bold text-gray-700">{escola.rede}</td>
          </tr>
          <tr className="border-b border-gray-100">
            <td className="py-1.5 text-gray-500">Ranking no município</td>
            <td className="py-1.5 text-right font-bold text-gray-700">
              #{escola.rankingMunicipal} de {escola.qtdEscolasMunicipio}
            </td>
          </tr>
          <tr>
            <td className="py-1.5 text-gray-500">Índice de inclusão</td>
            <td className="py-1.5 text-right">
              <Badge texto={`${formatarScore(escola.score)} · ${escola.faixa}`} cor={escola.cor} />
            </td>
          </tr>
        </tbody>
      </table>

      <BarreirasEscola coEntidade={escola.coEntidade} />
      <DeclaracaoPublicaEscola coEntidade={escola.coEntidade} />
    </Modal>
  );
}
