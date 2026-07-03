type PaginaEmConstrucaoProps = {
  titulo: string;
  specs: string[];
};

// Placeholder honesto para rotas cuja feature ainda não foi implementada —
// evita páginas quebradas enquanto construímos feature por feature (ver docs/requirements/).
export function PaginaEmConstrucao({ titulo, specs }: PaginaEmConstrucaoProps) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
      <h1 className="text-2xl font-bold text-gov-blue-dark">{titulo}</h1>
      <p className="text-sm text-gray-500">Funcionalidade ainda não implementada.</p>
      <ul className="text-xs text-gray-400">
        {specs.map((spec) => (
          <li key={spec}>{spec}</li>
        ))}
      </ul>
    </main>
  );
}
