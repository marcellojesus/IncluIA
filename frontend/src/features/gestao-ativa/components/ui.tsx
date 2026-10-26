// Peças visuais da Gestão Ativa, no estilo do protótipo aprovado (FASE2/prototipo_gestao_ativa_v2.html):
// papel claro, raio de 8px, selos por tom de status e callouts informativos.

type Tom = "verde" | "azul" | "ambar" | "vermelho" | "neutro" | "teal";

const TONS: Record<Tom, string> = {
  verde: "bg-[#e7f3ec] text-[#2f7a55]",
  azul: "bg-[#eaf0f6] text-[#426b95]",
  ambar: "bg-[#fff4df] text-[#9a6114]",
  vermelho: "bg-[#fbe9e7] text-[#b23838]",
  neutro: "bg-black/[.05] text-gray-600",
  teal: "bg-gov-blue-lt text-gov-blue-mid",
};

export function Selo({ tom, children }: { tom: Tom; children: React.ReactNode }) {
  return <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-bold ${TONS[tom]}`}>{children}</span>;
}

export function Cartao({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-black/5 bg-paper shadow-[0_2px_12px_rgba(31,54,47,.07)] ${className}`}>{children}</div>;
}

export function Aviso({ tom = "info", children }: { tom?: "info" | "atencao"; children: React.ReactNode }) {
  const estilo = tom === "atencao" ? "border-gov-orange bg-[#fff4df]" : "border-gov-blue bg-gov-blue-lt";
  return <div className={`rounded-r-lg border-l-4 px-4 py-3 text-[13px] leading-relaxed text-ink ${estilo}`}>{children}</div>;
}

export function Campo({
  id,
  rotulo,
  ajuda,
  ...props
}: { id: string; rotulo: string; ajuda?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="mb-3">
      <label htmlFor={id} className="mb-1 block text-xs font-bold text-gray-700">
        {rotulo}
      </label>
      <input
        id={id}
        {...props}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gov-blue focus:ring-2 focus:ring-gov-blue/20"
      />
      {ajuda && <p className="mt-1 text-[11px] text-gray-500">{ajuda}</p>}
    </div>
  );
}

export function CampoTexto({
  id,
  rotulo,
  ajuda,
  ...props
}: { id: string; rotulo: string; ajuda?: string } & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div className="mb-3">
      <label htmlFor={id} className="mb-1 block text-xs font-bold text-gray-700">
        {rotulo}
      </label>
      <textarea
        id={id}
        rows={3}
        {...props}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gov-blue focus:ring-2 focus:ring-gov-blue/20"
      />
      {ajuda && <p className="mt-1 text-[11px] text-gray-500">{ajuda}</p>}
    </div>
  );
}

export function Selecao({
  id,
  rotulo,
  opcoes,
  ...props
}: { id: string; rotulo: string; opcoes: { valor: string; texto: string }[] } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="mb-3">
      <label htmlFor={id} className="mb-1 block text-xs font-bold text-gray-700">
        {rotulo}
      </label>
      <select
        id={id}
        {...props}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gov-blue focus:ring-2 focus:ring-gov-blue/20"
      >
        <option value="">Escolha…</option>
        {opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto}
          </option>
        ))}
      </select>
    </div>
  );
}

// Motivos em lista fechada (backend/app/features/acesso/servico.py, CATEGORIAS): é o que vai para a
// auditoria; o texto livre fica só no vínculo, mascarado.
export const MOTIVOS: Record<string, { valor: string; texto: string }[]> = {
  aprovar: [
    { valor: "oficio", texto: "Ofício ou ato de designação" },
    { valor: "sistema_rede", texto: "Registro no sistema da rede" },
    { valor: "telefone_institucional", texto: "Contato pelo telefone oficial da escola" },
    { valor: "presencial", texto: "Conferência presencial" },
    { valor: "outro", texto: "Outro" },
  ],
  rejeitar: [
    { valor: "nao_consta", texto: "Não consta como diretor(a) da escola" },
    { valor: "escola_errada", texto: "Código INEP de outra escola" },
    { valor: "outro", texto: "Outro" },
  ],
  suspender: [
    { valor: "afastamento", texto: "Afastamento temporário" },
    { valor: "apuracao", texto: "Apuração em andamento" },
    { valor: "outro", texto: "Outro" },
  ],
  reativar: [
    { valor: "retorno", texto: "Retorno às funções" },
    { valor: "outro", texto: "Outro" },
  ],
  revogar: [
    { valor: "mudanca_escola", texto: "Mudou de escola" },
    { valor: "desligamento", texto: "Deixou a função" },
    { valor: "uso_indevido", texto: "Uso indevido do acesso" },
    { valor: "outro", texto: "Outro" },
  ],
  provisionar: [
    { valor: "oficio", texto: "Ofício da prefeitura" },
    { valor: "telefone_institucional", texto: "Telefone oficial da secretaria" },
    { valor: "diario_oficial", texto: "Publicação no diário oficial" },
    { valor: "outro", texto: "Outro" },
  ],
};

export const AVISO_TEXTO_LIVRE = "Não descreva motivos de saúde, situação pessoal nem dados de outras pessoas.";

type Variante = "primario" | "coral" | "contorno" | "discreto" | "perigo";

const VARIANTES: Record<Variante, string> = {
  primario: "bg-gov-blue text-white hover:bg-gov-blue-mid",
  coral: "bg-accent text-white hover:bg-accent-dark",
  contorno: "border border-gov-blue text-gov-blue hover:bg-gov-blue-lt",
  discreto: "text-gray-600 hover:bg-black/5",
  perigo: "border border-gov-red text-gov-red hover:bg-[#fbe9e7]",
};

export function Botao({
  variante = "primario",
  className = "",
  ...props
}: { variante?: Variante } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-bold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gov-blue disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTES[variante]} ${className}`}
    />
  );
}

export function Erro({ mensagem }: { mensagem: string | null }) {
  if (!mensagem) return null;
  return (
    <p role="alert" className="mb-3 rounded-lg bg-[#fbe9e7] px-3 py-2 text-[13px] text-[#b23838]">
      {mensagem}
    </p>
  );
}

export function Passos({ passos }: { passos: { titulo: string; texto: string; feito: boolean }[] }) {
  return (
    <ol className="mb-4 space-y-3">
      {passos.map((p) => (
        <li key={p.titulo} className="flex gap-3">
          <span
            aria-hidden
            className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
              p.feito ? "bg-gov-green text-white" : "border-2 border-gray-300 text-transparent"
            }`}
          >
            ✓
          </span>
          <div>
            <div className="text-[13px] font-bold text-ink">
              {p.titulo}
              <span className="sr-only">{p.feito ? " (concluído)" : " (pendente)"}</span>
            </div>
            <div className="text-[12px] text-gray-500">{p.texto}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}
