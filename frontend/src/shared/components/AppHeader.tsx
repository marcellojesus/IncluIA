"use client";

// Cabeçalho principal do app — navegação de topo + marca "Escola Sem Barreiras".
// Diferente do antigo ContextoMunicipioBar (abas dentro da tela de município), os itens
// "Escolas" e "Diagnóstico IA" agora são rotas de nível superior, escopadas ao município
// selecionado no filtro geográfico (GeoFiltroBar) — ver useAppStore.municipioSelecionado.
// A área pública não tem login: a única porta de entrada é a Gestão Ativa (/participar), para
// diretores e secretarias (login da Fase 1 desativado em 2026-10-27, impacto-fase-1.md).

import Link from "next/link";
import { usePathname } from "next/navigation";

import { destinoDoPapel } from "@/features/gestao-ativa/store";
import type { Papel } from "@/features/gestao-ativa/types";
import { useContaConectada } from "@/features/gestao-ativa/useContaConectada";
import { Logo } from "@/shared/components/Logo";
import { useAppStore } from "@/shared/store/useAppStore";

// Âncora dos cartões de acesso em /participar (ParticiparGestao).
export const ANCORA_ACESSO = "acesso";
const DESTAQUE = ["ring-4", "ring-accent/40", "rounded-xl"];
const PAPEL_CURTO: Record<Papel, string> = { diretor: "Diretor(a)", secretario: "Secretaria", admin: "Admin" };

type ItemNav = { href: string; label: string; ativo: (path: string) => boolean };

function itensNav(codigoIbge: number | undefined): ItemNav[] {
  const base = codigoIbge ? `/municipio/${codigoIbge}` : "/";
  return [
    { href: base, label: "Início", ativo: (p) => p === base || /^\/municipio\/\d+$/.test(p) },
    { href: `${base}/escolas`, label: "Escolas", ativo: (p) => p.endsWith("/escolas") },
    { href: "/comparar", label: "Comparar", ativo: (p) => p === "/comparar" },
    { href: `${base}/diagnostico`, label: "Diagnóstico IA", ativo: (p) => p.endsWith("/diagnostico") },
    { href: "/dados-abertos", label: "Dados abertos", ativo: (p) => p === "/dados-abertos" },
    { href: "/sobre", label: "Sobre", ativo: (p) => p === "/sobre" },
  ];
}

export function AppHeader() {
  const pathname = usePathname();
  const municipioSelecionado = useAppStore((s) => s.municipioSelecionado);
  // Quem já entrou na Gestão Ativa nesta aba vê outro botão ("Meu painel"), que leva ao painel do papel.
  const conta = useContaConectada();

  // Sem login, o botão é a porta de entrada (/participar). Estando já nela, ele funciona como âncora:
  // rola até os cartões de acesso e os destaca. Sem isso o clique não fazia nada, porque a rota não
  // muda e a rolagem fica no contêiner do layout, não na janela.
  function irParaAcesso(e: React.MouseEvent<HTMLAnchorElement>) {
    if (pathname !== "/participar") return;
    e.preventDefault();
    const alvo = document.getElementById(ANCORA_ACESSO);
    if (!alvo) return;
    alvo.scrollIntoView({ behavior: "smooth", block: "start" });
    alvo.focus({ preventScroll: true });
    alvo.classList.add(...DESTAQUE);
    window.setTimeout(() => alvo.classList.remove(...DESTAQUE), 1500);
  }

  return (
    <header className="flex-shrink-0 border-b border-black/5 bg-paper">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-6 py-3">
        <Link
          href={municipioSelecionado ? `/municipio/${municipioSelecionado.codigoIbge}` : "/"}
          className="flex items-center gap-3"
        >
          <Logo />
          <div>
            <div className="text-lg font-extrabold leading-none text-gov-blue-dark">
              Escola Sem Barreiras
            </div>
            <div className="mt-0.5 text-[11px] text-gray-400">
              Controle social da educação inclusiva
            </div>
          </div>
        </Link>

        <nav className="ml-2 flex flex-wrap items-center gap-1">
          {itensNav(municipioSelecionado?.codigoIbge).map((item) => {
            const ativo = pathname ? item.ativo(pathname) : false;
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`relative rounded px-3 py-2 text-sm font-semibold transition-colors ${
                  ativo ? "text-gov-blue-dark" : "text-gray-500 hover:text-gov-blue-dark"
                }`}
              >
                {item.label}
                {ativo && (
                  <span className="absolute inset-x-3 -bottom-[13px] h-[3px] rounded-full bg-accent" />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-4">
          {conta ? (
            <Link
              href={destinoDoPapel(conta.papel)}
              title={`Conectado como ${conta.nome}. Ir para o seu painel da Gestão Ativa`}
              className="flex items-center gap-2 rounded-full border-2 border-gov-blue bg-white px-4 py-1.5 text-xs font-extrabold text-gov-blue hover:bg-gov-blue-lt"
            >
              <span aria-hidden className="h-2 w-2 rounded-full bg-[#2f9e6b]" />
              Meu painel
              <span className="font-semibold text-gray-500">· {PAPEL_CURTO[conta.papel]}</span>
            </Link>
          ) : (
            <Link
              href="/participar"
              onClick={irParaAcesso}
              title="Para diretores de escola e secretarias de educação"
              className="rounded-full bg-accent px-4 py-2 text-xs font-extrabold text-white hover:bg-accent-dark"
            >
              Gestão Ativa
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
