// Componente do Design System Gov.br — ver interface.md §0 "Badge". Usa a cor hex vinda do
// backend diretamente (fonte de verdade única da classificação — ver metodologia_score.md §5).

export function Badge({ texto, cor }: { texto: string; cor: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold"
      style={{ backgroundColor: `${cor}22`, color: cor }}
    >
      {texto}
    </span>
  );
}
