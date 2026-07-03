"use client";

// Componente do Design System Gov.br — ver interface.md §0 "Header do app".

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAppStore } from "@/shared/store/useAppStore";

export function AppHeader() {
  const router = useRouter();
  const usuario = useAppStore((s) => s.usuario);
  const logout = useAppStore((s) => s.logout);

  const nome = usuario?.nome ?? "Convidado";
  const cargo = usuario
    ? `Sec. de Educação ${usuario.perfil === "municipal" ? "Municipal" : "Estadual"} · ${usuario.uf}`
    : "Sessão não iniciada";

  function handleSair() {
    logout();
    router.push("/login");
  }

  return (
    <div className="flex flex-shrink-0 items-center bg-gov-blue px-6 py-2.5">
      <Link href="/mapa">
        <div className="text-lg font-bold text-white">IncluIA</div>
        <div className="-mt-0.5 text-[11px] text-white/60">
          Governança da Inclusão Escolar · Censo 2025
        </div>
      </Link>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-white/80">
          👤 <strong className="text-white">{nome}</strong> — {cargo}
        </span>
        {usuario ? (
          <button onClick={handleSair} className="text-[11px] text-white/50 underline">
            Sair
          </button>
        ) : (
          <Link href="/login" className="text-[11px] text-white/50 underline">
            Entrar
          </Link>
        )}
      </div>
    </div>
  );
}
