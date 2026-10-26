import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { Escola } from "./types";

export async function getEscolasPorMunicipio(codigoIbge: number): Promise<Escola[]> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/escolas`);
  return res.json();
}

export async function getEscolaDetalhe(coEntidade: number): Promise<Escola> {
  const res = await fetch(`${API_BASE_URL}/escolas/${coEntidade}`);
  return res.json();
}

// Declaração de Obstáculos publicada pela escola (Gestão Ativa, DO-RF-08). null quando não há versão publicada.
export type DeclaracaoPublica = {
  coEntidade: number;
  escola: string;
  versao: number;
  emitidaEm: string;
  publicadaEm: string;
  censoVersao: string;
  itens: { codigo: string; eixo: string; barreira: string; dadoCenso: string; posicao: "obstaculo" | "divergencia" | "sem_relato"; textoPublico: string }[];
  // Plano de Ação aceito pela secretaria e publicado pela escola; só vem junto com a Declaração publicada.
  plano: PlanoPublico | null;
};

export type PlanoPublico = {
  versao: number;
  declaracaoVersao: number;
  aceitoEm: string | null;
  publicadoEm: string;
  itens: {
    codigo: string;
    barreira: string;
    horizonte: "LOA" | "PPA";
    acao: string | null;
    relacao: string | null;
    responsavel: string | null;
    prazo: string | null;
    custoEstimado: string | null;
    fontes: string[];
  }[];
};

export async function getDeclaracaoPublica(coEntidade: number): Promise<DeclaracaoPublica | null> {
  const res = await fetch(`${API_BASE_URL}/escolas/${coEntidade}/declaracao-publica`);
  if (!res.ok) return null;
  return res.json();
}

// Escolas do município com Declaração e Plano de Ação publicados (Gestão Ativa). Só versões, sem texto.
export type PublicacaoGestao = { coEntidade: number; declaracaoVersao: number; planoVersao: number | null };

export async function getPublicacoesGestao(codigoIbge: number): Promise<PublicacaoGestao[]> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/publicacoes-gestao`);
  if (!res.ok) return [];
  return (await res.json()).escolas;
}
