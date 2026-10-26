"use client";

// Caixa de e-mails de teste: mostra os códigos enquanto não há provedor de e-mail (AD-02,
// pendência 3). O backend só a serve com AMBIENTE=dev e para acesso da própria máquina.
import Link from "next/link";
import { useEffect, useState } from "react";

import { Logo } from "@/shared/components/Logo";

import { type EmailTeste, getEmailsTeste } from "../api";
import { Aviso, Cartao } from "./ui";

const VALIDADE_MINUTOS = 10;

function minutosDesde(iso: string, agora: number): number {
  return Math.floor((agora - new Date(iso).getTime()) / 60_000);
}

export function CaixaTeste() {
  const [emails, setEmails] = useState<EmailTeste[] | null>(null);
  const [indisponivel, setIndisponivel] = useState(false);
  const [agora, setAgora] = useState(() => Date.now());
  const [copiado, setCopiado] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    const atualizar = () =>
      getEmailsTeste()
        .then((dados) => {
          if (!ativo) return;
          setEmails(dados);
          setAgora(Date.now());
        })
        .catch(() => ativo && setIndisponivel(true));
    atualizar();
    const intervalo = setInterval(atualizar, 4000);
    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, []);

  async function copiar(codigo: string) {
    try {
      await navigator.clipboard.writeText(codigo);
      setCopiado(codigo);
    } catch {
      setCopiado(null);
    }
  }

  return (
    <div className="min-h-screen bg-cream">
      <header className="flex items-center gap-3 border-b border-black/5 bg-paper px-6 py-3">
        <Logo />
        <span className="text-lg font-extrabold text-gov-blue-dark">Caixa de e-mails de teste</span>
        <Link href="/gestao/entrar" className="ml-auto text-sm font-bold text-gov-blue hover:underline">
          Ir para a entrada
        </Link>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-6">
        <Aviso tom="atencao">
          Só existe no ambiente de desenvolvimento: mostra os códigos que seriam enviados por e-mail enquanto não há provedor
          configurado. Atualiza sozinha a cada 4 segundos e esvazia quando o backend reinicia.
        </Aviso>

        <div className="mt-5 space-y-3" aria-live="polite">
          {indisponivel ? (
            <Cartao className="p-5 text-sm text-gray-600">
              A caixa de teste não está disponível. Ela só funciona com o backend local em <code>AMBIENTE=dev</code>.
            </Cartao>
          ) : emails === null ? (
            <p role="status" className="text-sm text-gray-500">Carregando…</p>
          ) : emails.length === 0 ? (
            <Cartao className="p-5 text-sm text-gray-600">
              Nenhuma mensagem ainda. Peça um código na tela de entrada ou em “Solicitar acesso” e ele aparece aqui.
            </Cartao>
          ) : (
            emails.map((email, indice) => {
              const minutos = minutosDesde(email.enviadaEm, agora);
              const expirado = minutos >= VALIDADE_MINUTOS;
              return (
                <Cartao key={`${email.enviadaEm}-${indice}`} className={`p-4 ${expirado ? "opacity-60" : ""}`}>
                  <div className="flex flex-wrap items-baseline justify-between gap-2 text-[12px] text-gray-500">
                    <span>
                      Para <strong className="text-ink">{email.para}</strong>
                    </span>
                    <span>{minutos <= 0 ? "agora" : `há ${minutos} min`}{expirado ? " · expirado" : ""}</span>
                  </div>
                  <div className="mt-1 text-sm font-bold text-ink">{email.assunto}</div>
                  <p className="mt-1 text-[13px] text-gray-600">{email.texto}</p>
                  <div className="mt-3 flex items-center gap-3">
                    <span className="rounded-lg bg-gov-blue-lt px-4 py-2 font-mono text-2xl font-extrabold tracking-[.3em] text-gov-blue-dark">
                      {email.codigo}
                    </span>
                    {!expirado && (
                      <button onClick={() => copiar(email.codigo)} className="rounded-lg px-3 py-1.5 text-sm font-bold text-gov-blue hover:bg-gov-blue-lt">
                        {copiado === email.codigo ? "Copiado" : "Copiar"}
                      </button>
                    )}
                  </div>
                </Cartao>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}

/** Atalho para a caixa de teste; só aparece quando o backend a oferece (AMBIENTE=dev). */
export function LinkCaixaTeste() {
  const [disponivel, setDisponivel] = useState(false);

  useEffect(() => {
    let ativo = true;
    getEmailsTeste()
      .then(() => ativo && setDisponivel(true))
      .catch(() => undefined);
    return () => {
      ativo = false;
    };
  }, []);

  if (!disponivel) return null;
  return (
    <a href="/gestao/dev/emails" target="_blank" rel="noopener" className="mt-3 block text-[13px] font-bold text-accent hover:underline">
      Ambiente de teste: abrir a caixa de e-mails com o código ↗
    </a>
  );
}
