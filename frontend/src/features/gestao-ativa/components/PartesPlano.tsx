// Peças de exibição de uma ação do Plano de Ação, usadas pelo diretor (rascunho e prévia) e pelo
// secretário (revisão da versão enviada).
import type { AcaoPlano, CamposAcao } from "../types";
import { Selo } from "./ui";

export function SeloOrigem({ acao }: { acao: Pick<AcaoPlano, "origem" | "editada"> }) {
  if (acao.origem === "diretor") return <Selo tom="neutro">Escrita pela escola</Selo>;
  return <Selo tom="teal">{acao.editada ? "Sugerida pela IA · editada" : "Sugerida pela IA"}</Selo>;
}

export function Fontes({ ids, citacoes }: { ids: string[]; citacoes: Record<string, string> }) {
  if (!ids.length) return null;
  return (
    <div className="mt-1 text-[11px] text-gray-500">
      Fontes: {ids.map((id) => citacoes[id] ?? id).join("; ")}
    </div>
  );
}

export function Detalhes({ campos }: { campos: Omit<CamposAcao, "codigo" | "acao"> }) {
  const linhas: [string, string | null][] = [
    ["Responsável", campos.responsavel],
    ["Prazo", campos.prazo],
    ["Horizonte", campos.horizonte === "LOA" ? "LOA · exercício corrente" : "PPA · até quatro anos"],
    ["Custo estimado", campos.custoEstimado],
    ["Premissas", campos.premissas],
  ];
  return (
    <dl className="mt-2 grid gap-x-4 gap-y-1 text-[12px] sm:grid-cols-[auto_1fr]">
      {linhas
        .filter(([, valor]) => valor)
        .map(([rotulo, valor]) => (
          <div key={rotulo} className="contents">
            <dt className="font-bold text-gray-500">{rotulo}</dt>
            <dd className="text-gray-700">{valor}</dd>
          </div>
        ))}
    </dl>
  );
}
