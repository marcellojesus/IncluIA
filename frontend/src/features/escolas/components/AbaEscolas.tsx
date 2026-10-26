"use client";

// Ver interface.md §6 — composição completa da aba Escolas. As escolas que publicaram o Plano de Ação
// (Gestão Ativa) aparecem primeiro, numa lista própria; as demais vêm em seguida.
import { useEffect, useState } from "react";

import { type PublicacaoGestao, getEscolasPorMunicipio, getPublicacoesGestao } from "../api";
import type { Escola } from "../types";
import { ListaEscolas } from "./ListaEscolas";
import { ModalEscola } from "./ModalEscola";

type Filtro = "" | "critica" | "sem-aee" | "com-plano";

// RN-03 de docs/business-rules/escolas.md: filtros mutuamente exclusivos, sem combinação.
function aplicarFiltro(escolas: Escola[], filtro: Filtro, publicacoes: Record<number, PublicacaoGestao>): Escola[] {
  if (filtro === "critica") return escolas.filter((e) => e.score < 3);
  if (filtro === "sem-aee") return escolas.filter((e) => e.statusEixoI === "nok");
  if (filtro === "com-plano") return escolas.filter((e) => publicacoes[e.coEntidade]?.planoVersao);
  return escolas;
}

function TituloLista({ titulo, quantidade, tom }: { titulo: string; quantidade: number; tom: "verde" | "neutro" }) {
  return (
    <h3 className="mt-2 flex items-center gap-2 text-[13px] font-extrabold uppercase tracking-wider text-gov-blue-dark">
      <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${tom === "verde" ? "bg-[#2f9e6b]" : "bg-gray-300"}`} />
      {titulo}
      <span className="rounded-full bg-black/[.06] px-2 py-0.5 text-[11px] text-gray-600">{quantidade}</span>
    </h3>
  );
}

export function AbaEscolas({ codigoIbge }: { codigoIbge: number }) {
  const [escolas, setEscolas] = useState<Escola[] | null>(null);
  const [publicacoes, setPublicacoes] = useState<Record<number, PublicacaoGestao>>({});
  const [erro, setErro] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("");
  const [escolaSelecionada, setEscolaSelecionada] = useState<Escola | null>(null);

  useEffect(() => {
    getEscolasPorMunicipio(codigoIbge)
      .then(setEscolas)
      .catch(() => setErro("Não foi possível carregar as escolas deste município."));
    // Falha aqui não derruba a lista: só ficam sem os selos da Gestão Ativa.
    getPublicacoesGestao(codigoIbge)
      .then((lista) => setPublicacoes(Object.fromEntries(lista.map((p) => [p.coEntidade, p]))))
      .catch(() => setPublicacoes({}));
  }, [codigoIbge]);

  if (erro) {
    return <p className="p-5 text-sm text-gov-red">{erro}</p>;
  }
  if (!escolas) {
    return <p className="p-5 text-sm text-gray-400">Carregando escolas…</p>;
  }

  const escolasFiltradas = aplicarFiltro(escolas, filtro, publicacoes);
  const comPlano = escolasFiltradas.filter((e) => publicacoes[e.coEntidade]?.planoVersao);
  const semPlano = escolasFiltradas.filter((e) => !publicacoes[e.coEntidade]?.planoVersao);
  const totalComPlano = escolas.filter((e) => publicacoes[e.coEntidade]?.planoVersao).length;
  const totalComDeclaracao = escolas.filter((e) => publicacoes[e.coEntidade]).length;

  return (
    <div className="flex flex-col gap-3">
      <section aria-label="Transparência da gestão" className="flex flex-col gap-3 rounded-2xl bg-paper p-5 shadow-sm sm:flex-row sm:items-center">
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-extrabold text-[#2f7a55]">{totalComPlano}</span>
          <span className="text-sm text-gray-600">de {escolas.length} escolas</span>
        </div>
        <div className="flex-1">
          <p className="text-[14px] font-bold text-gov-blue-dark">publicaram o Plano de Ação aceito pela secretaria</p>
          <p className="text-[12px] text-gray-500">
            {totalComDeclaracao} {totalComDeclaracao === 1 ? "escola publicou" : "escolas publicaram"} a Declaração de Obstáculos. Escola sem
            publicação não é escola sem dificuldade: a gestão ainda não publicou seus registros.
          </p>
        </div>
        {totalComPlano > 0 && filtro !== "com-plano" && (
          <button onClick={() => setFiltro("com-plano")} className="shrink-0 rounded-lg border-2 border-[#2f9e6b] px-3 py-1.5 text-xs font-bold text-[#2f7a55] hover:bg-[#e7f3ec]">
            Ver só as com plano
          </button>
        )}
      </section>

      <div className="flex items-center justify-end gap-2">
        <select
          value={filtro}
          onChange={(e) => setFiltro(e.target.value as Filtro)}
          className="rounded-lg border border-gray-300 bg-paper px-2.5 py-1.5 text-xs font-semibold text-gov-blue-dark"
        >
          <option value="">Todas as escolas</option>
          <option value="com-plano">Com Plano de Ação publicado</option>
          <option value="critica">Situação crítica</option>
          <option value="sem-aee">Sem AEE</option>
        </select>
        <button
          disabled
          title="Disponível em uma fase futura"
          className="cursor-not-allowed rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-400"
        >
          📄 Exportar (em breve)
        </button>
      </div>

      {comPlano.length > 0 && (
        <>
          <TituloLista titulo="Com Plano de Ação publicado" quantidade={comPlano.length} tom="verde" />
          <ListaEscolas escolas={comPlano} onSelecionar={setEscolaSelecionada} publicacoes={publicacoes} />
        </>
      )}
      {filtro !== "com-plano" && (
        <>
          {comPlano.length > 0 && <TituloLista titulo="Sem Plano de Ação publicado" quantidade={semPlano.length} tom="neutro" />}
          <ListaEscolas escolas={semPlano} onSelecionar={setEscolaSelecionada} publicacoes={publicacoes} />
        </>
      )}

      {escolaSelecionada && (
        <ModalEscola escola={escolaSelecionada} onFechar={() => setEscolaSelecionada(null)} />
      )}
    </div>
  );
}
