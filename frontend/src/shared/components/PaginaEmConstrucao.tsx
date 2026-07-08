type PaginaEmConstrucaoProps = {
  titulo: string;
  descricao: string;
  specs: string[];
  linkExterno?: { href: string; label: string };
};

// Placeholder honesto para telas cuja funcionalidade ainda não foi implementada — evita telas
// quebradas enquanto construímos feature por feature. Comparar e Sobre já são reais; hoje usado
// por Participar e Dados abertos.
export function PaginaEmConstrucao({ titulo, descricao, specs, linkExterno }: PaginaEmConstrucaoProps) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 px-6 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gov-blue-dark text-2xl">
        🚧
      </div>
      <h1 className="text-2xl font-extrabold text-gov-blue-dark">{titulo}</h1>
      <p className="text-sm text-gray-500">{descricao}</p>
      <div className="mt-2 w-full rounded-2xl bg-paper p-5 text-left shadow-sm">
        <div className="mb-2 text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
          Planejado para uma próxima etapa
        </div>
        <ul className="flex flex-col gap-1.5 text-sm text-gray-600">
          {specs.map((spec) => (
            <li key={spec} className="flex items-start gap-2">
              <span className="mt-0.5 text-accent">›</span>
              {spec}
            </li>
          ))}
        </ul>
      </div>
      {linkExterno && (
        <a
          href={linkExterno.href}
          target="_blank"
          rel="noreferrer"
          className="text-sm font-bold text-gov-blue hover:underline"
        >
          {linkExterno.label} ↗
        </a>
      )}
    </div>
  );
}
