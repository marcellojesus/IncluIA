import { API_BASE_URL } from "@/shared/lib/apiConfig";
import type { LoginRequest, LoginResponse } from "./types";

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
