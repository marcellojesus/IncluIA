import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { LoginResponse } from "@/features/login/types";

export type MunicipioSelecionado = {
  codigoIbge: number;
  nome: string;
  uf: string;
  score: number;
};

type AppState = {
  usuario: LoginResponse | null;
  municipioSelecionado: MunicipioSelecionado | null;
  login: (usuario: LoginResponse) => void;
  logout: () => void;
  setMunicipioSelecionado: (municipio: MunicipioSelecionado | null) => void;
};

// Estado global (arquitetura.md): usuário autenticado e município selecionado.
// `usuario` persiste em localStorage (RF-03 de docs/requirements/login.md — sessão sobrevive
// a recarregar a página); `logout()` limpa tudo, inclusive o município selecionado (RF-08).
export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      usuario: null,
      municipioSelecionado: null,
      login: (usuario) => set({ usuario }),
      logout: () => set({ usuario: null, municipioSelecionado: null }),
      setMunicipioSelecionado: (municipio) => set({ municipioSelecionado: municipio }),
    }),
    { name: "incluia-app-store" },
  ),
);
