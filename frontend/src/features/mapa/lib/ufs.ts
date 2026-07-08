// 27 UFs (sigla, nome, código IBGE de 2 dígitos, região) — usado no filtro geográfico
// (Região → UF → Município) e nas chamadas à API do IBGE.

export type Regiao = "Norte" | "Nordeste" | "Centro-Oeste" | "Sudeste" | "Sul";

export type Uf = {
  sigla: string;
  nome: string;
  codigoIbge: number;
  regiao: Regiao;
};

export const REGIOES: Regiao[] = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"];

export const UFS: Uf[] = [
  { sigla: "AC", nome: "Acre", codigoIbge: 12, regiao: "Norte" },
  { sigla: "AL", nome: "Alagoas", codigoIbge: 27, regiao: "Nordeste" },
  { sigla: "AP", nome: "Amapá", codigoIbge: 16, regiao: "Norte" },
  { sigla: "AM", nome: "Amazonas", codigoIbge: 13, regiao: "Norte" },
  { sigla: "BA", nome: "Bahia", codigoIbge: 29, regiao: "Nordeste" },
  { sigla: "CE", nome: "Ceará", codigoIbge: 23, regiao: "Nordeste" },
  { sigla: "DF", nome: "Distrito Federal", codigoIbge: 53, regiao: "Centro-Oeste" },
  { sigla: "ES", nome: "Espírito Santo", codigoIbge: 32, regiao: "Sudeste" },
  { sigla: "GO", nome: "Goiás", codigoIbge: 52, regiao: "Centro-Oeste" },
  { sigla: "MA", nome: "Maranhão", codigoIbge: 21, regiao: "Nordeste" },
  { sigla: "MT", nome: "Mato Grosso", codigoIbge: 51, regiao: "Centro-Oeste" },
  { sigla: "MS", nome: "Mato Grosso do Sul", codigoIbge: 50, regiao: "Centro-Oeste" },
  { sigla: "MG", nome: "Minas Gerais", codigoIbge: 31, regiao: "Sudeste" },
  { sigla: "PA", nome: "Pará", codigoIbge: 15, regiao: "Norte" },
  { sigla: "PB", nome: "Paraíba", codigoIbge: 25, regiao: "Nordeste" },
  { sigla: "PR", nome: "Paraná", codigoIbge: 41, regiao: "Sul" },
  { sigla: "PE", nome: "Pernambuco", codigoIbge: 26, regiao: "Nordeste" },
  { sigla: "PI", nome: "Piauí", codigoIbge: 22, regiao: "Nordeste" },
  { sigla: "RJ", nome: "Rio de Janeiro", codigoIbge: 33, regiao: "Sudeste" },
  { sigla: "RN", nome: "Rio Grande do Norte", codigoIbge: 24, regiao: "Nordeste" },
  { sigla: "RS", nome: "Rio Grande do Sul", codigoIbge: 43, regiao: "Sul" },
  { sigla: "RO", nome: "Rondônia", codigoIbge: 11, regiao: "Norte" },
  { sigla: "RR", nome: "Roraima", codigoIbge: 14, regiao: "Norte" },
  { sigla: "SC", nome: "Santa Catarina", codigoIbge: 42, regiao: "Sul" },
  { sigla: "SP", nome: "São Paulo", codigoIbge: 35, regiao: "Sudeste" },
  { sigla: "SE", nome: "Sergipe", codigoIbge: 28, regiao: "Nordeste" },
  { sigla: "TO", nome: "Tocantins", codigoIbge: 17, regiao: "Norte" },
];

export function getUfPorSigla(sigla: string): Uf | undefined {
  return UFS.find((uf) => uf.sigla === sigla);
}

export function getUfsPorRegiao(regiao: Regiao | "todas"): Uf[] {
  const lista = regiao === "todas" ? UFS : UFS.filter((uf) => uf.regiao === regiao);
  return [...lista].sort((a, b) => a.nome.localeCompare(b.nome, "pt"));
}
