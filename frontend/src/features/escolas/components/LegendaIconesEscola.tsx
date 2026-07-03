// Legenda dos ícones de status por eixo usados em TabelaEscolas/ModalEscola.
const ITENS: { icone: string; texto: string }[] = [
  { icone: "✅", texto: "Conforme" },
  { icone: "⚠️", texto: "Parcialmente conforme" },
  { icone: "❌", texto: "Não conforme" },
  { icone: "N/A", texto: "Não se aplica a esta escola" },
];

export function LegendaIconesEscola() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded bg-gray-50 px-3 py-1.5 text-[11px] text-gray-500">
      <span className="font-bold uppercase tracking-wide text-gray-400">Legenda:</span>
      {ITENS.map((item) => (
        <span key={item.texto} className="flex items-center gap-1">
          <span className={item.icone === "N/A" ? "text-[9px] text-gray-400" : ""}>{item.icone}</span>
          {item.texto}
        </span>
      ))}
    </div>
  );
}
