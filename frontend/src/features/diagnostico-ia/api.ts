// RN-06 de docs/business-rules/login.md: única feature que exige autenticação — todas as
// chamadas abaixo enviam o token do usuário logado (se houver) via Authorization: Bearer.
import { API_BASE_URL } from "@/shared/lib/apiConfig";
import { useAppStore } from "@/shared/store/useAppStore";
import type { DiagnosticoEixo, Eixo, MensagemChat, RespostaChatIA } from "./types";

// Lançado quando o backend responde 401 (sem token, token expirado ou inválido) — os componentes
// tratam isso diferente de uma falha genérica (mensagem convidando a fazer login, não "tente
// novamente").
export class ErroAutenticacao extends Error {
  constructor() {
    super("Sessão expirada ou inexistente — faça login para acessar o Diagnóstico IA.");
    this.name = "ErroAutenticacao";
  }
}

function headersAutenticados(extra?: Record<string, string>): Record<string, string> {
  const token = useAppStore.getState().usuario?.token;
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function tratarResposta<T>(res: Response, mensagemErro: string): Promise<T> {
  if (res.status === 401) throw new ErroAutenticacao();
  // 422: o Guardião LGPD bloqueou a mensagem (dado de risco alto); o backend explica o que reescrever.
  if (res.status === 422) {
    const corpo = await res.json().catch(() => null);
    throw new Error(typeof corpo?.detail === "string" ? corpo.detail : mensagemErro);
  }
  if (!res.ok) throw new Error(mensagemErro);
  return res.json();
}

export async function getDiagnostico(
  codigoIbge: number,
  forcar = false,
): Promise<DiagnosticoEixo[]> {
  const res = await fetch(
    `${API_BASE_URL}/municipios/${codigoIbge}/diagnostico?forcar=${forcar}`,
    { method: "POST", headers: headersAutenticados() },
  );
  return tratarResposta(res, "Falha ao gerar o diagnóstico de IA");
}

export async function getChatHistorico(codigoIbge: number, eixo: Eixo): Promise<MensagemChat[]> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/diagnostico/${eixo}/chat`, {
    headers: headersAutenticados(),
  });
  return tratarResposta(res, "Falha ao carregar o histórico do chat");
}

export async function enviarMensagemChat(
  codigoIbge: number,
  eixo: Eixo,
  mensagem: string,
): Promise<RespostaChatIA> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/diagnostico/${eixo}/chat`, {
    method: "POST",
    headers: headersAutenticados({ "Content-Type": "application/json" }),
    body: JSON.stringify({ mensagem }),
  });
  return tratarResposta(res, "Não foi possível enviar sua mensagem agora. Tente novamente.");
}

export async function reprocessarDiagnostico(codigoIbge: number, eixo: Eixo): Promise<DiagnosticoEixo> {
  const res = await fetch(`${API_BASE_URL}/municipios/${codigoIbge}/diagnostico/${eixo}/reprocessar`, {
    method: "POST",
    headers: headersAutenticados(),
  });
  return tratarResposta(res, "Não foi possível reprocessar o diagnóstico agora. Tente novamente.");
}
