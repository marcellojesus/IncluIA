// Ver interface.md §9 "Escola (linha da lista)" e docs/requirements/escolas.md.

// "na" só ocorre no Eixo IV, para escolas especiais exclusivas (RN-05 de
// docs/business-rules/escolas.md) — taxa de inclusão em classe comum não se aplica a elas.
export type StatusEixo = "ok" | "warn" | "nok" | "na";

export type Rede = "Federal" | "Estadual" | "Municipal" | "Privada";

export type Escola = {
  coEntidade: number;
  nome: string;
  bairro: string;
  rede: Rede;
  alunosEsp: number;
  statusEixoI: StatusEixo;
  statusEixoII: StatusEixo;
  statusEixoIII: StatusEixo;
  statusEixoIV: StatusEixo;
  score: number;
  faixa: string;
  cor: string;
  especialExclusiva: boolean;
  rankingMunicipal: number;
  qtdEscolasMunicipio: number;
};
