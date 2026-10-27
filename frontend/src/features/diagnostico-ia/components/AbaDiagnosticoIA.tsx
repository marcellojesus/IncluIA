"use client";

// Ver interface.md §7. Narrativa pública do município (impacto-fase-1.md, opção 2): só leitura, sem
// login e sem chat, escrita uma vez por edição do Censo. Rotulada como texto gerado por IA (PUB-05).
import Link from "next/link";
import { useEffect, useState } from "react";

import { Panel } from "@/shared/components/Panel";
import { getNarrativa } from "../api";
import type { NarrativaMunicipio } from "../types";
import { DiagnosticoEixoCard } from "./DiagnosticoEixoCard";

export function AbaDiagnosticoIA({ codigoIbge }: { codigoIbge: number }) {
  const [narrativa, setNarrativa] = useState<NarrativaMunicipio | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    getNarrativa(codigoIbge)
      .then((dados) => ativo && setNarrativa(dados))
      .catch((falha) => ativo && setErro((falha as Error).message));
    return () => {
      ativo = false;
    };
  }, [codigoIbge]);

  if (erro) return <p className="text-sm text-gov-red">{erro}</p>;

  if (!narrativa) {
    return (
      <div role="status" className="flex flex-col items-center justify-center gap-2 py-16 text-sm text-gray-400">
        Carregando a leitura do município…
      </div>
    );
  }

  const comIA = narrativa.eixos.filter((e) => e.modeloUsado !== "dados_brutos");
  const modelos = Array.from(new Set(comIA.map((e) => e.modeloUsado)));
  const geradoEm = comIA[0]?.geradoEm;

  return (
    <div className="flex flex-col gap-3">
      <p className="rounded-r border-l-4 border-gov-blue bg-gov-blue-lt px-4 py-3 text-[13px] leading-relaxed text-ink">
        <strong>Texto gerado por inteligência artificial</strong>
        {modelos.length > 0 && <> ({modelos.join(", ")})</>} a partir dos dados do Censo Escolar {narrativa.censoVersao}
        {geradoEm && <>, em {new Date(geradoEm).toLocaleDateString("pt-BR")}</>}. A IA só explica os números: a situação de cada eixo vem do
        cálculo do índice, não da IA. É uma leitura dos dados, não um parecer jurídico nem um plano de ação.
        {comIA.length < narrativa.eixos.length && (
          <> Alguns eixos mostram só o dado calculado, porque a IA não respondeu; a leitura completa será escrita depois.</>
        )}
      </p>

      <Panel titulo="Leitura por eixo da PNEEI">
        {narrativa.eixos.map((eixo) => (
          <DiagnosticoEixoCard key={eixo.eixo} diagnostico={eixo} />
        ))}
      </Panel>

      <p className="text-[12px] text-gray-500">
        Quer saber o que cada escola fez diante das barreiras? Veja as Declarações de Obstáculos e os Planos de Ação publicados na{" "}
        <Link href={`/municipio/${codigoIbge}/escolas`} className="font-semibold text-gov-blue underline underline-offset-2">
          aba Escolas
        </Link>
        .
      </p>
    </div>
  );
}
