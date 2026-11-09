// Rótulos e tons compartilhados pelas telas do diretor (protótipo v2, badges de posição).
import { useGestaoStore } from "./store";
import type { EstadoVersaoPlano, Posicao } from "./types";

// O DF não tem rede municipal: a Gestão Ativa atende lá a rede distrital, que o Censo chama de
// "Estadual" (backend/app/features/acesso/censo.py, decisão de 2026-11-09).
export type RotulosRede = { rede: string; escolas: string; secretaria: string; secretariaMinuscula: string };

export function rotulosDaRede(uf: string | null | undefined): RotulosRede {
  return uf === "DF"
    ? { rede: "rede distrital", escolas: "escolas distritais", secretaria: "Secretaria de Educação do DF", secretariaMinuscula: "secretaria de estado de educação do DF" }
    : { rede: "rede municipal", escolas: "escolas municipais", secretaria: "Secretaria municipal", secretariaMinuscula: "secretaria municipal de educação" };
}

// A área restrita só mostra as telas depois de carregar /gestao/eu (AreaRestrita), então o escopo já está na store.
export const rotulosAtuais = (): RotulosRede => rotulosDaRede(useGestaoStore.getState().eu?.escopo.uf);

export const POSICOES: Record<Posicao, { texto: string; tom: "verde" | "azul" | "neutro" | "ambar" }> = {
  sem_posicao: { texto: "Sem posição", tom: "ambar" },
  rascunho: { texto: "Rascunho", tom: "ambar" },
  obstaculo: { texto: "Obstáculo relatado", tom: "verde" },
  divergencia: { texto: "Divergência com o Censo", tom: "azul" },
  sem_relato: { texto: "Sem relato nesta versão", tom: "neutro" },
};

export const NOMES_EIXOS: Record<string, string> = {
  I: "AEE",
  II: "Acessibilidade",
  III: "Profissionais",
  IV: "Classe comum",
};

export const POSICOES_FINAIS: Posicao[] = ["obstaculo", "divergencia", "sem_relato"];

export const dataCurta = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("pt-BR") : "—");

// Estados de uma versão enviada do Plano de Ação (decisão da secretaria, RN-SFR-03).
export const ESTADOS_VERSAO_PLANO: Record<EstadoVersaoPlano, { texto: string; tom: "ambar" | "verde" | "vermelho" | "azul" }> = {
  aguardando_analise: { texto: "Aguardando análise", tom: "ambar" },
  aceito: { texto: "Aceito como base", tom: "verde" },
  ajustes_solicitados: { texto: "Ajustes solicitados", tom: "azul" },
  reprovado: { texto: "Reprovado", tom: "vermelho" },
};
