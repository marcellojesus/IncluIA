// Componente do Design System Gov.br — ver interface.md §0 "KPI".

type KpiProps = {
  rotulo: string;
  valor: string;
  subtitulo: string;
  cor?: "azul" | "verde" | "laranja" | "vermelho";
};

const BORDA_POR_COR: Record<NonNullable<KpiProps["cor"]>, string> = {
  azul: "border-gov-blue",
  verde: "border-gov-green",
  laranja: "border-gov-orange",
  vermelho: "border-gov-red",
};

const TEXTO_POR_COR: Record<NonNullable<KpiProps["cor"]>, string> = {
  azul: "text-gov-blue-dark",
  verde: "text-gov-green",
  laranja: "text-gov-orange",
  vermelho: "text-gov-red",
};

export function Kpi({ rotulo, valor, subtitulo, cor = "azul" }: KpiProps) {
  return (
    <div className={`border-l-4 ${BORDA_POR_COR[cor]} bg-white px-5 py-3`}>
      <div className="text-[10px] font-bold uppercase tracking-wide text-gray-400">{rotulo}</div>
      <div className={`text-2xl font-bold leading-tight ${TEXTO_POR_COR[cor]}`}>{valor}</div>
      <div className="text-xs text-gray-400">{subtitulo}</div>
    </div>
  );
}
