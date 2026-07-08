"use client";

// Barra verde de acessibilidade, presente em todas as páginas (montada dentro de cada layout que
// controla a altura total da tela — (app)/layout.tsx, LoginPage.tsx e app/metodologia/page.tsx —
// em vez do layout raiz, para não quebrar o cálculo de h-screen/rolagem interna delas).
import { useEffect, useState } from "react";

type EscalaFonte = "sm" | "md" | "lg";

const CHAVE_CONTRASTE = "esb-alto-contraste";
const CHAVE_FONTE = "esb-escala-fonte";

export function BarraAcessibilidade() {
  const [altoContraste, setAltoContraste] = useState(false);
  const [escalaFonte, setEscalaFonte] = useState<EscalaFonte>("md");

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- sincroniza com a preferência salva no localStorage (fonte externa ao React), só existe no cliente
    if (localStorage.getItem(CHAVE_CONTRASTE) === "1") setAltoContraste(true);
    const fonteSalva = localStorage.getItem(CHAVE_FONTE);
    if (fonteSalva === "sm" || fonteSalva === "lg") setEscalaFonte(fonteSalva);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("alto-contraste", altoContraste);
    localStorage.setItem(CHAVE_CONTRASTE, altoContraste ? "1" : "0");
  }, [altoContraste]);

  useEffect(() => {
    document.documentElement.classList.remove("fonte-sm", "fonte-lg");
    if (escalaFonte !== "md") document.documentElement.classList.add(`fonte-${escalaFonte}`);
    localStorage.setItem(CHAVE_FONTE, escalaFonte);
  }, [escalaFonte]);

  return (
    <div className="flex flex-shrink-0 flex-wrap items-center justify-between gap-2 bg-gov-blue-dark px-4 py-1.5 text-[11px] text-white/80">
      <span>Iniciativa da sociedade civil · Dados abertos INEP/MEC · Censo Escolar 2025</span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setAltoContraste((v) => !v)}
          aria-pressed={altoContraste}
          className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-bold hover:bg-white/10 ${
            altoContraste ? "border-white bg-white/15 text-white" : "border-white/25 text-white/90"
          }`}
        >
          ◐ Alto contraste
        </button>
        <div className="flex items-center overflow-hidden rounded-full border border-white/25">
          <button
            type="button"
            onClick={() => setEscalaFonte("sm")}
            aria-label="Diminuir fonte"
            className={`px-2 py-1 font-bold hover:bg-white/10 ${
              escalaFonte === "sm" ? "bg-white/15 text-white" : "text-white/90"
            }`}
          >
            A-
          </button>
          <button
            type="button"
            onClick={() => setEscalaFonte("md")}
            aria-label="Fonte padrão"
            className={`border-x border-white/25 px-2 py-1 font-bold hover:bg-white/10 ${
              escalaFonte === "md" ? "bg-white/15 text-white" : "text-white/90"
            }`}
          >
            A
          </button>
          <button
            type="button"
            onClick={() => setEscalaFonte("lg")}
            aria-label="Aumentar fonte"
            className={`px-2 py-1 font-bold hover:bg-white/10 ${
              escalaFonte === "lg" ? "bg-white/15 text-white" : "text-white/90"
            }`}
          >
            A+
          </button>
        </div>
      </div>
    </div>
  );
}
