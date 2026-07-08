import fs from "node:fs";
import path from "node:path";

import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { BarraAcessibilidade } from "@/shared/components/BarraAcessibilidade";

// Lê a cópia sincronizada em src/content/ (ver scripts/sync-metodologia.mjs, rodado antes de
// dev/build) em vez do arquivo original na raiz do monorepo — next.config.ts fixa o root do
// Turbopack em frontend/, então nada fora dela é acessível de forma confiável no build.
function lerMetodologia(): string {
  const caminho = path.join(process.cwd(), "src", "content", "metodologia_score.md");
  return fs.readFileSync(caminho, "utf-8");
}

export default function MetodologiaPage() {
  const conteudo = lerMetodologia();

  return (
    <div className="flex min-h-screen flex-col">
      <BarraAcessibilidade />
      <div className="flex-shrink-0 bg-gov-blue-dark px-6 py-3">
        <Link href="/" className="text-xs text-white/60 hover:text-white/90">
          ← Voltar ao início
        </Link>
      </div>
      <div className="flex-1 bg-gray-50 px-6 py-10">
        <article className="mx-auto max-w-3xl rounded bg-white p-10 text-sm leading-relaxed text-gray-700 shadow-sm">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => (
                <h1 className="mb-4 border-b border-gray-200 pb-3 text-2xl font-bold text-gov-blue-dark">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="mb-3 mt-8 text-lg font-bold text-gov-blue-dark">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="mb-2 mt-6 text-base font-bold text-gov-blue">{children}</h3>
              ),
              p: ({ children }) => <p className="mb-3">{children}</p>,
              a: ({ href, children }) => (
                <a href={href} className="text-gov-blue underline underline-offset-2">
                  {children}
                </a>
              ),
              strong: ({ children }) => <strong className="font-bold text-gray-900">{children}</strong>,
              code: ({ children }) => (
                <code className="rounded bg-gov-blue-lt px-1 py-0.5 text-xs text-gov-blue-dark">
                  {children}
                </code>
              ),
              blockquote: ({ children }) => (
                <blockquote className="my-3 rounded-r border-l-[3px] border-gov-blue bg-gov-blue-lt px-4 py-2 text-xs text-gov-blue-dark">
                  {children}
                </blockquote>
              ),
              ul: ({ children }) => <ul className="mb-3 list-disc pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="mb-3 list-decimal pl-5">{children}</ol>,
              li: ({ children }) => <li className="mb-1">{children}</li>,
              hr: () => <hr className="my-8 border-gray-200" />,
              table: ({ children }) => (
                <div className="mb-4 overflow-x-auto">
                  <table className="w-full border-collapse text-xs">{children}</table>
                </div>
              ),
              thead: ({ children }) => <thead className="bg-gov-blue text-white">{children}</thead>,
              th: ({ children }) => (
                <th className="border border-gray-200 px-2.5 py-1.5 text-left font-bold">{children}</th>
              ),
              td: ({ children }) => <td className="border border-gray-200 px-2.5 py-1.5">{children}</td>,
            }}
          >
            {conteudo}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  );
}
