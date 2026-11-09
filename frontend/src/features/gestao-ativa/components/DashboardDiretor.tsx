"use client";

// Dashboard da situação da escola (requirements/diretor/dashboard-situacao-escola.md; view
// director-dashboard do protótipo v2). Dado do Censo e posição da escola ficam visualmente
// separados (RN-DSE-03); barreira sem posição não significa ausência de dificuldade.
import Link from "next/link";
import { useEffect, useState } from "react";

import { classificarFaixa, formatarScore } from "@/shared/lib/score";

import { getDashboardEscola } from "../api";
import { POSICOES } from "../rotulos";
import type { DashboardEscola } from "../types";
import { PainelTrabalhoDiretor } from "./PainelTrabalhoDiretor";
import { Aviso, Cartao, Selo } from "./ui";

function tomDaFaixa(faixa: string | null): "verde" | "ambar" | "vermelho" | "neutro" {
  if (!faixa) return "neutro";
  if (faixa === "Crítico" || faixa === "Insuficiente") return "vermelho";
  if (faixa === "Em desenvolvimento") return "ambar";
  return "verde";
}

const pontos = (valor: number) => valor.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 });

export function DashboardDiretor() {
  const [dados, setDados] = useState<DashboardEscola | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    getDashboardEscola().then(setDados).catch((falha) => setErro((falha as Error).message));
  }, []);

  if (erro) return <p role="alert" className="mx-auto mt-10 max-w-md rounded-lg bg-[#fbe9e7] p-4 text-sm text-[#b23838]">{erro}</p>;
  if (!dados) return <p role="status" className="mt-16 text-center text-sm text-gray-500">Carregando a situação da escola…</p>;

  const eixosComBarreira = dados.eixos.filter((e) => e.barreiras > 0).length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <nav className="text-xs text-gray-500" aria-label="Trilha">
        Gestão Ativa / <strong className="text-ink">Visão da escola</strong>
      </nav>

      <section className="mt-3 grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <p className="text-xs font-extrabold uppercase tracking-wider text-accent">Painel do diretor · {dados.nome}</p>
          <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Situação atual da escola</h1>
          <p className="mt-2 max-w-2xl text-[15px] text-gray-600">
            Uma visão de trabalho da sua escola, com os indicadores do Censo separados dos obstáculos que sua gestão registrar.
          </p>
        </div>
        <div className="rounded-lg bg-gov-blue-dark px-6 py-5 text-white">
          <div className="text-[11px] font-bold uppercase tracking-wider text-white/60">Score da escola · Censo {dados.censoVersao}</div>
          <div className="mt-1 flex items-baseline gap-3">
            <span className="text-5xl font-extrabold">{formatarScore(dados.score)}</span>
            <span className="rounded-full px-2.5 py-0.5 text-[11px] font-bold text-white" style={{ backgroundColor: classificarFaixa(dados.score).cor }}>
              {dados.faixa}
            </span>
          </div>
          <div className="mt-2 text-[12px] text-white/70">
            {eixosComBarreira} eixos com barreiras · {dados.declaracao.comPosicao} de {dados.declaracao.total} barreiras com posição
          </div>
          <div className="mt-1 text-[11px] text-white/50">Indicador calculado a partir do Censo Escolar; não é certificação legal.</div>
        </div>
      </section>

      <PainelTrabalhoDiretor dados={dados} />

      <section className="mt-8" aria-labelledby="titulo-eixos">
        <div className="flex items-center gap-3">
          <h2 id="titulo-eixos" className="text-lg font-extrabold text-gov-blue-dark">Leitura dos eixos</h2>
          <Selo tom="teal">Dados do Censo Escolar {dados.censoVersao}</Selo>
        </div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {dados.eixos.map((eixo) => (
            <Cartao key={eixo.eixo} className="p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-extrabold text-ink">Eixo {eixo.eixo} · {eixo.nome}</h3>
                <Selo tom={tomDaFaixa(eixo.faixa)}>{eixo.faixa ?? "Indisponível"}</Selo>
              </div>
              <div className="mt-2 text-2xl font-extrabold text-gov-blue-dark">{eixo.score === null ? "—" : formatarScore(eixo.score)}</div>
              <div className="mt-1 text-[12px] text-gray-500">
                {eixo.barreiras} {eixo.barreiras === 1 ? "barreira" : "barreiras"} · {eixo.comPosicao} com posição
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-black/5" aria-hidden>
                <div className="h-1.5 rounded-full bg-gov-blue" style={{ width: `${eixo.barreiras ? (100 * eixo.comPosicao) / eixo.barreiras : 100}%` }} />
              </div>
              {eixo.barreiras > 0 && (
                <Link href={`/gestao/diretor/declaracao?eixo=${eixo.eixo}`} className="mt-3 inline-block text-[12px] font-bold text-gov-blue hover:underline">
                  {eixo.comPosicao < eixo.barreiras ? "Registrar obstáculo →" : "Ver registros do eixo →"}
                </Link>
              )}
            </Cartao>
          ))}
        </div>
      </section>

      <section className="mt-8" aria-labelledby="titulo-barreiras">
        <div className="flex flex-wrap items-center gap-3">
          <h2 id="titulo-barreiras" className="text-lg font-extrabold text-gov-blue-dark">Barreiras e registros</h2>
          <Selo tom="neutro">{dados.barreiras.length} barreiras identificadas</Selo>
        </div>
        <p className="mt-1 text-[13px] text-gray-600">
          O dado do Censo e o relato da gestão permanecem distintos. Barreira sem registro não significa ausência de dificuldade.
        </p>
        <Cartao className="mt-3 overflow-x-auto">
          {dados.barreiras.length === 0 ? (
            <p className="p-5 text-sm text-gray-600">O Censo {dados.censoVersao} não indica barreiras para esta escola.</p>
          ) : (
            <table className="w-full min-w-[720px] text-left text-[13px]">
              <thead className="border-b border-black/5 text-[11px] uppercase tracking-wider text-gray-500">
                <tr>
                  <th scope="col" className="px-4 py-2.5">Barreira identificada</th>
                  <th scope="col" className="px-4 py-2.5">Eixo</th>
                  <th scope="col" className="px-4 py-2.5">Dado observado · Censo {dados.censoVersao}</th>
                  <th scope="col" className="px-4 py-2.5">Posição da escola</th>
                </tr>
              </thead>
              <tbody>
                {dados.barreiras.map((b) => (
                  <tr key={b.codigo} className="border-b border-black/5 last:border-0">
                    <td className="px-4 py-3 align-top">
                      <div className="font-bold text-ink">{b.nome}</div>
                      <div className="text-[11px] text-gray-500">{b.codigo} · {pontos(b.pontos)} pontos em jogo</div>
                    </td>
                    <td className="px-4 py-3 align-top">{b.eixo}</td>
                    <td className="px-4 py-3 align-top text-gray-700">
                      {b.dadoCenso}
                      {b.nota && <div className="mt-0.5 text-[11px] text-gray-500">Nota: {b.nota}.</div>}
                    </td>
                    <td className="px-4 py-3 align-top">
                      <Selo tom={POSICOES[b.posicao].tom}>{POSICOES[b.posicao].texto}</Selo>
                      {b.resumo && <div className="mt-1 max-w-[260px] text-[12px] text-gray-600">{b.resumo}</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Cartao>
        <p className="mt-2 text-[11px] text-gray-500">Barreiras pela metodologia v{dados.metodologiaVersao}, a partir dos dados do Censo.</p>
      </section>

      <div className="mt-8">
        <Aviso>
          Os indicadores vêm do Censo Escolar {dados.censoVersao} e não mudam com os registros da escola. O que você registrar fica
          visível à secretaria de educação só depois de emitido.
        </Aviso>
      </div>
    </div>
  );
}
