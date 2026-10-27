import { redirect } from "next/navigation";

// O login da Fase 1 (autocadastro para o Diagnóstico IA) foi desativado em 2026-10-27: a área
// pública não pede login e a única entrada é a da Gestão Ativa (impacto-fase-1.md). Links antigos
// para /login caem aqui.
export default function LoginPage() {
  redirect("/gestao/entrar");
}
