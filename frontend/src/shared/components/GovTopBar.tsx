// Componente do Design System Gov.br — ver interface.md §0 "Header gov.br". Presente em toda tela.

export function GovTopBar() {
  return (
    <div className="flex flex-shrink-0 items-center gap-2.5 bg-gov-blue-dark px-6 py-1.5">
      <div className="flex gap-0.5">
        <span className="block h-4 w-1 rounded-sm bg-gov-green" />
        <span className="block h-4 w-1 rounded-sm bg-yellow-400" />
        <span className="block h-4 w-1 rounded-sm bg-gov-blue" />
      </div>
      <span className="text-[13px] font-bold text-white">gov.br</span>
      <div className="h-4.5 w-px bg-white/25" />
      <span className="text-xs text-white/65">Ministério da Educação · INEP</span>
    </div>
  );
}
