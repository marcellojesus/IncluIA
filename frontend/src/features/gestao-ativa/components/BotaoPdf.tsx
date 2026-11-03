"use client";

// Baixa o PDF de uma versão congelada (RF-31). O botão só aparece onde a versão já existe; o
// servidor confere de novo o acesso e os dados pessoais, e a mensagem de recusa vem dele. Antes do
// primeiro download da sessão, um aviso lembra que o arquivo sai da plataforma (revisão do AgLGPD, M2).
import { useState } from "react";

import { baixarPdf } from "../api";
import { Botao } from "./ui";

const CHAVE_CIENCIA = "gestao-pdf-ciente";

function jaCiente(): boolean {
  try {
    return sessionStorage.getItem(CHAVE_CIENCIA) === "1";
  } catch {
    return false;
  }
}

function registrarCiencia(): void {
  try {
    sessionStorage.setItem(CHAVE_CIENCIA, "1");
  } catch {
    // Sem armazenamento, o aviso volta no próximo download.
  }
}

export function BotaoPdf({ caminho, rotulo = "Baixar PDF", comoLink = false }: { caminho: string; rotulo?: string; comoLink?: boolean }) {
  const [baixando, setBaixando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function baixar() {
    setErro(null);
    setConfirmando(false);
    setBaixando(true);
    try {
      await baixarPdf(caminho);
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setBaixando(false);
    }
  }

  function pedir() {
    if (jaCiente()) void baixar();
    else setConfirmando(true);
  }

  const texto = baixando ? "Gerando PDF…" : rotulo;
  return (
    <>
      {comoLink ? (
        <button
          type="button"
          onClick={pedir}
          disabled={baixando}
          className="ml-1 font-bold text-gov-blue underline-offset-2 hover:underline disabled:opacity-50"
        >
          {texto}
        </button>
      ) : (
        <Botao type="button" variante="contorno" onClick={pedir} disabled={baixando}>
          {texto}
        </Botao>
      )}
      {confirmando && (
        <span role="alertdialog" aria-label="Aviso sobre o PDF" className="mt-1 block rounded-lg bg-[#fff4df] px-3 py-2 text-left text-[12px] font-normal text-[#7a4b0f]">
          O arquivo sai da plataforma e não acompanha correções nem retiradas posteriores. Guarde em local restrito e não encaminhe para
          fora da escola ou da secretaria.{" "}
          <button
            type="button"
            onClick={() => {
              registrarCiencia();
              void baixar();
            }}
            className="font-bold text-gov-blue underline"
          >
            Entendi, baixar
          </button>{" "}
          <button type="button" onClick={() => setConfirmando(false)} className="text-gray-600 underline">
            Cancelar
          </button>
        </span>
      )}
      {erro && (
        <span role="alert" className="block text-[12px] text-[#b23838]">
          {erro}
        </span>
      )}
    </>
  );
}
