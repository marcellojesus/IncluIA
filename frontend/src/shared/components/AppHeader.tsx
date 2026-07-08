"use client";

// Cabeçalho principal do app — navegação de topo + marca "Escola Sem Barreiras".
// Diferente do antigo ContextoMunicipioBar (abas dentro da tela de município), os itens
// "Escolas" e "Diagnóstico IA" agora são rotas de nível superior, escopadas ao município
// selecionado no filtro geográfico (GeoFiltroBar) — ver useAppStore.municipioSelecionado.

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { BotaoRegistrarBarreira } from "@/shared/components/BotaoRegistrarBarreira";
import { Logo } from "@/shared/components/Logo";
import { useAppStore } from "@/shared/store/useAppStore";

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
  const router = useRouter();
  const pathname = usePathname();
  const usuario = useAppStore((s) => s.usuario);
  const logout = useAppStore((s) => s.logout);
  const municipioSelecionado = useAppStore((s) => s.municipioSelecionado);

  function handleSair() {
    logout();
    router.push("/login");
  }

  return (
    <header className="flex-shrink-0 border-b border-black/5 bg-paper">
      <div className="flex items-center gap-6 px-6 py-3">
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

        <nav className="ml-2 flex items-center gap-1">
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
          <BotaoRegistrarBarreira className="rounded-full bg-accent px-4 py-2 text-xs font-extrabold text-white hover:bg-accent-dark">
            Registrar barreira
          </BotaoRegistrarBarreira>
          {usuario ? (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span>
                👤 <strong className="text-gov-blue-dark">{usuario.nome}</strong>
              </span>
              <button onClick={handleSair} className="underline underline-offset-2 hover:text-gov-blue-dark">
                Sair
              </button>
            </div>
          ) : (
            <Link href="/login" className="text-xs font-semibold text-gray-500 underline underline-offset-2 hover:text-gov-blue-dark">
              Entrar
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
