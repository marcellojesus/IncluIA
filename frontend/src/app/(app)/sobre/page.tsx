import Link from "next/link";

const REPO_URL = "https://github.com/marcellojesus/IncluIA";

function Rotulo({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-2 text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
      {children}
    </div>
  );
}

export default function SobrePage() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
      <section>
        <span className="mb-4 inline-flex w-fit items-center rounded-full bg-gov-blue-lt px-3 py-1 text-xs font-extrabold text-gov-blue">
          Sobre a plataforma
        </span>
        <h1 className="mb-3 text-4xl font-extrabold text-gov-blue-dark">Escola Sem Barreiras</h1>
        <p className="max-w-[70ch] text-[15px] leading-relaxed text-gray-600">
          Plataforma de <strong>controle social da educação especial inclusiva</strong>: reúne, em
          linguagem cidadã, os dados do <strong>Censo Escolar do INEP</strong> sobre o
          cumprimento da PNEEI (Decreto 12.686/2025) — para que famílias, imprensa e sociedade
          civil possam acompanhar, comparar, cobrar e agir.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl bg-paper p-6 shadow-sm">
          <Rotulo>Área pública</Rotulo>
          <h2 className="mb-2 text-lg font-extrabold text-gov-blue-dark">Para famílias, imprensa e sociedade</h2>
          <p className="text-sm leading-relaxed text-gray-600">
            Índice de inclusão por município e escola, barreiras identificadas no Censo, comparação entre redes e uma leitura de cada eixo
            escrita com apoio de IA. Também mostra o que as escolas publicaram na Gestão Ativa. Não precisa de cadastro.
          </p>
        </div>
        <div className="rounded-2xl bg-paper p-6 shadow-sm">
          <Rotulo>Gestão Ativa</Rotulo>
          <h2 className="mb-2 text-lg font-extrabold text-gov-blue-dark">Para diretores de escola e secretarias</h2>
          <p className="text-sm leading-relaxed text-gray-600">
            A escola explica cada barreira numa Declaração de Obstáculos e propõe um Plano de Ação; a secretaria municipal analisa os planos
            e monta o plano da rede. O acesso é validado pela secretaria. A escola decide o que publicar, sem alterar os dados do Censo nem o
            índice.
          </p>
          <Link href="/participar" className="mt-3 inline-block text-sm font-bold text-gov-blue hover:underline">
            Conhecer a Gestão Ativa →
          </Link>
        </div>
      </section>

      <div className="rounded-2xl border border-orange-200 bg-orange-50 px-5 py-4 text-sm leading-relaxed text-orange-900">
        <strong>Protótipo acadêmico:</strong> número baseado no Censo Escolar — Microdados do
        Censo Escolar da Educação Básica 2025.{" "}
        <a
          href="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar"
          target="_blank"
          rel="noreferrer"
          className="font-bold underline underline-offset-2"
        >
          Link
        </a>
      </div>

      <div className="rounded-2xl border border-orange-200 bg-orange-50 px-5 py-4 text-sm leading-relaxed text-orange-900">
        <strong>Metodologia em construção:</strong> a fórmula do Índice de Inclusão é uma
        proposta dos alunos da UFT — ainda carece de revisão por um estatístico e por um
        especialista da área de educação antes de qualquer uso oficial.{" "}
        <Link href="/metodologia" className="font-bold underline underline-offset-2">
          Ver metodologia completa
        </Link>
      </div>

      <section className="rounded-2xl bg-paper p-6 shadow-sm">
        <h2 className="mb-1 text-xl font-extrabold text-gov-blue-dark">Trabalho acadêmico</h2>
        <p className="mb-5 text-sm leading-relaxed text-gray-500">
          Este projeto foi desenvolvido como trabalho das disciplinas abaixo, no âmbito do
          Programa de Pós-Graduação em Governança e Transformação Digital.
        </p>

        <div className="mb-5 grid grid-cols-2 gap-6">
          <div>
            <Rotulo>Disciplinas</Rotulo>
            <p className="text-sm text-gray-700">
              Ferramentas para mudança e inovação em serviços públicos
            </p>
            <p className="text-sm text-gray-400">e</p>
            <p className="text-sm text-gray-700">
              Desenvolvimento de produtos para governo com IA generativa
            </p>
          </div>
          <div>
            <Rotulo>Programa</Rotulo>
            <p className="text-sm text-gray-700">
              Pós-Graduação em Governança e Transformação Digital
            </p>
            <p className="text-sm font-bold text-gov-blue">Universidade Federal de Tocantins</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 border-t border-gray-100 pt-5">
          <div>
            <Rotulo>Discentes</Rotulo>
            <ul className="flex flex-col gap-3 text-sm text-gray-700">
              <li>Bruno Feres Bichara Peixoto</li>
              <li>Cassiano de Souza Alves</li>
              <li>
                <div>Marcello de Jesus Fernandes</div>
                <a
                  href="mailto:marcello.jesus@uft.edu.br"
                  className="text-xs text-gov-blue hover:underline"
                >
                  marcello.jesus@uft.edu.br
                </a>
              </li>
            </ul>
          </div>
          <div>
            <Rotulo>Docentes</Rotulo>
            <ul className="flex flex-col gap-1 text-sm text-gray-700">
              <li>Prof. David Nadler Prata</li>
              <li>Profa. Marina Figueiredo Moreira</li>
              <li>Prof. Paulo Henrique de Souza Bermejo</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="flex items-center justify-between gap-4 rounded-2xl bg-gov-blue-dark p-6 text-white">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💻</span>
          <div>
            <div className="mb-1 font-bold">Projeto de código aberto</div>
            <p className="text-sm leading-relaxed text-white/70">
              Todo o código-fonte é livre e auditável, sob licença aberta. Contribuições da
              comunidade são bem-vindas — issues, dados e melhorias.
            </p>
          </div>
        </div>
        <a
          href={REPO_URL}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-xl bg-paper px-4 py-2.5 text-sm font-extrabold text-gov-blue-dark hover:bg-white"
        >
          Ver no GitHub ↗
        </a>
      </section>

      <div className="flex gap-3">
        <Link
          href="/"
          className="rounded-xl bg-gov-blue px-5 py-3 text-sm font-extrabold text-white hover:bg-gov-blue-mid"
        >
          Explorar a plataforma
        </Link>
        <Link
          href="/dados-abertos"
          className="rounded-xl border-2 border-gray-200 px-5 py-3 text-sm font-extrabold text-gov-blue-dark hover:bg-gray-50"
        >
          Ver dados abertos
        </Link>
      </div>
    </div>
  );
}
