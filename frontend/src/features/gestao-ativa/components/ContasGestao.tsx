"use client";

// Visão do administrador do piloto: quem tem conta na Gestão Ativa, com qual e-mail e onde.
// Agrupa por município: primeiro a secretaria, depois os diretores com a escola e o código INEP.
import { useEffect, useMemo, useState } from "react";

import { listarContas } from "../api";
import type { ContaDaGestao } from "../types";
import { Cartao, Erro, Selo } from "./ui";

type Tom = "ambar" | "verde" | "vermelho" | "neutro" | "azul";

function situacao(conta: ContaDaGestao): { texto: string; tom: Tom } {
  if (conta.estado === "pendente") {
    return conta.pedidoConfirmado
      ? { texto: "Aguardando a secretaria", tom: "ambar" }
      : { texto: "Pedido sem confirmação do e-mail", tom: "neutro" };
  }
  if (conta.estado === "aprovado") {
    return conta.emailConfirmado ? { texto: "Ativo", tom: "verde" } : { texto: "Aguardando o 1º acesso", tom: "azul" };
  }
  if (conta.estado === "suspenso") return { texto: "Suspenso", tom: "vermelho" };
  return { texto: conta.estado === "rejeitado" ? "Rejeitado" : "Revogado", tom: "neutro" };
}

type Grupo = { chave: number; municipio: string; uf: string; secretarias: ContaDaGestao[]; diretores: ContaDaGestao[] };

function agrupar(contas: ContaDaGestao[]): Grupo[] {
  const grupos = new Map<number, Grupo>();
  for (const conta of contas) {
    const grupo = grupos.get(conta.coMunicipio) ?? {
      chave: conta.coMunicipio, municipio: conta.municipio, uf: conta.uf, secretarias: [], diretores: [],
    };
    (conta.papel === "secretario" ? grupo.secretarias : grupo.diretores).push(conta);
    grupos.set(conta.coMunicipio, grupo);
  }
  return [...grupos.values()];
}

function Linha({ conta }: { conta: ContaDaGestao }) {
  const s = situacao(conta);
  return (
    <tr className="border-t border-black/5 align-top">
      <td className="py-2.5 pr-4">
        {conta.papel === "diretor" ? (
          <>
            <div className="font-bold text-gov-blue-dark">{conta.escola ?? "Escola não encontrada no Censo"}</div>
            <div className="text-xs text-gray-400">INEP {conta.coEntidade}</div>
          </>
        ) : (
          <div className="font-bold text-gov-blue-dark">Secretaria de educação</div>
        )}
      </td>
      <td className="py-2.5 pr-4 text-gray-700">{conta.nome}</td>
      <td className="py-2.5 pr-4">
        <a href={`mailto:${conta.email}`} className="break-all font-mono text-[13px] text-gov-blue underline-offset-2 hover:underline">
          {conta.email}
        </a>
      </td>
      <td className="py-2.5 pr-4"><Selo tom={s.tom}>{s.texto}</Selo></td>
      <td className="whitespace-nowrap py-2.5 text-xs text-gray-400">{new Date(conta.criadoEm).toLocaleDateString("pt-BR")}</td>
    </tr>
  );
}

export function ContasGestao() {
  const [contas, setContas] = useState<ContaDaGestao[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [busca, setBusca] = useState("");

  useEffect(() => {
    listarContas().then(setContas).catch((falha) => setErro((falha as Error).message));
  }, []);

  const grupos = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase("pt-BR");
    const filtradas = (contas ?? []).filter((c) =>
      !termo || [c.nome, c.email, c.municipio, c.uf, c.escola ?? "", String(c.coEntidade ?? ""), String(c.coMunicipio)]
        .some((campo) => campo.toLocaleLowerCase("pt-BR").includes(termo)),
    );
    return agrupar(filtradas);
  }, [contas, busca]);

  const total = (papel: ContaDaGestao["papel"]) => (contas ?? []).filter((c) => c.papel === papel).length;

  return (
    <div className="mx-auto max-w-5xl px-6 py-6">
      <p className="text-xs font-extrabold uppercase tracking-wider text-accent">Administração</p>
      <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Contas da Gestão Ativa</h1>
      <p className="mt-2 text-[15px] text-gray-600">
        Secretarias e diretores com o e-mail usado para entrar, o município e a escola. Uso restrito à operação do piloto.
      </p>

      <Erro mensagem={erro} />

      {contas && (
        <>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Selo tom="azul">{total("secretario")} secretaria(s)</Selo>
            <Selo tom="teal">{total("diretor")} diretor(es)</Selo>
            <input
              type="search"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nome, e-mail, município, escola ou INEP"
              aria-label="Buscar contas"
              className="ml-auto w-full rounded-lg border border-black/10 bg-white px-3 py-2 text-sm sm:w-80"
            />
          </div>

          {grupos.length === 0 && (
            <Cartao className="mt-4 p-6 text-center text-sm text-gray-500">
              {contas.length === 0 ? "Nenhuma conta de secretaria ou diretor ainda." : "Nada encontrado para essa busca."}
            </Cartao>
          )}

          {grupos.map((g) => (
            <Cartao key={g.chave} className="mt-4 overflow-x-auto p-5">
              <div className="flex flex-wrap items-baseline gap-x-3">
                <h2 className="text-lg font-extrabold text-gov-blue-dark">{g.municipio || "Município não encontrado"}{g.uf && `/${g.uf}`}</h2>
                <span className="text-xs text-gray-400">IBGE {g.chave}</span>
                {g.secretarias.length === 0 && <Selo tom="ambar">Sem secretaria habilitada</Selo>}
              </div>
              <table className="mt-3 w-full min-w-[640px] text-left text-sm">
                <thead>
                  <tr className="text-[11px] font-extrabold uppercase tracking-wide text-gray-400">
                    <th className="pb-1.5 pr-4">Local</th>
                    <th className="pb-1.5 pr-4">Nome</th>
                    <th className="pb-1.5 pr-4">E-mail</th>
                    <th className="pb-1.5 pr-4">Situação</th>
                    <th className="pb-1.5">Desde</th>
                  </tr>
                </thead>
                <tbody>
                  {[...g.secretarias, ...g.diretores].map((c) => <Linha key={`${c.email}`} conta={c} />)}
                </tbody>
              </table>
            </Cartao>
          ))}
        </>
      )}
      {!contas && !erro && <p className="mt-5 text-sm text-gray-400">Carregando contas…</p>}
    </div>
  );
}
