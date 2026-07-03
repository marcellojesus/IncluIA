// Ver docs/requirements/login.md "Dados de entrada/saída".

export type PerfilUsuario = "municipal" | "estadual";

export type LoginRequest = {
  email: string;
  senha: string;
};

export type LoginResponse = {
  usuarioId: string;
  nome: string;
  perfil: PerfilUsuario;
  municipioId?: number;
  uf: string;
  token: string;
};
