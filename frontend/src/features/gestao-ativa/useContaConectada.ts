"use client";

// Conta da Gestão Ativa já conectada nesta aba, para as telas públicas (cabeçalho, /participar,
// /gestao/entrar) mandarem quem já entrou direto ao seu painel, em vez de pedir o login de novo.
// Só o token fica guardado (sessionStorage); os dados da conta vêm de /gestao/eu, uma vez por carga.
import { useEffect, useSyncExternalStore } from "react";

import { SemAcesso, getEu } from "./api";
import { useGestaoStore } from "./store";
import type { Eu } from "./types";

export function useContaConectada(): Eu | null {
  const token = useGestaoStore((s) => s.token);
  const eu = useGestaoStore((s) => s.eu);
  const definirEu = useGestaoStore((s) => s.definirEu);
  const sair = useGestaoStore((s) => s.sair);
  // A sessão salva carrega depois da primeira renderização; antes disso, ninguém está conectado
  // (evita divergência entre o HTML do servidor e o do navegador).
  const hidratado = useSyncExternalStore(
    (avisar) => useGestaoStore.persist.onFinishHydration(avisar),
    () => useGestaoStore.persist.hasHydrated(),
    () => false,
  );

  useEffect(() => {
    if (!hidratado || !token || eu) return;
    let ativo = true;
    getEu()
      .then((dados) => ativo && definirEu(dados))
      .catch((falha) => {
        // Sessão vencida ou acesso encerrado: limpa o token para a tela pública voltar ao normal.
        if (ativo && falha instanceof SemAcesso) sair();
      });
    return () => {
      ativo = false;
    };
  }, [hidratado, token, eu, definirEu, sair]);

  return hidratado && token ? eu : null;
}
