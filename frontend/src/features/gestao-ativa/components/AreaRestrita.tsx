"use client";

// Moldura das páginas da Gestão Ativa: confere a sessão no servidor (/gestao/eu) ao abrir, mostra a
// faixa privada do protótipo ("Área restrita" + escopo) e manda para a entrada quem não tem acesso.
// A proteção real está no backend (RN-07); aqui só se evita mostrar uma tela vazia.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useSyncExternalStore } from "react";

import { Logo } from "@/shared/components/Logo";

import { SemAcesso, getEu } from "../api";
import { destinoDoPapel, useGestaoStore } from "../store";
import { rotulosDaRede } from "../rotulos";
import type { Eu, Papel } from "../types";

const ROTULO_PAPEL: Record<Papel, string> = { diretor: "Diretor(a)", secretario: "Secretaria municipal", admin: "Administração" };

function escopoTexto(eu: Eu): string {
  const { escola, coEntidade, municipio, uf } = eu.escopo;
  if (escola) return `${escola} · INEP ${coEntidade}`;
  if (municipio) return `${rotulosDaRede(uf).rede.replace(/^r/, "R")} de ${municipio}/${uf}`;
  return "Administração do produto";
}

export function AreaRestrita({ papel, children }: { papel: Papel; children: (eu: Eu) => React.ReactNode }) {
  const router = useRouter();
  const token = useGestaoStore((s) => s.token);
  const sair = useGestaoStore((s) => s.sair);
  const definirEu = useGestaoStore((s) => s.definirEu);
  const [eu, setEu] = useState<Eu | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  // A sessão salva no navegador carrega depois da primeira renderização; só então dá para decidir.
  const hidratado = useSyncExternalStore(
    (avisar) => useGestaoStore.persist.onFinishHydration(avisar),
    () => useGestaoStore.persist.hasHydrated(),
    () => false,
  );

  useEffect(() => {
    if (!hidratado) return;
    if (!token) {
      router.replace("/gestao/entrar");
      return;
    }
    getEu()
      .then((dados) => {
        definirEu(dados);
        if (dados.papel !== papel) router.replace(destinoDoPapel(dados.papel));
        else setEu(dados);
      })
      .catch((falha) => {
        if (falha instanceof SemAcesso) {
          sair();
          router.replace("/gestao/entrar");
        } else setErro((falha as Error).message);
      });
  }, [hidratado, token, papel, router, sair, definirEu]);

  function handleSair() {
    sair();
    router.push("/participar");
  }

  return (
    <div className="flex min-h-screen flex-col bg-cream">
      <div aria-hidden className="h-[5px] bg-[linear-gradient(90deg,#2f9e6b_0_33%,#e6b800_33%_66%,#426b95_66%)]" />
      <header className="border-b border-black/5 bg-paper">
        <div className="flex items-center gap-4 px-6 py-3">
          <Link href="/" className="flex items-center gap-3">
            <Logo />
            <span className="text-lg font-extrabold text-gov-blue-dark">Escola Sem Barreiras</span>
          </Link>
          {eu && (
            <div className="ml-auto flex items-center gap-3 text-[13px]">
              <span className="text-gray-600">
                {eu.papel === "secretario" ? rotulosDaRede(eu.escopo.uf).secretaria : ROTULO_PAPEL[eu.papel]} · <strong className="text-ink">{eu.nome}</strong>
              </span>
              <button onClick={handleSair} className="rounded-lg px-3 py-1.5 font-bold text-gov-blue hover:bg-gov-blue-lt">
                Sair
              </button>
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3 bg-gov-blue-dark px-6 py-2 text-[12px] text-white/80">
          <span className="rounded-full bg-accent px-2.5 py-0.5 text-[11px] font-extrabold text-white">Área restrita</span>
          {eu && <strong className="text-white">{escopoTexto(eu)}</strong>}
          <span>Gestão Ativa · dados privados · Censo Escolar 2025</span>
        </div>
      </header>

      <main className="flex-1">
        {erro ? (
          <p role="alert" className="mx-auto mt-10 max-w-md rounded-lg bg-[#fbe9e7] p-4 text-sm text-[#b23838]">
            {erro}
          </p>
        ) : eu ? (
          children(eu)
        ) : (
          <p className="mt-16 text-center text-sm text-gray-500" role="status">
            Conferindo seu acesso…
          </p>
        )}
      </main>
    </div>
  );
}
