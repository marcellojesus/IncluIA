"use client";

// Tela de login/cadastro contextual do Diagnóstico IA — ver RN-06 de docs/business-rules/login.md
// e RF-09/RF-11/RF-12 de docs/requirements/login.md. Só aparece quando o `redirect` de /login
// aponta para uma rota de Diagnóstico IA; caso contrário, LoginPage usa o layout institucional.
import { useRouter } from "next/navigation";
import type { FormEvent, ReactNode } from "react";
import { useState } from "react";

import { BarraAcessibilidade } from "@/shared/components/BarraAcessibilidade";
import { useAppStore } from "@/shared/store/useAppStore";
import { login, registrar } from "../api";
import type { PerfilPublico } from "../types";

const PERFIS: { value: PerfilPublico; label: string }[] = [
  { value: "familia", label: "Família / responsável" },
  { value: "imprensa", label: "Jornalista / imprensa" },
  { value: "sociedade_civil", label: "Sociedade civil / ONG" },
  { value: "secretario_educacao", label: "Secretário(a) de Educação" },
  { value: "pesquisador", label: "Pesquisador(a)" },
  { value: "poder_publico", label: "Poder público / gestor" },
];

const ESTILO_INPUT =
  "w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gov-blue-dark outline-none focus:border-gov-blue";

// Só redireciona de volta para caminhos internos do próprio app — nunca para uma URL absoluta
// vinda da querystring (evitaria um open redirect se alguém manipular o link).
function destinoSeguro(redirect: string | null): string {
  if (redirect && redirect.startsWith("/") && !redirect.startsWith("//")) return redirect;
  return "/";
}

function Campo({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-bold text-gray-600">{label}</span>
      {children}
    </label>
  );
}

export function AuthDiagnosticoIA({ redirect }: { redirect: string | null }) {
  const router = useRouter();
  const autenticar = useAppStore((s) => s.login);
  const nomeMunicipio = useAppStore((s) => s.municipioSelecionado?.nome);

  const [aba, setAba] = useState<"criar" | "entrar">("criar");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const [nome, setNome] = useState("");
  const [perfil, setPerfil] = useState<PerfilPublico>("familia");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");

  const [emailLogin, setEmailLogin] = useState("joao.silva@niteroi.rj.gov.br");
  const [senhaLogin, setSenhaLogin] = useState("demo1234");

  async function handleCriarConta(e: FormEvent) {
    e.preventDefault();
    setCarregando(true);
    setErro(null);
    try {
      const resposta = await registrar({ nome, email, senha, perfil });
      autenticar(resposta);
      router.push(destinoSeguro(redirect));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não foi possível criar a conta agora.");
      setCarregando(false);
    }
  }

  async function handleEntrar(e: FormEvent) {
    e.preventDefault();
    setCarregando(true);
    setErro(null);
    try {
      const resposta = await login({ email: emailLogin, senha: senhaLogin });
      autenticar(resposta);
      router.push(destinoSeguro(redirect));
    } catch {
      setErro("E-mail ou senha inválidos");
      setCarregando(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-cream">
      <BarraAcessibilidade />
      <div className="flex flex-1 items-center justify-center px-6 py-10">
        <div className="w-full max-w-md">
          <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gov-blue text-2xl">
            🤖
          </div>
          <h1 className="mb-2 text-2xl font-extrabold text-gov-blue-dark">Diagnóstico com IA</h1>
          <p className="max-w-[38ch] text-sm leading-relaxed text-gray-500">
            A IA lê os dados do Censo Escolar do INEP e gera uma análise por eixo da PNEEI
            {nomeMunicipio ? ` para ${nomeMunicipio}` : ""}. Para gerar, crie uma conta verificada
            e faça login.
          </p>
        </div>

        <div className="rounded-2xl bg-paper p-6 shadow-sm">
          <div className="mb-5 flex rounded-xl bg-[#eef1ec] p-1">
            <button
              type="button"
              onClick={() => setAba("criar")}
              className={`flex-1 rounded-lg py-2 text-sm font-bold transition-colors ${
                aba === "criar" ? "bg-gov-blue-dark text-white" : "text-gray-500"
              }`}
            >
              Criar conta
            </button>
            <button
              type="button"
              onClick={() => setAba("entrar")}
              className={`flex-1 rounded-lg py-2 text-sm font-bold transition-colors ${
                aba === "entrar" ? "bg-gov-blue-dark text-white" : "text-gray-500"
              }`}
            >
              Entrar
            </button>
          </div>

          {aba === "criar" ? (
            <form onSubmit={handleCriarConta} className="flex flex-col gap-3.5">
              <Campo label="Nome completo">
                <input
                  required
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Seu nome"
                  className={ESTILO_INPUT}
                />
              </Campo>
              <Campo label="Você é">
                <select
                  value={perfil}
                  onChange={(e) => setPerfil(e.target.value as PerfilPublico)}
                  className={ESTILO_INPUT}
                >
                  {PERFIS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo label="E-mail">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="voce@email.com"
                  className={ESTILO_INPUT}
                />
              </Campo>
              <Campo label="Senha">
                <input
                  type="password"
                  required
                  minLength={6}
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  placeholder="Crie uma senha"
                  className={ESTILO_INPUT}
                />
              </Campo>

              {erro && <div className="text-sm text-gov-red">{erro}</div>}

              <button
                type="submit"
                disabled={carregando}
                className="mt-1 rounded-xl bg-accent py-3 text-sm font-extrabold text-white hover:bg-accent-dark disabled:opacity-60"
              >
                {carregando ? "Criando conta…" : "Criar conta e gerar diagnóstico"}
              </button>

              <p className="text-center text-[11px] leading-relaxed text-gray-400">
                Conta gratuita, usada apenas para liberar a IA e evitar abuso. Os dados do Censo
                são públicos e abertos.
              </p>
            </form>
          ) : (
            <form onSubmit={handleEntrar} className="flex flex-col gap-3.5">
              <Campo label="E-mail">
                <input
                  type="email"
                  required
                  value={emailLogin}
                  onChange={(e) => setEmailLogin(e.target.value)}
                  className={ESTILO_INPUT}
                />
              </Campo>
              <Campo label="Senha">
                <input
                  type="password"
                  required
                  value={senhaLogin}
                  onChange={(e) => setSenhaLogin(e.target.value)}
                  className={ESTILO_INPUT}
                />
              </Campo>

              {erro && <div className="text-sm text-gov-red">{erro}</div>}

              <button
                type="submit"
                disabled={carregando}
                className="mt-1 rounded-xl bg-gov-blue py-3 text-sm font-extrabold text-white hover:bg-gov-blue-mid disabled:opacity-60"
              >
                {carregando ? "Entrando…" : "Entrar e gerar diagnóstico"}
              </button>
            </form>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}
