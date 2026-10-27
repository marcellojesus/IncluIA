import { create } from "zustand";
import { persist } from "zustand/middleware";

export type MunicipioSelecionado = {
  codigoIbge: number;
  nome: string;
  uf: string;
  score: number;
};

type AppState = {
  municipioSelecionado: MunicipioSelecionado | null;
  setMunicipioSelecionado: (municipio: MunicipioSelecionado | null) => void;
};

// Estado global da área pública (arquitetura.md): o município selecionado, em localStorage.
// A área pública não tem login desde 2026-10-27; a sessão da Gestão Ativa fica em
// features/gestao-ativa/store.ts. A versão 1 apaga do navegador o `usuario` (nome, perfil e token)
// gravado pelo login antigo: o `migrate` regrava a chave já na primeira carga (revisão do AgLGPD).
type Persistido = { municipioSelecionado: MunicipioSelecionado | null };

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      municipioSelecionado: null,
      setMunicipioSelecionado: (municipio) => set({ municipioSelecionado: municipio }),
    }),
    {
      name: "incluia-app-store",
      version: 1,
      partialize: (estado): Persistido => ({ municipioSelecionado: estado.municipioSelecionado }),
      migrate: (antigo) => ({ municipioSelecionado: (antigo as Partial<Persistido> | null)?.municipioSelecionado ?? null }),
      merge: (persistido, atual) => ({ ...atual, municipioSelecionado: (persistido as Persistido | null)?.municipioSelecionado ?? null }),
    },
  ),
);
