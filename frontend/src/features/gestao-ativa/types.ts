// Contratos da API /gestao (backend/app/features/acesso e backend/app/features/diretor).

export type Papel = "diretor" | "secretario" | "admin";

export type SituacaoAcesso = "ativo" | "aguardando_aprovacao" | "rejeitado" | "suspenso" | "revogado";

export type RespostaEntrada = {
  situacao: SituacaoAcesso;
  token: string | null;
  mensagem: string;
};

export type Eu = {
  id: string;
  nome: string;
  email: string;
  papel: Papel;
  escopo: {
    coEntidade: number | null;
    escola: string | null;
    coMunicipio: number | null;
    municipio: string | null;
    uf: string | null;
  };
};

export type EstadoVinculo = "pendente" | "aprovado" | "rejeitado" | "suspenso" | "revogado";

export type SolicitacaoVinculo = {
  id: string;
  nome: string;
  email: string;
  emailConfirmado: boolean;
  coEntidade: number;
  escola: string;
  estado: EstadoVinculo;
  categoria: string | null;
  criadoEm: string;
  decididoEm: string | null;
  metodoVerificacao: string | null;
  justificativa: string | null;
};

export type AcaoVinculo = "aprovar" | "rejeitar" | "suspender" | "reativar" | "revogar";

export type Posicao = "sem_posicao" | "rascunho" | "obstaculo" | "divergencia" | "sem_relato";

export type DashboardEscola = {
  coEntidade: number;
  nome: string;
  municipio: string;
  uf: string;
  rede: string;
  censoVersao: string;
  score: number;
  faixa: string;
  matriculasEducacaoEspecial: number;
  matriculasClasseComum: number;
  eixos: { eixo: string; nome: string; score: number | null; faixa: string | null; barreiras: number; comPosicao: number }[];
  barreiras: { codigo: string; eixo: string; nome: string; dadoCenso: string; pontos: number; nota: string | null; posicao: Posicao; resumo: string | null }[];
  metodologiaVersao: string;
  declaracao: {
    estado: "rascunho" | "emitida" | "publicada";
    versao: number | null;
    comPosicao: number;
    total: number;
    haAlteracoes: boolean;
    emitidaEm: string | null;
    publicadaEm: string | null;
  };
  plano: {
    estado: "sem_declaracao" | "rascunho" | "aguardando_analise" | "aceito" | "ajustes_solicitados" | "reprovado";
    versao: number | null;
    acoesNoRascunho: number;
    comentario: string | null;
    decididaEm: string | null;
    versaoAceita: number | null;
    versaoPublicada: number | null;
    declaracaoBase: number | null;
    desatualizado: boolean;
  } | null;
};

export type PosicaoFinal = "obstaculo" | "divergencia" | "sem_relato";

export type BarreiraDeclaracao = {
  codigo: string;
  eixo: string;
  nome: string;
  dadoCenso: string;
  pontos: number;
  nota: string | null;
  posicao: Posicao;
  texto: string | null;
  resumo: string | null;
  relatoOriginal: string | null;
  perguntaInicial: string;
  atualizadoEm: string | null;
};

export type EstadoDeclaracao = {
  escola: string;
  coEntidade: number;
  censoVersao: string;
  metodologiaVersao: string;
  barreiras: BarreiraDeclaracao[];
  faltam: number;
  haAlteracoes: boolean;
  podeEmitir: boolean;
  versoes: { versao: number; emitidaEm: string; publicadaEm: string | null; retiradaEm: string | null }[];
};

export type VersaoDeclaracao = {
  versao: number;
  escola: string;
  censoVersao: string;
  metodologiaVersao: string;
  emitidaEm: string;
  publicadaEm: string | null;
  retiradaEm: string | null;
  itens: { codigo: string; eixo: string; barreira: string; dadoCenso: string; pontos: number; posicao: PosicaoFinal; texto: string | null; resumo: string | null }[];
};

export type MensagemConversa = { papel: "diretor" | "ia"; texto: string; criadoEm: string };

export type RespostaConversa = { resposta: string; textoFormal: string | null; resumo: string | null };

export type ItemPublico = { codigo: string; eixo: string; barreira: string; dadoCenso: string; posicao: PosicaoFinal; textoPublico: string };

export type PreviaPublica = {
  versao: number;
  escola: string;
  emitidaEm: string;
  publicadaEm: string | null;
  itens: ItemPublico[];
  pontos: { codigo: string; barreira: string; mensagem: string; bloqueia: boolean }[];
  podePublicar: boolean;
  retiradaEm: string | null;
};

export type DeclaracoesDaRede = {
  municipio: string;
  uf: string;
  escolasMunicipais: number;
  comDeclaracao: number;
  escolas: {
    coEntidade: number;
    escola: string;
    versao: number;
    emitidaEm: string;
    publicadaEm: string | null;
    total: number;
    obstaculos: number;
    divergencias: number;
    semRelato: number;
    retiradaEm: string | null;
  }[];
};

// --- Plano de Ação Escolar ---------------------------------------------------------------------
export type Horizonte = "LOA" | "PPA";

export type CamposAcao = {
  codigo: string;
  acao: string;
  relacao: string | null;
  responsavel: string | null;
  prazo: string | null;
  horizonte: Horizonte;
  custoEstimado: string | null;
  premissas: string | null;
};

export type SugestaoPlano = CamposAcao & { id: string; fontes: string[]; incertezas: string | null; lacunas: string[]; ajustada: boolean };

export type AcaoPlano = CamposAcao & { id: string; fontes: string[]; origem: "ia" | "diretor"; editada: boolean };

export type EstadoVersaoPlano = "aguardando_analise" | "aceito" | "ajustes_solicitados" | "reprovado";

// Barreira (sem itemId) ou ação (com itemId) que a secretaria marcou para ajuste; acaoId é a ação do rascunho.
export type Apontamento = { codigo: string; itemId: string | null; acaoId: string | null; texto: string | null };

export type EstadoPlano = {
  escola: string;
  declaracaoBase: number;
  ultimaDeclaracao: number;
  desatualizado: boolean;
  barreiras: { codigo: string; eixo: string; barreira: string; posicao: PosicaoFinal; texto: string | null; resumo: string | null }[];
  sugestoes: SugestaoPlano[];
  acoes: AcaoPlano[];
  versoes: { versao: number; declaracaoVersao: number; submetidaEm: string; estado: EstadoVersaoPlano; decididaEm: string | null; decididaPor: string | null; comentario: string | null; publicadaEm: string | null; retiradaEm: string | null }[];
  podeSubmeter: boolean;
  motivo: string | null;
  fontes: Record<string, string>;
  apontamentos: Apontamento[];
  avisoGuardiao: string | null;
};

export type VersaoPlano = {
  versao: number;
  escola: string;
  declaracaoVersao: number;
  submetidaEm: string;
  estado: EstadoVersaoPlano;
  decididaEm: string | null;
  decididaPor: string | null;
  comentario: string | null;
  itens: (Omit<CamposAcao, "codigo"> & { id: string; codigo: string; barreira: string; fontes: string[]; origem: "ia" | "diretor"; editada: boolean })[];
  fontes: Record<string, string>;
  apontamentos: Apontamento[];
};

// --- Revisão de planos pelo secretário -----------------------------------------------------------
export type ResumoVersaoPlano = EstadoPlano["versoes"][number];

export type PlanoNaFila = {
  coEntidade: number;
  escola: string;
  versao: number;
  estado: EstadoVersaoPlano;
  submetidaEm: string;
  decididaEm: string | null;
  declaracaoVersao: number;
  ultimaDeclaracao: number;
  acoes: number;
  loa: number;
  ppa: number;
  versoes: number;
};

export type FilaPlanos = { municipio: string; uf: string; planos: PlanoNaFila[] };

export type RevisaoPlano = {
  coEntidade: number;
  versao: VersaoPlano;
  ultimaDeclaracao: number;
  versaoAtual: number;
  historico: ResumoVersaoPlano[];
  barreiras: EstadoPlano["barreiras"];
  avisoGuardiao: string | null;
};

export type DecisaoPlano = "aceitar" | "ajustes" | "reprovar";

export type ApontamentoEntrada = { codigo: string; itemId?: string; texto?: string };

// --- Publicação do plano aceito -----------------------------------------------------------------
export type ItemPlanoPublico = {
  codigo: string;
  barreira: string;
  horizonte: Horizonte;
  acao: string | null;
  relacao: string | null;
  responsavel: string | null;
  prazo: string | null;
  custoEstimado: string | null;
  fontes: string[];
};

export type PreviaPlanoPublico = {
  versao: number;
  escola: string;
  aceitoEm: string | null;
  publicadoEm: string | null;
  retiradoEm: string | null;
  itens: ItemPlanoPublico[];
  pontos: { item: string; mensagem: string; bloqueia: boolean }[];
  podePublicar: boolean;
  motivo: string | null;
};

// --- Plano Estratégico Municipal (backend/app/features/plano_municipal) --------------------------
export type Prioridade = "alta" | "media" | "baixa";
export type Cobertura = "total" | "parcial";

export type EscolaAtendida = { coEntidade: number; escola: string; itemIds: string[]; cobertura: Cobertura };

export type ItemEscolarDaRede = {
  ref: string;
  coEntidade: number;
  escola: string;
  itemId: string;
  acao: string;
  responsavel: string | null;
  prazo: string | null;
  horizonte: Horizonte;
  custoEstimado: string | null;
};

export type BarreiraDaRede = {
  codigo: string;
  eixo: string;
  eixoNome: string;
  nome: string;
  escolasComBarreira: number;
  escolasComAcao: number;
  itens: ItemEscolarDaRede[];
};

type CamposAcaoMunicipal = {
  acao: string;
  justificativa: string | null;
  responsavel: string | null;
  prazo: string | null;
  horizonte: Horizonte;
  custoEstimado: string | null;
  premissas: string | null;
  prioridade: Prioridade;
  escolas: EscolaAtendida[];
};

export type SugestaoMunicipal = CamposAcaoMunicipal & { id: string; codigo: string; fontes: string[]; incertezas: string | null; lacunas: string[] };

export type AcaoMunicipal = CamposAcaoMunicipal & { id: string; codigos: string[]; fontes: string[]; origem: "ia" | "secretario"; editada: boolean };

export type NovaAcaoMunicipal = Omit<CamposAcaoMunicipal, "escolas"> & {
  codigos: string[];
  escolas: { coEntidade: number; itemIds: string[]; cobertura: Cobertura }[];
};

export type EstadoPlanoMunicipal = {
  municipio: string;
  uf: string;
  escolasMunicipais: number;
  escolasComPlanoAceito: number;
  barreiras: BarreiraDaRede[];
  sugestoes: SugestaoMunicipal[];
  acoes: AcaoMunicipal[];
  escolasAtendidas: number;
  versoes: { versao: number; confirmadaEm: string; confirmadaPor: string | null; acoes: number; escolasAtendidas: number }[];
  fontes: Record<string, string>;
  avisoGuardiao: string | null;
};

export type AcoesMunicipaisDaEscola = {
  versao: number | null;
  confirmadaEm: string | null;
  acoes: {
    acao: string;
    responsavel: string | null;
    prazo: string | null;
    horizonte: Horizonte;
    prioridade: Prioridade;
    cobertura: Cobertura;
    barreiras: string[];
    escolasAtendidas: number;
  }[];
};
