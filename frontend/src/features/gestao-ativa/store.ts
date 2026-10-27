import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { Eu } from "./types";

// Sessão da Gestão Ativa, a única do produto: a área pública não tem login desde 2026-10-27
// (RF-12 do acesso). O token só identifica a conta; o
// servidor confere conta e vínculo a cada requisição.
//
// Só o token é guardado, e só na aba (sessionStorage): computadores de escola são compartilhados,
// e nome e e-mail vêm de /gestao/eu a cada abertura (revisão do AgLGPD de 2026-10-23).
type GestaoState = {
  token: string | null;
  eu: Eu | null;
  entrar: (token: string) => void;
  definirEu: (eu: Eu) => void;
  sair: () => void;
};

export const useGestaoStore = create<GestaoState>()(
  persist(
    (set) => ({
      token: null,
      eu: null,
      entrar: (token) => set({ token, eu: null }),
      definirEu: (eu) => set({ eu }),
      sair: () => set({ token: null, eu: null }),
    }),
    {
      name: "escola-sem-barreiras-gestao",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (estado) => ({ token: estado.token }),
    },
  ),
);

export function destinoDoPapel(papel: Eu["papel"]): string {
  return { diretor: "/gestao/diretor", secretario: "/gestao/secretario", admin: "/gestao/admin" }[papel];
}
