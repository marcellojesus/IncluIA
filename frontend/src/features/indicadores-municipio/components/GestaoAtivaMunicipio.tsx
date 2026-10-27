"use client";

// Gestão Ativa na Início (impacto-fase-1.md PUB-04): quantas escolas do município publicaram
// Declaração de Obstáculos e Plano de Ação, e a porta de entrada para diretores e secretarias.
// Busca no navegador: a rota pública tem limite por IP, e o servidor do site não pode gastá-lo.
// Só contagens de publicação; nada privado da Gestão Ativa (planos em análise, decisões) aparece.
import Link from "next/link";
import { useEffect, useState } from "react";

import { type PublicacaoGestao, getPublicacoesGestao } from "@/features/escolas/api";

export function GestaoAtivaMunicipio({ codigoIbge, nome }: { codigoIbge: number; nome: string }) {
  const [publicacoes, setPublicacoes] = useState<PublicacaoGestao[] | null>(null);

  useEffect(() => {
    getPublicacoesGestao(codigoIbge).then(setPublicacoes).catch(() => setPublicacoes(null));
  }, [codigoIbge]);

  const declaracoes = publicacoes?.length ?? 0;
  const planos = publicacoes?.filter((p) => p.planoVersao).length ?? 0;

  return (
    <section aria-labelledby="titulo-gestao-ativa" className="grid gap-4 md:grid-cols-[1.3fr_1fr]">
      <div className="rounded-2xl bg-paper p-5 shadow-sm">
        <h2 id="titulo-gestao-ativa" className="mb-1 text-xl font-extrabold text-gov-blue-dark">O que as escolas publicaram</h2>
        <p className="mb-4 text-[13px] text-gray-500">
          Na Gestão Ativa, as escolas explicam as barreiras do Censo e propõem planos de ação. O que a escola publica aparece aqui.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-gov-blue-lt p-4">
            <div className="text-3xl font-extrabold text-gov-blue-dark">{publicacoes ? declaracoes : "—"}</div>
            <div className="text-[13px] font-bold text-gov-blue-dark">
              {declaracoes === 1 ? "escola publicou" : "escolas publicaram"} a Declaração de Obstáculos
            </div>
          </div>
          <div className="rounded-xl bg-[#e7f3ec] p-4">
            <div className="text-3xl font-extrabold text-[#2f7a55]">{publicacoes ? planos : "—"}</div>
            <div className="text-[13px] font-bold text-[#2f7a55]">
              {planos === 1 ? "escola publicou" : "escolas publicaram"} o Plano de Ação aceito pela secretaria
            </div>
          </div>
        </div>
        <p className="mt-3 text-[12px] text-gray-500">
          Escola sem publicação não é escola sem dificuldade: a gestão ainda não publicou seus registros.
        </p>
        <Link href={`/municipio/${codigoIbge}/escolas`} className="mt-2 inline-block text-[13px] font-bold text-gov-blue hover:underline">
          Ver as escolas de {nome} →
        </Link>
      </div>

      <Link href="/participar" className="flex flex-col justify-between rounded-2xl border border-orange-200 bg-orange-50/60 p-5 shadow-sm hover:shadow">
        <div>
          <div className="mb-2 text-2xl" aria-hidden>
            🏫
          </div>
          <div className="mb-1 font-bold text-accent-dark">É diretor de escola ou da secretaria?</div>
          <p className="text-[13px] leading-relaxed text-orange-900/70">
            Na Gestão Ativa, a escola registra os obstáculos por trás de cada barreira e propõe um plano de ação; a secretaria analisa e
            monta o plano da rede. O acesso é validado pela secretaria.
          </p>
        </div>
        <span className="mt-3 text-[13px] font-extrabold text-accent-dark">Conhecer a Gestão Ativa →</span>
      </Link>
    </section>
  );
}
