// Ver interface.md §6 "Tabela de escolas" — lista em cartões (substituiu a tabela original),
// com um badge de texto + ponto colorido por eixo, no estilo do protótipo de referência.
import type { Escola, StatusEixo } from "../types";

const ESTILO_POR_STATUS: Record<StatusEixo, { texto: string; chip: string; dot: string; label: string }> = {
  ok: { texto: "text-gov-green", chip: "bg-green-50", dot: "bg-gov-green", label: "Conforme" },
  warn: { texto: "text-gov-orange", chip: "bg-orange-50", dot: "bg-gov-orange", label: "Parcial" },
  nok: { texto: "text-gov-red", chip: "bg-red-50", dot: "bg-gov-red", label: "Não conf." },
  na: { texto: "text-gray-400", chip: "bg-gray-50", dot: "bg-gray-300", label: "Não se aplica" },
};

function BadgeStatusEixo({ status }: { status: StatusEixo }) {
  const estilo = ESTILO_POR_STATUS[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${estilo.chip} ${estilo.texto}`}
    >
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${estilo.dot}`} />
      {estilo.label}
    </span>
  );
}

function ColunaEixo({ label, status }: { label: string; status: StatusEixo }) {
  return (
    <div className="flex w-28 shrink-0 flex-col items-center gap-1.5">
      <span className="text-[10px] font-extrabold uppercase tracking-wide text-gray-400">{label}</span>
      <BadgeStatusEixo status={status} />
    </div>
  );
}

export function ListaEscolas({
  escolas,
  onSelecionar,
}: {
  escolas: Escola[];
  onSelecionar: (escola: Escola) => void;
}) {
  if (escolas.length === 0) {
    return (
      <div className="rounded-2xl bg-paper p-8 text-center text-sm text-gray-400 shadow-sm">
        Nenhuma escola nesta situação.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {escolas.map((escola) => (
        <button
          key={escola.coEntidade}
          type="button"
          onClick={() => onSelecionar(escola)}
          className="flex w-full items-center gap-4 rounded-2xl bg-paper px-5 py-4 text-left shadow-sm transition-shadow hover:shadow"
        >
          <div className="min-w-0 flex-1">
            <div className="truncate font-bold text-gov-blue-dark">{escola.nome}</div>
            <div className="truncate text-xs text-gray-400">
              {escola.bairro} · {escola.rede} · {escola.alunosEsp} estudantes ESP
            </div>
          </div>

          <ColunaEixo label="AEE" status={escola.statusEixoI} />
          <ColunaEixo label="Acessib." status={escola.statusEixoII} />
          <ColunaEixo label="Apoio" status={escola.statusEixoIII} />
          <ColunaEixo label="Classe C" status={escola.statusEixoIV} />

          <span className="shrink-0 text-lg text-gray-300">›</span>
        </button>
      ))}
    </div>
  );
}
