// Ver docs/requirements/diagnostico-ia.md "Dados de entrada/saída".

export type RecomendacaoIA = {
  acao: string;
  custoEstimado: string;
  prazo: string;
  impactoAlunos: number;
  fundamentacao: string;
};

export type Eixo = "I" | "II" | "III" | "IV";

export type DiagnosticoEixo = {
  eixo: Eixo;
  situacao: string;
  analise: string;
  alertaLegal?: string;
  recomendacoes: RecomendacaoIA[];
  referenciaMunicipio?: string;
  modeloUsado: string;
  geradoEm: string;
  recomendacaoAjustadaEm?: string;
  reprocessadoEm?: string;
};

export type MensagemChat = {
  papel: "user" | "assistant";
  conteudo: string;
  criadoEm: string;
};

export type RespostaChatIA = {
  resposta: string;
  recomendacoesAtualizadas?: RecomendacaoIA[] | null;
};
