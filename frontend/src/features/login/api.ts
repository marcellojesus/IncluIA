import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { LoginRequest, LoginResponse, RegistroRequest } from "./types";

export async function login(request: LoginRequest): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    throw new Error("E-mail ou senha inválidos");
  }
  return res.json();
}

export async function registrar(request: RegistroRequest): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/registrar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (res.status === 409) {
    throw new Error("Este e-mail já está cadastrado — tente entrar em vez de criar uma conta.");
  }
  if (!res.ok) {
    throw new Error("Não foi possível criar a conta agora. Tente novamente.");
  }
  return res.json();
}
