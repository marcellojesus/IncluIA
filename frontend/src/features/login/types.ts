// Ver docs/requirements/login.md "Dados de entrada/saída".

// Provisionados manualmente (seed) — sem cadastro público, ver RN-01/RN-02 de
// docs/business-rules/login.md.
export type PerfilGestor = "municipal" | "estadual";

// Autocadastro público, oferecido na tela contextual do Diagnóstico IA (RN-01 revisada).
export type PerfilPublico =
  | "familia"
  | "imprensa"
  | "sociedade_civil"
  | "secretario_educacao"
  | "pesquisador"
  | "poder_publico";

export type PerfilUsuario = PerfilGestor | PerfilPublico;

export type LoginRequest = {
  email: string;
  senha: string;
};

export type RegistroRequest = {
  nome: string;
  email: string;
  senha: string;
  perfil: PerfilPublico;
};

export type LoginResponse = {
  usuarioId: string;
  nome: string;
  perfil: PerfilUsuario;
  municipioId?: number;
  uf?: string;
  token: string;
};
