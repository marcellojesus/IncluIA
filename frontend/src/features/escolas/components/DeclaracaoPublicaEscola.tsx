"use client";

// Declaração de Obstáculos publicada pela escola (protótipo v2, área pública; DO-RF-08). Mostra a
// versão e a data; o relato da escola fica separado do dado do Censo, que não muda (RN-DO-04).
import { useEffect, useState } from "react";

import { type DeclaracaoPublica, type PlanoPublico, getDeclaracaoPublica } from "../api";

const ROTULO: Record<DeclaracaoPublica["itens"][number]["posicao"], string> = {
  obstaculo: "Obstáculo relatado",
  divergencia: "Divergência com o Censo",
  sem_relato: "Sem relato nesta versão",
};

const data = (iso: string) => new Date(iso).toLocaleDateString("pt-BR");

export function DeclaracaoPublicaEscola({ coEntidade }: { coEntidade: number }) {
  const [declaracao, setDeclaracao] = useState<DeclaracaoPublica | null | undefined>(undefined);

  useEffect(() => {
    let ativo = true;
    getDeclaracaoPublica(coEntidade)
      .then((dados) => ativo && setDeclaracao(dados))
      .catch(() => ativo && setDeclaracao(null));
    return () => {
      ativo = false;
    };
  }, [coEntidade]);

  if (declaracao === undefined) return null;

  return (
    <section className="mt-5 border-t border-gray-100 pt-4" aria-labelledby={`declaracao-${coEntidade}`}>
      <div className="flex items-center justify-between gap-2">
        <h3 id={`declaracao-${coEntidade}`} className="text-[13px] font-bold text-gov-blue-dark">Declaração de Obstáculos da escola</h3>
        <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-bold ${declaracao ? "bg-[#e7f3ec] text-[#2f7a55]" : "bg-black/[.05] text-gray-600"}`}>
          {declaracao ? `Publicada · v${declaracao.versao}` : "Não publicada"}
        </span>
      </div>
      {declaracao ? (
        <>
          <p className="mt-1 text-[11px] text-gray-500">
            Versão {declaracao.versao}, emitida em {data(declaracao.emitidaEm)} e publicada em {data(declaracao.publicadaEm)} pela gestão da
            escola. Não altera os dados do Censo nem o índice de inclusão.
          </p>
          <ul className="mt-2 space-y-2">
            {declaracao.itens.map((item) => (
              <li key={item.codigo} className="rounded border border-gray-100 p-2.5">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[12px] font-bold text-gray-700">{item.barreira}</span>
                  <span className="whitespace-nowrap text-[10px] font-bold text-gray-500">{ROTULO[item.posicao]}</span>
                </div>
                <div className="text-[11px] text-gray-400">Censo {declaracao.censoVersao}: {item.dadoCenso}</div>
                <p className="mt-1 text-[12px] text-gray-700">{item.textoPublico}</p>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="mt-1 text-[12px] text-gray-500">A gestão da escola ainda não publicou uma Declaração de Obstáculos.</p>
      )}
      {declaracao?.plano && <PlanoPublicoEscola plano={declaracao.plano} coEntidade={coEntidade} />}
    </section>
  );
}

// Plano de Ação aceito pela secretaria e publicado pela escola: transparência sobre o que a escola
// planeja para cada obstáculo. Aceitar não é financiamento nem execução (RN-SFR-05).
function PlanoPublicoEscola({ plano, coEntidade }: { plano: PlanoPublico; coEntidade: number }) {
  const barreiras = [...new Set(plano.itens.map((i) => i.barreira))];
  return (
    <div className="mt-5" aria-labelledby={`plano-${coEntidade}`}>
      <div className="flex items-center justify-between gap-2">
        <h3 id={`plano-${coEntidade}`} className="text-[13px] font-bold text-gov-blue-dark">Plano de Ação da escola</h3>
        <span className="rounded-full bg-[#e7f3ec] px-2.5 py-0.5 text-[11px] font-bold text-[#2f7a55]">Aceito pela secretaria · v{plano.versao}</span>
      </div>
      <p className="mt-1 text-[11px] text-gray-500">
        Versão {plano.versao}, baseada na Declaração v{plano.declaracaoVersao}
        {plano.aceitoEm ? `, aceita pela secretaria municipal em ${data(plano.aceitoEm)}` : ""} e publicada em {data(plano.publicadoEm)}. O
        aceite significa que o plano serve de base ao planejamento da rede; não é garantia de orçamento nem de execução. Custos e prazos
        são estimativas.
      </p>
      <div className="mt-2 space-y-2">
        {barreiras.map((barreira) => (
          <div key={barreira} className="rounded border border-gray-100 p-2.5">
            <div className="text-[12px] font-bold text-gray-700">{barreira}</div>
            <ul className="mt-1 space-y-2">
              {plano.itens
                .filter((i) => i.barreira === barreira)
                .map((i, n) => (
                  <li key={n} className="border-l-2 border-[#0e7c6b]/40 pl-2">
                    <p className="text-[12px] font-bold text-gray-800">{i.acao}</p>
                    {i.relacao && <p className="text-[12px] text-gray-600">{i.relacao}</p>}
                    <p className="mt-0.5 text-[11px] text-gray-500">
                      {[i.responsavel, i.prazo, i.horizonte === "LOA" ? "LOA · exercício corrente" : "PPA · até quatro anos", i.custoEstimado && `Custo: ${i.custoEstimado}`]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                    {i.fontes.length > 0 && <p className="text-[10px] text-gray-400">Fontes: {i.fontes.join("; ")}</p>}
                  </li>
                ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
