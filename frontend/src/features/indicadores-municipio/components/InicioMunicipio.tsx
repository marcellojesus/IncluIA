// Tela "Início" — dashboard público do município: hero + índice geral + 4 compromissos da lei
// + score por eixo + números da rede + atalhos + ranking na UF. Substitui a antiga aba
// "Indicadores" (era uma aba dentro da tela de município; agora é a home do sistema).
import Link from "next/link";

import { Badge } from "@/shared/components/Badge";
import { BotaoRegistrarBarreira } from "@/shared/components/BotaoRegistrarBarreira";
import { formatarScore } from "@/shared/lib/score";
import type { MunicipioDetalhe } from "../types";
import { DadosGeraisPanel } from "./DadosGeraisPanel";
import { RankingEstados } from "./RankingEstados";
import { ScoreEixoPanel } from "./ScoreEixoPanel";
import { SemaforoGrid } from "./SemaforoGrid";

export function InicioMunicipio({ municipio }: { municipio: MunicipioDetalhe }) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-8">
      {/* Hero */}
      <section className="grid grid-cols-[1.4fr_1fr] items-center gap-8 rounded-2xl">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-gov-blue-lt px-3 py-1.5 text-xs font-extrabold text-gov-blue-dark">
            📍 {municipio.nome} · {municipio.uf}
          </div>
          <h1 className="mb-3 text-3xl font-extrabold leading-tight text-gov-blue-dark">
            Como está a educação especial inclusiva em {municipio.nome}?
          </h1>
          <p className="mb-5 max-w-[46ch] text-[15px] leading-relaxed text-gray-500">
            Um retrato do cumprimento da <strong>PNEEI (Decreto 12.686/2025)</strong>, com base
            nos dados do <strong>Censo Escolar do INEP</strong> — para famílias, jornalistas e a
            sociedade acompanharem, cobrarem e agirem.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <Link
              href={`/municipio/${municipio.codigoIbge}/escolas`}
              className="rounded-xl bg-gov-blue px-5 py-3 text-sm font-extrabold text-white hover:bg-gov-blue-mid"
            >
              Ver escolas da rede
            </Link>
            <BotaoRegistrarBarreira className="rounded-xl border-2 border-accent px-4 py-2.5 text-sm font-extrabold text-accent-dark hover:bg-white">
              Registrar uma barreira
            </BotaoRegistrarBarreira>
          </div>
        </div>

        <div className="rounded-2xl bg-gov-blue-dark p-6 text-white">
          <div className="text-xs font-extrabold uppercase tracking-wide text-white/60">
            Índice de inclusão
          </div>
          <div className="my-1 flex items-end gap-3">
            <span className="text-6xl font-extrabold leading-none" style={{ color: municipio.cor }}>
              {formatarScore(municipio.score)}
            </span>
            <Badge texto={municipio.faixa} cor={municipio.cor} />
          </div>
          <div className="mb-4 text-xs text-white/50">de 0 a 10 · Censo Escolar 2025</div>
          <div className="h-px bg-white/15" />
          <p className="mt-4 text-[13px] leading-relaxed text-white/80">
            Situação classificada como <strong>{municipio.faixa.toLowerCase()}</strong> segundo o
            detalhamento dos 4 eixos da PNEEI abaixo.
          </p>
        </div>
      </section>

      {/* 4 compromissos */}
      <section>
        <h2 className="mb-1 text-xl font-extrabold text-gov-blue-dark">Os 4 compromissos da lei</h2>
        <p className="mb-4 text-sm text-gray-500">
          Cada eixo do Decreto 12.686/2025, e como {municipio.nome} está em cada um, segundo o
          Censo Escolar.
        </p>
        <SemaforoGrid eixos={municipio.eixos} />
      </section>

      {/* Score por eixo + dados gerais */}
      <section className="grid grid-cols-2 gap-4">
        <ScoreEixoPanel scoreEixos={municipio.scoreEixos} />
        <DadosGeraisPanel dadosGerais={municipio.dadosGerais} />
      </section>

      {/* O que você pode fazer */}
      <section>
        <h2 className="mb-4 text-xl font-extrabold text-gov-blue-dark">O que você pode fazer</h2>
        <div className="grid grid-cols-3 gap-4">
          <Link
            href={`/municipio/${municipio.codigoIbge}/escolas`}
            className="rounded-2xl bg-paper p-5 shadow-sm hover:shadow"
          >
            <div className="mb-2 text-2xl">🏫</div>
            <div className="mb-1 font-bold text-gov-blue-dark">Consultar sua escola</div>
            <div className="text-[13px] leading-relaxed text-gray-500">
              Veja se a escola cumpre as metas do decreto — AEE, acessibilidade, profissionais.
            </div>
          </Link>
          <Link href="/comparar" className="rounded-2xl bg-paper p-5 shadow-sm hover:shadow">
            <div className="mb-2 text-2xl">📊</div>
            <div className="mb-1 font-bold text-gov-blue-dark">Comparar redes</div>
            <div className="text-[13px] leading-relaxed text-gray-500">
              Compare municípios de uma região ou estado e cobre sua gestão com evidências.
            </div>
          </Link>
          <BotaoRegistrarBarreira className="rounded-2xl border border-orange-200 bg-orange-50/60 p-5 text-left shadow-sm hover:shadow">
            <div className="mb-2 text-2xl">📣</div>
            <div className="mb-1 font-bold text-accent-dark">Registrar uma barreira</div>
            <div className="text-[13px] leading-relaxed text-orange-900/70">
              Faltou intérprete, rampa ou vaga? Registre — vira dado público e alerta aos órgãos.
            </div>
          </BotaoRegistrarBarreira>
        </div>
      </section>

      <RankingEstados ufAtual={municipio.uf} />
    </div>
  );
}
