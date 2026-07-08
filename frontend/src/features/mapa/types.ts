// Ver interface.md §9 e backend/app/features/mapa/schemas.py (fonte de verdade do shape real).

export type KpisNacionais = {
  municipiosCriticos: number;
  escolasSemAee: number;
  scoreMedioNacional: number;
  scoreDesejado: number;
  municipiosMapeados: number;
  totalAlunosEsp: number;
};

export type MunicipioResumo = {
  codigoIbge: number;
  nome: string;
  uf: string;
  score: number;
  faixa: string;
  cor: string;
};

export type MunicipioRanking = MunicipioResumo & {
  rankingNoEstado: number;
  qtdMunicipiosNoEstado: number;
};

export type RankingUf = {
  melhores: MunicipioRanking[];
  criticos: MunicipioRanking[];
};

export type UfRanking = {
  sigla: string;
  codigoUf: number;
  qtdMunicipios: number;
  totalAlunosEsp: number;
  score: number;
  faixa: string;
  cor: string;
  rankingNacional: number;
};
