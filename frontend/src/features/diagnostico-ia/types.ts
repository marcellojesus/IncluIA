// Ver docs/requirements/diagnostico-ia.md "Dados de entrada/saída".

export type Eixo = "I" | "II" | "III" | "IV";

export type NarrativaEixo = {
  eixo: Eixo;
  situacao: string;
  analise: string;
  alertaLegal?: string | null;
  referenciaMunicipio?: string | null;
  // "dados_brutos" quando nenhum provedor de IA respondeu: o texto é só o dado calculado.
  modeloUsado: string;
  geradoEm: string;
};

export type NarrativaMunicipio = {
  codigoIbge: number;
  censoVersao: string;
  eixos: NarrativaEixo[];
};
