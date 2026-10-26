// Chamadas à API da Gestão Ativa (/gestao). Erros chegam com a mensagem do servidor, que já é
// escrita para o usuário (backend/app/features/acesso/servico.py).
import { API_BASE_URL } from "@/shared/lib/apiConfig";

import { useGestaoStore } from "./store";
import type {
  AcaoVinculo,
  CamposAcao,
  EstadoPlano,
  VersaoPlano,
  ApontamentoEntrada,
  AcoesMunicipaisDaEscola,
  EstadoPlanoMunicipal,
  NovaAcaoMunicipal,
  DecisaoPlano,
  PreviaPlanoPublico,
  FilaPlanos,
  RevisaoPlano,
  DeclaracoesDaRede,
  PreviaPublica,
  DashboardEscola,
  EstadoDeclaracao,
  Eu,
  MensagemConversa,
  PosicaoFinal,
  RespostaConversa,
  RespostaEntrada,
  SolicitacaoVinculo,
  VersaoDeclaracao,
} from "./types";

export class SemAcesso extends Error {
  constructor(public readonly status: 401 | 403, mensagem: string) {
    super(mensagem);
    this.name = "SemAcesso";
  }
}

async function chamar<T>(caminho: string, opcoes: RequestInit = {}, autenticado = false): Promise<T> {
  const token = useGestaoStore.getState().token;
  let resposta: Response;
  try {
    resposta = await fetch(`${API_BASE_URL}/gestao${caminho}`, {
      ...opcoes,
      headers: {
        "Content-Type": "application/json",
        ...(autenticado && token ? { Authorization: `Bearer ${token}` } : {}),
        ...opcoes.headers,
      },
    });
  } catch {
    throw new Error("Não foi possível falar com o servidor. Verifique a conexão e tente de novo.");
  }
  const corpo = await resposta.json().catch(() => null);
  const mensagem = typeof corpo?.detail === "string" ? corpo.detail : "Algo deu errado. Tente de novo.";
  if (resposta.status === 401 || resposta.status === 403) throw new SemAcesso(resposta.status, mensagem);
  if (!resposta.ok) throw new Error(mensagem);
  return corpo as T;
}

const post = (corpo: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(corpo) });

export const solicitarAcessoDiretor = (dados: { nome: string; email: string; coEntidade: number }) =>
  chamar<{ mensagem: string }>("/acesso/diretor", post(dados));

export const pedirCodigo = (email: string) => chamar<{ mensagem: string }>("/acesso/codigo", post({ email }));

export const entrar = (email: string, codigo: string) =>
  chamar<RespostaEntrada>("/acesso/entrar", post({ email, codigo }));

export const getEu = () => chamar<Eu>("/eu", {}, true);

export const getDashboardEscola = () => chamar<DashboardEscola>("/diretor/escola", {}, true);

export const listarVinculos = (situacao: "pendentes" | "ativos" | "encerrados") =>
  chamar<SolicitacaoVinculo[]>(`/secretario/vinculos?situacao=${situacao}`, {}, true);

export const decidirVinculo = (id: string, acao: AcaoVinculo, categoria: string, texto: string) =>
  chamar<{ mensagem: string }>(`/secretario/vinculos/${id}/${acao}`, post({ categoria, texto }), true);

export const provisionarSecretario = (dados: { nome: string; email: string; coMunicipio: number; categoria: string; metodoVerificacao: string }) =>
  chamar<{ mensagem: string }>("/admin/secretarios", post(dados), true);

// Só existe com AMBIENTE=dev no backend e acesso pela própria máquina; fora disso responde 404.
export type EmailTeste = { para: string; assunto: string; texto: string; codigo: string; enviadaEm: string };
export const getEmailsTeste = () => chamar<EmailTeste[]>("/dev/emails");

// --- Declaração de Obstáculos (backend/app/features/declaracao) ---------------------------------
const put = (corpo: unknown): RequestInit => ({ method: "PUT", body: JSON.stringify(corpo) });
const base = "/diretor/declaracao";

export const getDeclaracao = () => chamar<EstadoDeclaracao>(base, {}, true);

export const registrarPosicao = (codigo: string, corpo: { posicao: PosicaoFinal; texto?: string | null; resumo?: string | null }) =>
  chamar<EstadoDeclaracao>(`${base}/barreiras/${codigo}`, put(corpo), true);

export const retificarPosicao = (codigo: string) =>
  chamar<EstadoDeclaracao>(`${base}/barreiras/${codigo}`, { method: "DELETE" }, true);

export const emitirDeclaracao = () => chamar<VersaoDeclaracao>(`${base}/emitir`, { method: "POST" }, true);

export const getVersaoDeclaracao = (numero: number) => chamar<VersaoDeclaracao>(`${base}/versoes/${numero}`, {}, true);

export const getConversa = (codigo: string) => chamar<MensagemConversa[]>(`${base}/barreiras/${codigo}/conversa`, {}, true);

export const conversar = (codigo: string, corpo: { mensagem?: string; formalizar?: boolean }) =>
  chamar<RespostaConversa>(`${base}/barreiras/${codigo}/conversa`, post(corpo), true);

export const getPreviaPublica = (numero: number) => chamar<PreviaPublica>(`${base}/versoes/${numero}/publica`, {}, true);

export const publicarDeclaracao = (numero: number) =>
  chamar<PreviaPublica>(`${base}/versoes/${numero}/publicar`, post({ aprovado: true }), true);

// --- Secretário: declarações emitidas da rede -----------------------------------------------------
export const getDeclaracoesRede = () => chamar<DeclaracoesDaRede>("/secretario/declaracoes", {}, true);

export const getVersaoDaRede = (coEntidade: number, numero: number) =>
  chamar<VersaoDeclaracao>(`/secretario/declaracoes/${coEntidade}/versoes/${numero}`, {}, true);

export const retirarPublicacao = (numero: number, motivo: string) =>
  chamar<PreviaPublica>(`${base}/versoes/${numero}/retirar`, post({ motivo }), true);

// --- Plano de Ação Escolar (backend/app/features/plano) ------------------------------------------
const plano = "/diretor/plano";

export const getPlano = () => chamar<EstadoPlano>(plano, {}, true);

export const sugerirAcoes = (codigo: string, orientacao?: string) =>
  chamar<EstadoPlano>(`${plano}/barreiras/${codigo}/sugestoes`, post({ orientacao: orientacao || null }), true);

export const aceitarSugestao = (id: string, edicao?: CamposAcao) =>
  chamar<EstadoPlano>(`${plano}/sugestoes/${id}/aceitar`, post(edicao ? { edicao } : {}), true);

export const ajustarSugestao = (id: string, pedido: string) => chamar<EstadoPlano>(`${plano}/sugestoes/${id}/ajustar`, post({ pedido }), true);

export const descartarSugestao = (id: string) => chamar<EstadoPlano>(`${plano}/sugestoes/${id}/descartar`, post({}), true);

export const incluirAcao = (campos: CamposAcao) => chamar<EstadoPlano>(`${plano}/acoes`, post(campos), true);

export const editarAcao = (id: string, campos: CamposAcao) => chamar<EstadoPlano>(`${plano}/acoes/${id}`, put(campos), true);

export const removerAcao = (id: string) => chamar<EstadoPlano>(`${plano}/acoes/${id}`, { method: "DELETE" }, true);

export const atualizarBasePlano = () => chamar<EstadoPlano>(`${plano}/atualizar-base`, post({}), true);

export const submeterPlano = () => chamar<VersaoPlano>(`${plano}/submeter`, post({ confirmado: true }), true);

// --- Secretário: fila e revisão de planos (backend/app/features/plano/router_secretario.py) ------
export const getFilaPlanos = () => chamar<FilaPlanos>("/secretario/planos", {}, true);

export const getRevisaoPlano = (coEntidade: number, numero: number) =>
  chamar<RevisaoPlano>(`/secretario/planos/${coEntidade}/versoes/${numero}`, {}, true);

export const decidirPlano = (coEntidade: number, numero: number, decisao: DecisaoPlano, comentario: string, apontamentos: ApontamentoEntrada[] = []) =>
  chamar<RevisaoPlano>(
    `/secretario/planos/${coEntidade}/versoes/${numero}/decisao`,
    post({ decisao, comentario: comentario.trim() || null, apontamentos }),
    true,
  );

// --- Publicação do plano aceito (backend/app/features/plano/publicacao.py) -----------------------
export const getPreviaPlanoPublico = (numero: number) => chamar<PreviaPlanoPublico>(`${plano}/versoes/${numero}/publica`, {}, true);

export const publicarPlano = (numero: number) =>
  chamar<PreviaPlanoPublico>(`${plano}/versoes/${numero}/publicar`, post({ aprovado: true }), true);

export const retirarPlano = (numero: number, motivo: string) =>
  chamar<PreviaPlanoPublico>(`${plano}/versoes/${numero}/retirar`, post({ motivo }), true);

// --- Plano Estratégico Municipal (backend/app/features/plano_municipal/router.py) ----------------
const municipal = "/secretario/plano-municipal";

export const getPlanoMunicipal = () => chamar<EstadoPlanoMunicipal>(municipal, {}, true);

export const sugerirAcoesMunicipais = (codigo: string, orientacao?: string) =>
  chamar<EstadoPlanoMunicipal>(`${municipal}/barreiras/${codigo}/sugestoes`, post({ orientacao: orientacao || null }), true);

export const aceitarSugestaoMunicipal = (id: string, edicao?: NovaAcaoMunicipal) =>
  chamar<EstadoPlanoMunicipal>(`${municipal}/sugestoes/${id}/aceitar`, post(edicao ? { edicao } : {}), true);

export const descartarSugestaoMunicipal = (id: string) => chamar<EstadoPlanoMunicipal>(`${municipal}/sugestoes/${id}/descartar`, post({}), true);

export const incluirAcaoMunicipal = (dados: NovaAcaoMunicipal) => chamar<EstadoPlanoMunicipal>(`${municipal}/acoes`, post(dados), true);

export const editarAcaoMunicipal = (id: string, dados: NovaAcaoMunicipal) => chamar<EstadoPlanoMunicipal>(`${municipal}/acoes/${id}`, put(dados), true);

export const removerAcaoMunicipal = (id: string) => chamar<EstadoPlanoMunicipal>(`${municipal}/acoes/${id}`, { method: "DELETE" }, true);

export const confirmarPlanoMunicipal = () => chamar<{ versao: number }>(`${municipal}/confirmar`, post({ confirmado: true }), true);

export const getAcoesMunicipaisDaEscola = () => chamar<AcoesMunicipaisDaEscola>("/diretor/acoes-municipais", {}, true);
