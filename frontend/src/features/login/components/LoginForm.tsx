"use client";

// Ver interface.md §2 "Coluna direita" e docs/requirements/login.md RF-01 a RF-05.
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { useAppStore } from "@/shared/store/useAppStore";
import { login } from "../api";

// Só redireciona de volta para caminhos internos do próprio app — nunca para uma URL absoluta
// vinda da querystring (evitaria um open redirect se alguém manipular o link).
function destinoSeguro(redirect: string | null): string {
  if (redirect && redirect.startsWith("/") && !redirect.startsWith("//")) return redirect;
  return "/";
}

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const autenticar = useAppStore((s) => s.login);

  // Pré-preenchido com o usuário de demonstração — não há autosserviço de cadastro no MVP
  // (ver docs/business-rules/login.md RN-01).
  const [email, setEmail] = useState("joao.silva@niteroi.rj.gov.br");
  const [senha, setSenha] = useState("demo1234");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCarregando(true);
    setErro(null);
    try {
      const resposta = await login({ email, senha });
      autenticar(resposta);
      router.push(destinoSeguro(searchParams.get("redirect")));
    } catch {
      setErro("E-mail ou senha inválidos");
      setCarregando(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <div className="mb-1 text-xl font-bold text-gov-blue-dark">Entrar</div>
      <div className="mb-6 text-sm text-gray-400">
        Acesso necessário para gerar o Diagnóstico com IA de um município.
      </div>

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="mb-1 block text-xs font-semibold text-gray-600">
            E-mail institucional
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gov-blue"
          />
        </div>
        <div className="mb-3">
          <label className="mb-1 block text-xs font-semibold text-gray-600">Senha</label>
          <input
            type="password"
            required
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gov-blue"
          />
        </div>

        {erro && <div className="mb-3 text-sm text-gov-red">{erro}</div>}

        <button
          type="submit"
          disabled={carregando}
          className="w-full rounded bg-gov-blue py-2.5 text-sm font-bold text-white disabled:opacity-60"
        >
          {carregando ? "Entrando…" : "Entrar"}
        </button>
      </form>

      <div className="mt-5 rounded border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs text-gray-500">
        Esta tela é só para contas de gestor (sem autocadastro) — use o acesso de demonstração já
        preenchido acima. Famílias, jornalistas, ONGs e pesquisadores podem criar a própria conta
        ao abrir o Diagnóstico IA de um município.
      </div>
    </div>
  );
}
