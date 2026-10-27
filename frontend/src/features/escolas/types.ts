// Ver interface.md §9 "Escola (linha da lista)" e docs/requirements/escolas.md.

// "na" só ocorre no Eixo IV, para escolas especiais exclusivas (RN-05 de
// docs/business-rules/escolas.md) — taxa de inclusão em classe comum não se aplica a elas.
// "omitido" só ocorre no Eixo IV, em escola com 1 a 4 matrículas da educação especial (RN-06).
export type StatusEixo = "ok" | "warn" | "nok" | "na" | "omitido";

export type Rede = "Federal" | "Estadual" | "Municipal" | "Privada";

export type Escola = {
  coEntidade: number;
  nome: string;
  bairro: string;
  rede: Rede;
  // null quando a escola tem de 1 a 4 matrículas da educação especial (RN-06).
  alunosEsp: number | null;
  statusEixoI: StatusEixo;
  statusEixoII: StatusEixo;
  statusEixoIII: StatusEixo;
  statusEixoIV: StatusEixo;
  score: number;
  faixa: string;
  cor: string;
  especialExclusiva: boolean;
  // Score público calculado com a taxa média de classe comum, para não identificar estudantes.
  dadosProtegidos: boolean;
  rankingMunicipal: number;
  qtdEscolasMunicipio: number;
};
