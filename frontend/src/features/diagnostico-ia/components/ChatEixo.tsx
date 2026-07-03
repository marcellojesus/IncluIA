"use client";

// RN-09/RN-10 de docs/business-rules/diagnostico-ia.md — chat por eixo (Q&A + ajuste de
// recomendação) e botão de reprocessamento completo do diagnóstico considerando a conversa.
import { useState } from "react";

import { enviarMensagemChat, ErroAutenticacao, getChatHistorico, reprocessarDiagnostico } from "../api";
import type { DiagnosticoEixo, Eixo, MensagemChat, RecomendacaoIA } from "../types";

function mensagemErro(e: unknown, fallback: string): string {
  return e instanceof ErroAutenticacao
    ? "Sua sessão expirou. Recarregue a página para fazer login novamente."
    : fallback;
}

export function ChatEixo({
  codigoIbge,
  eixo,
  onRecomendacoesAtualizadas,
  onDiagnosticoReprocessado,
}: {
  codigoIbge: number;
  eixo: Eixo;
  onRecomendacoesAtualizadas: (recomendacoes: RecomendacaoIA[]) => void;
  onDiagnosticoReprocessado: (diagnostico: DiagnosticoEixo) => void;
}) {
  const [aberto, setAberto] = useState(false);
  const [mensagens, setMensagens] = useState<MensagemChat[] | null>(null);
  const [rascunho, setRascunho] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [reprocessando, setReprocessando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function alternar() {
    setAberto((atual) => !atual);
    if (mensagens === null) {
      getChatHistorico(codigoIbge, eixo)
        .then(setMensagens)
        .catch(() => setMensagens([]));
    }
  }

  function enviar() {
    const texto = rascunho.trim();
    if (!texto || enviando) return;

    setErro(null);
    setEnviando(true);
    setRascunho("");
    setMensagens((atual) => [
      ...(atual ?? []),
      { papel: "user", conteudo: texto, criadoEm: new Date().toISOString() },
    ]);

    enviarMensagemChat(codigoIbge, eixo, texto)
      .then((resposta) => {
        setMensagens((atual) => [
          ...(atual ?? []),
          { papel: "assistant", conteudo: resposta.resposta, criadoEm: new Date().toISOString() },
        ]);
        if (resposta.recomendacoesAtualizadas) {
          onRecomendacoesAtualizadas(resposta.recomendacoesAtualizadas);
        }
      })
      .catch((e) => setErro(mensagemErro(e, "Não foi possível enviar sua mensagem agora. Tente novamente.")))
      .finally(() => setEnviando(false));
  }

  function reprocessar() {
    if (reprocessando) return;
    setErro(null);
    setReprocessando(true);
    reprocessarDiagnostico(codigoIbge, eixo)
      .then((diagnostico) => {
        onDiagnosticoReprocessado(diagnostico);
        return getChatHistorico(codigoIbge, eixo).then(setMensagens);
      })
      .catch((e) => setErro(mensagemErro(e, "Não foi possível reprocessar o diagnóstico agora. Tente novamente.")))
      .finally(() => setReprocessando(false));
  }

  const temConversa = (mensagens?.length ?? 0) > 0;

  return (
    <div className="mt-1">
      <button onClick={alternar} className="text-[11px] font-semibold text-gov-blue hover:underline">
        {aberto ? "▲ Fechar chat" : "💬 Conversar sobre este eixo"}
      </button>

      {aberto && (
        <div className="mt-2 rounded border border-gov-blue-lt bg-white">
          <div className="max-h-72 overflow-y-auto p-3">
            {mensagens === null && <p className="text-xs text-gray-400">Carregando conversa…</p>}
            {mensagens?.length === 0 && (
              <p className="text-xs text-gray-400">
                Tire dúvidas sobre este diagnóstico ou peça um ajuste na recomendação.
              </p>
            )}
            {mensagens?.map((m, i) => (
              <div key={i} className={`mb-2 flex ${m.papel === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded px-2.5 py-1.5 text-xs ${
                    m.papel === "user" ? "bg-gov-blue text-white" : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {m.conteudo}
                </div>
              </div>
            ))}
            {enviando && <p className="text-xs text-gray-400">⏳ Pensando…</p>}
          </div>

          {erro && <p className="border-t border-gray-100 px-3 py-1.5 text-xs text-gov-red">{erro}</p>}

          {temConversa && (
            <div className="border-t border-gray-100 p-2">
              <button
                onClick={reprocessar}
                disabled={reprocessando || enviando}
                title="Gera uma nova versão completa do diagnóstico deste eixo, considerando tudo que foi conversado"
                className="w-full rounded border border-gov-green bg-green-50 py-1.5 text-xs font-bold text-gov-green disabled:opacity-60"
              >
                {reprocessando ? "⏳ Reprocessando…" : "🔄 Reprocessar diagnóstico com esta conversa"}
              </button>
            </div>
          )}

          <div className="flex gap-2 border-t border-gray-100 p-2">
            <input
              value={rascunho}
              onChange={(e) => setRascunho(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && enviar()}
              disabled={enviando}
              placeholder="Pergunte ou peça um ajuste…"
              className="flex-1 rounded border border-gray-300 px-2 py-1 text-xs outline-none focus:border-gov-blue disabled:opacity-60"
            />
            <button
              onClick={enviar}
              disabled={enviando || !rascunho.trim()}
              className="rounded bg-gov-blue px-3 py-1 text-xs font-bold text-white disabled:opacity-60"
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
