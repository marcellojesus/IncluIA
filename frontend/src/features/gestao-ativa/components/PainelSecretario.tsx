"use client";

// Painel do secretário municipal: fila de Planos de Ação, Plano Estratégico Municipal, Declarações e vínculos.
// O topo destaca o que depende do secretário (planos aguardando análise, pedidos de acesso a validar).
import { useCallback, useEffect, useState } from "react";

import { getFilaPlanos, listarVinculos } from "../api";
import type { Eu } from "../types";
import { DeclaracoesRede } from "./DeclaracoesRede";
import { FilaPlanos } from "./FilaPlanos";
import { PlanoMunicipal } from "./PlanoMunicipal";
import { VinculosSecretario } from "./VinculosSecretario";

type Aba = "planos" | "municipal" | "declaracoes" | "vinculos";

type Pendencias = { planos: number; planoMaisAntigo: string | null; vinculos: number; vinculoMaisAntigo: string | null };

const DIA = 24 * 60 * 60 * 1000;

function espera(iso: string | null) {
  if (!iso) return "";
  const dias = Math.floor((Date.now() - new Date(iso).getTime()) / DIA);
  return dias <= 0 ? "o mais antigo chegou hoje" : `o mais antigo espera há ${dias} ${dias === 1 ? "dia" : "dias"}`;
}

function maisAntigo(datas: string[]) {
  return datas.length ? datas.reduce((a, b) => (a < b ? a : b)) : null;
}

export function PainelSecretario({ eu }: { eu: Eu }) {
  const [aba, setAba] = useState<Aba>("planos");
  const [pendencias, setPendencias] = useState<Pendencias | null>(null);

  const atualizar = useCallback(async () => {
    try {
      const [fila, vinculos] = await Promise.all([getFilaPlanos(), listarVinculos("pendentes")]);
      const aguardando = fila.planos.filter((p) => p.estado === "aguardando_analise");
      setPendencias({
        planos: aguardando.length,
        planoMaisAntigo: maisAntigo(aguardando.map((p) => p.submetidaEm)),
        vinculos: vinculos.length,
        vinculoMaisAntigo: maisAntigo(vinculos.map((v) => v.criadoEm)),
      });
    } catch {
      setPendencias(null); // o aviso é um atalho; as abas continuam mostrando os próprios erros
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial vinda da API
    atualizar();
  }, [atualizar]);

  const contagem: Record<Aba, number> = { planos: pendencias?.planos ?? 0, municipal: 0, declaracoes: 0, vinculos: pendencias?.vinculos ?? 0 };
  const total = contagem.planos + contagem.vinculos;

  return (
    <div>
      <div className="mx-auto max-w-6xl px-6 pt-6">
        <p className="text-xs font-extrabold uppercase tracking-wider text-accent">
          Secretaria municipal · {eu.escopo.municipio}/{eu.escopo.uf}
        </p>

        {pendencias && total > 0 && (
          <section
            role="status"
            aria-labelledby="titulo-pendencias-secretaria"
            className="mt-3 rounded-lg border-l-[6px] border-accent bg-[#fdece8] p-5"
          >
            <p className="text-xs font-extrabold uppercase tracking-wider text-accent-dark">Ação necessária</p>
            <h2 id="titulo-pendencias-secretaria" className="mt-1 text-xl font-extrabold text-gov-blue-dark">
              {total === 1 ? "Há 1 pendência aguardando você" : `Há ${total} pendências aguardando você`}
            </h2>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {pendencias.planos > 0 && (
                <Pendencia
                  numero={pendencias.planos}
                  titulo={pendencias.planos === 1 ? "Plano de Ação aguardando análise" : "Planos de Ação aguardando análise"}
                  detalhe={`As escolas esperam a decisão para seguir com o planejamento; ${espera(pendencias.planoMaisAntigo)}.`}
                  botao="Analisar planos →"
                  onClick={() => setAba("planos")}
                />
              )}
              {pendencias.vinculos > 0 && (
                <Pendencia
                  numero={pendencias.vinculos}
                  titulo={pendencias.vinculos === 1 ? "Pedido de acesso de diretor" : "Pedidos de acesso de diretores"}
                  detalhe={`Sem a sua validação o diretor não entra na Gestão Ativa; ${espera(pendencias.vinculoMaisAntigo)}.`}
                  botao="Validar pedidos →"
                  onClick={() => setAba("vinculos")}
                />
              )}
            </div>
          </section>
        )}

        <div role="tablist" aria-label="Áreas da secretaria" className="mt-4 flex gap-1 border-b border-black/10">
          {(
            [
              ["planos", "Planos das escolas"],
              ["municipal", "Plano municipal"],
              ["declaracoes", "Declarações das escolas"],
              ["vinculos", "Vínculos de diretores"],
            ] as [Aba, string][]
          ).map(([id, rotulo]) => (
            <button
              key={id}
              role="tab"
              aria-selected={aba === id}
              onClick={() => setAba(id)}
              className={`-mb-px flex items-center gap-2 border-b-[3px] px-4 py-2 text-sm font-bold ${aba === id ? "border-accent text-gov-blue-dark" : "border-transparent text-gray-500 hover:text-gov-blue-dark"}`}
            >
              {rotulo}
              {contagem[id] > 0 && (
                <span className="rounded-full bg-accent px-2 py-0.5 text-[11px] font-extrabold text-white">
                  {contagem[id]}
                  <span className="sr-only"> pendente(s)</span>
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
      {aba === "planos" ? (
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-3xl font-extrabold text-gov-blue-dark">Planos de Ação das escolas</h1>
          <p className="mb-5 mt-2 max-w-3xl text-[15px] text-gray-600">
            Versões enviadas pelas escolas da rede para análise. Rascunhos e sugestões do assistente ficam com a escola.
          </p>
          <FilaPlanos onMudou={atualizar} />
        </div>
      ) : aba === "municipal" ? (
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-3xl font-extrabold text-gov-blue-dark">Plano Estratégico Municipal</h1>
          <p className="mb-5 mt-2 max-w-3xl text-[15px] text-gray-600">
            Um plano para a rede, a partir dos Planos de Ação aceitos das escolas: o assistente junta necessidades comuns e propõe ações
            municipais; você decide, ajusta e confirma.
          </p>
          <PlanoMunicipal />
        </div>
      ) : aba === "declaracoes" ? (
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-3xl font-extrabold text-gov-blue-dark">Declarações de Obstáculos</h1>
          <p className="mb-5 mt-2 max-w-3xl text-[15px] text-gray-600">
            Versões emitidas pelas escolas da rede municipal. Rascunhos das escolas não aparecem aqui.
          </p>
          <DeclaracoesRede />
        </div>
      ) : (
        <VinculosSecretario eu={eu} onMudou={atualizar} />
      )}
    </div>
  );
}

function Pendencia({ numero, titulo, detalhe, botao, onClick }: { numero: number; titulo: string; detalhe: string; botao: string; onClick: () => void }) {
  return (
    <div className="flex flex-col justify-between gap-3 rounded-lg bg-white p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="text-3xl font-extrabold leading-none text-accent">{numero}</span>
        <div>
          <p className="text-[15px] font-extrabold text-ink">{titulo}</p>
          <p className="mt-0.5 text-[12px] text-gray-600">{detalhe}</p>
        </div>
      </div>
      <button
        onClick={onClick}
        className="chamar-atencao self-start rounded-lg bg-accent px-5 py-2.5 text-sm font-extrabold text-white shadow-md hover:bg-accent-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {botao}
      </button>
    </div>
  );
}
