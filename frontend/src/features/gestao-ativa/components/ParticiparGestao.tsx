"use client";

// Porta de entrada da Gestão Ativa (view-participar do protótipo v2).
import Link from "next/link";
import { useState } from "react";

import { ANCORA_ACESSO } from "@/shared/components/AppHeader";

import { destinoDoPapel, useGestaoStore } from "../store";
import { useContaConectada } from "../useContaConectada";
import { SolicitarAcesso } from "./SolicitarAcesso";
import { Aviso, Botao, Cartao, Selo } from "./ui";

const ETAPAS = [
  { titulo: "1 · Barreiras", texto: "O Censo Escolar indica as barreiras de cada escola, com regra pública e versionada." },
  { titulo: "2 · Declaração", texto: "O diretor registra a posição da escola sobre cada barreira e emite a Declaração de Obstáculos." },
  { titulo: "3 · Planos", texto: "A escola propõe ações; a secretaria analisa e organiza o plano da rede." },
];

export function ParticiparGestao() {
  const [solicitando, setSolicitando] = useState(false);
  const conta = useContaConectada();
  const sair = useGestaoStore((s) => s.sair);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {conta && (
        <div className="mb-6">
          <Aviso>
            Você já entrou na Gestão Ativa como <strong>{conta.nome}</strong>.{" "}
            <Link href={destinoDoPapel(conta.papel)} className="font-bold text-gov-blue underline underline-offset-2">
              Ir para o seu painel
            </Link>{" "}
            ·{" "}
            <button onClick={sair} className="font-bold text-gov-blue underline underline-offset-2">
              Sair
            </button>
          </Aviso>
        </div>
      )}
      <p className="text-xs font-extrabold uppercase tracking-wider text-accent">Participar</p>
      <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Gestão Ativa</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-gray-600">
        Área restrita para diretores de escola e secretarias municipais transformarem as barreiras identificadas no Censo em
        registros, declarações e planos de ação.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {ETAPAS.map((etapa) => (
          <Cartao key={etapa.titulo} className="p-4">
            <h2 className="text-sm font-extrabold text-gov-blue-dark">{etapa.titulo}</h2>
            <p className="mt-1 text-[13px] text-gray-600">{etapa.texto}</p>
          </Cartao>
        ))}
      </div>

      <div id={ANCORA_ACESSO} tabIndex={-1} className="mt-6 grid scroll-mt-4 gap-4 outline-none transition-shadow md:grid-cols-2">
        <Cartao className="p-5">
          <Selo tom="azul">Diretor de escola</Selo>
          <h2 className="mt-2 text-lg font-extrabold text-gov-blue-dark">Acesso com vínculo validado</h2>
          <p className="mt-1 text-[13px] text-gray-600">
            Informe o código INEP da escola. O acesso é liberado após a validação do vínculo pela secretaria de educação.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Botao onClick={() => setSolicitando(true)}>Solicitar acesso</Botao>
            <Link href="/gestao/entrar" className="inline-flex items-center rounded-lg border border-gov-blue px-4 py-2 text-sm font-bold text-gov-blue hover:bg-gov-blue-lt">
              Já tenho acesso
            </Link>
          </div>
        </Cartao>
        <Cartao className="p-5">
          <Selo tom="teal">Secretaria de educação</Selo>
          <h2 className="mt-2 text-lg font-extrabold text-gov-blue-dark">Acesso por convite</h2>
          <p className="mt-1 text-[13px] text-gray-600">
            Secretarias municipais são habilitadas pela equipe da Escola Sem Barreiras, após confirmação por canal institucional.
          </p>
          <div className="mt-4">
            <Link href="/gestao/entrar" className="inline-flex items-center rounded-lg bg-gov-blue px-4 py-2 text-sm font-bold text-white hover:bg-gov-blue-mid">
              Entrar
            </Link>
          </div>
        </Cartao>
      </div>

      <div className="mt-6 space-y-3">
        <Aviso>
          <strong>Não é diretor nem da secretaria?</strong> A área pública não precisa de cadastro: veja o índice do seu município e, na aba
          Escolas, as barreiras de cada escola e o que ela publicou na Gestão Ativa.{" "}
          <Link href="/" className="font-bold text-gov-blue underline underline-offset-2">
            Ir para a área pública
          </Link>
        </Aviso>
        <Aviso>
          <strong>Sem gov.br nesta versão.</strong> A confirmação de e-mail prova o controle do canal; o vínculo com a escola ou a
          rede é validado à parte.
        </Aviso>
      </div>

      {solicitando && <SolicitarAcesso onFechar={() => setSolicitando(false)} />}
    </div>
  );
}
