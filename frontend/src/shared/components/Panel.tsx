// Componente do Design System Gov.br — ver interface.md §0 "Painel" (card com cabeçalho + corpo).

type PanelProps = {
  titulo: string;
  acao?: React.ReactNode;
  children: React.ReactNode;
  semPadding?: boolean;
};

export function Panel({ titulo, acao, children, semPadding = false }: PanelProps) {
  return (
    <div className="rounded bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2.5">
        <span className="text-[13px] font-bold text-gov-blue-dark">{titulo}</span>
        {acao}
      </div>
      <div className={semPadding ? "" : "p-3.5"}>{children}</div>
    </div>
  );
}
