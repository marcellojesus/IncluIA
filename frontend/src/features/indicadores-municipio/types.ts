// Ver interface.md §9 "Município (detalhe, usado nas abas Indicadores/IA)".

export type StatusEixo = "ok" | "warn" | "nok";

export type EixoIndicador = {
  status: StatusEixo;
  icone: string;
  label: string;
  valor: string;
  subtexto: string;
};

export type ScoreEixo = {
  label: string;
  percentual: number;
  valor: string;
  cor: string;
};

export type Conformidade = "conforme" | "parcial" | "nao_conforme";

export type CriterioDecreto = {
  eixo: string;
  criterio: string;
  variavelCenso: string;
  resultado: string;
  conformidade: Conformidade;
};

export type MunicipioDetalhe = {
  codigoIbge: number;
  nome: string;
  uf: string;
  score: number;
  faixa: string;
  cor: string;
  eixos: EixoIndicador[];
  scoreEixos: ScoreEixo[];
  dadosGerais: Array<[string, string]>;
  detalhamentoDecreto: CriterioDecreto[];
};
