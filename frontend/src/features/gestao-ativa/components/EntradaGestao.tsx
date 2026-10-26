"use client";

// Entrada sem senha: e-mail → código de uso único → área do papel (decisão de 2026-10-23, AD-02).
// Conta sem acesso ativo (pendente, rejeitada, suspensa, revogada) recebe a explicação, nunca o token.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { entrar, getEu, pedirCodigo } from "../api";
import { destinoDoPapel, useGestaoStore } from "../store";
import type { SituacaoAcesso } from "../types";
import { LinkCaixaTeste } from "./CaixaTeste";
import { Aviso, Botao, Campo, Erro, Selo } from "./ui";

const TITULOS: Record<Exclude<SituacaoAcesso, "ativo">, string> = {
  aguardando_aprovacao: "Vínculo em validação",
  rejeitado: "Vínculo não confirmado",
  suspenso: "Acesso suspenso",
  revogado: "Acesso revogado",
};

export function EntradaGestao() {
  const router = useRouter();
  const guardarToken = useGestaoStore((s) => s.entrar);
  const definirEu = useGestaoStore((s) => s.definirEu);
  const [etapa, setEtapa] = useState<"email" | "codigo">("email");
  const [email, setEmail] = useState("");
  const [codigo, setCodigo] = useState("");
  const [situacao, setSituacao] = useState<{ tipo: Exclude<SituacaoAcesso, "ativo">; mensagem: string } | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviarEmail(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await pedirCodigo(email);
      setEtapa("codigo");
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function enviarCodigo(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const resposta = await entrar(email, codigo);
      if (resposta.situacao === "ativo" && resposta.token) {
        guardarToken(resposta.token);
        const eu = await getEu();
        definirEu(eu);
        router.push(destinoDoPapel(eu.papel));
        return;
      }
      setSituacao({ tipo: resposta.situacao as Exclude<SituacaoAcesso, "ativo">, mensagem: resposta.mensagem });
    } catch (falha) {
      setErro((falha as Error).message);
    }
    setEnviando(false);
  }

  return (
    <div className="grid min-h-screen bg-cream md:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="hidden flex-col justify-center bg-gov-blue-dark px-12 text-white md:flex">
        <span className="w-fit rounded-full bg-white/10 px-3 py-1 text-[11px] font-extrabold tracking-wider">ÁREA RESTRITA</span>
        <h1 className="mt-4 text-4xl font-extrabold">Gestão Ativa</h1>
        <ul className="mt-6 space-y-3 text-[15px] text-white/80">
          <li>Acesso vinculado à escola ou à rede municipal</li>
          <li>Declarações e planos com histórico de versões</li>
          <li>Assistência por IA com revisão humana</li>
        </ul>
      </aside>

      <main className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <Link href="/participar" className="text-xs font-bold text-gov-blue hover:underline">
            ← Participar
          </Link>

          {situacao ? (
            <div className="mt-4">
              <Selo tom={situacao.tipo === "aguardando_aprovacao" ? "ambar" : "vermelho"}>{TITULOS[situacao.tipo]}</Selo>
              <h2 className="mt-2 text-xl font-extrabold text-gov-blue-dark">A Gestão Ativa ainda não está liberada</h2>
              <div className="mt-3">
                <Aviso tom="atencao">{situacao.mensagem}</Aviso>
              </div>
              <Botao className="mt-4" variante="contorno" onClick={() => { setSituacao(null); setEtapa("email"); setCodigo(""); }}>
                Voltar
              </Botao>
            </div>
          ) : etapa === "email" ? (
            <form onSubmit={enviarEmail} className="mt-4">
              <h2 className="text-xl font-extrabold text-gov-blue-dark">Entrar na Gestão Ativa</h2>
              <p className="mb-5 mt-1 text-sm text-gray-500">Enviaremos um código de 6 dígitos para o seu e-mail. Não há senha.</p>
              <Campo id="email-entrada" rotulo="E-mail institucional" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <Erro mensagem={erro} />
              <Botao type="submit" className="w-full" disabled={enviando}>
                {enviando ? "Enviando…" : "Enviar código"}
              </Botao>
              <p className="mt-4 text-[13px] text-gray-500">
                Primeiro acesso de diretor?{" "}
                <Link href="/participar" className="font-bold text-gov-blue hover:underline">
                  Solicitar acesso
                </Link>
                . Secretarias municipais são habilitadas por convite.
              </p>
            </form>
          ) : (
            <form onSubmit={enviarCodigo} className="mt-4">
              <h2 className="text-xl font-extrabold text-gov-blue-dark">Digite o código</h2>
              <p className="mb-5 mt-1 text-sm text-gray-500">
                Se houver uma conta para <strong>{email}</strong>, o código chegou por e-mail e vale por 10 minutos.
              </p>
              <Campo
                id="codigo-entrada"
                rotulo="Código"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                placeholder="6 dígitos"
                value={codigo}
                onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ""))}
                required
              />
              <Erro mensagem={erro} />
              <Botao type="submit" className="w-full" disabled={enviando || codigo.length !== 6}>
                {enviando ? "Entrando…" : "Entrar"}
              </Botao>
              <Botao type="button" variante="discreto" className="mt-2 w-full" onClick={() => { setEtapa("email"); setErro(null); }}>
                Usar outro e-mail
              </Botao>
              <LinkCaixaTeste />
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
