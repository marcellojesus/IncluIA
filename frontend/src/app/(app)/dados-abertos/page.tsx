import { API_BASE_URL } from "@/shared/lib/apiConfig";

const INEP_URL =
  "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar";

export default function DadosAbertosPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-10">
      <section className="text-center">
        <h1 className="mb-3 text-3xl font-extrabold text-gov-blue-dark">Dados abertos</h1>
        <p className="text-[15px] leading-relaxed text-gray-600">
          Tudo o que alimenta o Índice de Inclusão vem do <strong>Censo Escolar do INEP</strong> —
          dado público, versionado e auditável. Este projeto ainda não tem exportação própria, mas
          os microdados oficiais completos já estão disponíveis para download direto na fonte:{" "}
          <a
            href={INEP_URL}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-gov-blue hover:underline"
          >
            microdados do Censo Escolar no site do INEP ↗
          </a>
          .
        </p>
        <p className="mt-3 text-[14px] leading-relaxed text-gray-600">
          As Declarações de Obstáculos e os Planos de Ação que as escolas publicam na Gestão Ativa aparecem na ficha de cada escola, com
          versão e data. Elas não são oferecidas para download em massa: são textos das escolas, que podem ser retirados de publicação.
        </p>
      </section>

      <section className="flex items-center justify-between gap-4 rounded-2xl bg-gov-blue-dark p-6 text-white">
        <div>
          <div className="mb-1 font-bold">API pública e metodologia aberta</div>
          <p className="text-sm leading-relaxed text-white/70">
            Acesse os indicadores do Censo por município, escola e eixo via API REST, ou leia
            como o índice é calculado — passo a passo, com código-fonte aberto.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded-xl bg-paper px-4 py-2.5 text-sm font-extrabold text-gov-blue-dark hover:bg-white"
          >
            Ver a API
          </a>
          <a
            href="/metodologia"
            className="rounded-xl border-2 border-white/25 px-4 py-2.5 text-sm font-extrabold text-white hover:bg-white/10"
          >
            Metodologia
          </a>
        </div>
      </section>
    </div>
  );
}
