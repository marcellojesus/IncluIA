"use client";

// Validação de vínculos de diretores pela secretaria municipal (RF-05, RF-09; RN-03, RN-04, RN-12).
// O protótipo v2 não tinha esta tela; ela segue o mesmo estilo. Aprovar exige registrar como o
// vínculo foi confirmado numa fonte institucional independente do pedido.
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { decidirVinculo, listarVinculos } from "../api";
import type { AcaoVinculo, Eu, SolicitacaoVinculo } from "../types";
import { AVISO_TEXTO_LIVRE, Aviso, Botao, Cartao, CampoTexto, Erro, MOTIVOS, Selecao, Selo } from "./ui";

type Aba = "pendentes" | "ativos" | "encerrados";

const ABAS: { id: Aba; rotulo: string }[] = [
  { id: "pendentes", rotulo: "Pendentes" },
  { id: "ativos", rotulo: "Ativos e suspensos" },
  { id: "encerrados", rotulo: "Rejeitados e revogados" },
];

const ACOES: Record<AcaoVinculo, { titulo: string; rotulo: string; ajuda: string; botao: string; variante: "primario" | "perigo" }> = {
  aprovar: {
    titulo: "Aprovar vínculo",
    rotulo: "Como o vínculo foi confirmado",
    ajuda: "Fonte institucional independente do pedido: ato de designação, registro funcional, contato pelo canal oficial da escola.",
    botao: "Aprovar vínculo",
    variante: "primario",
  },
  rejeitar: { titulo: "Rejeitar solicitação", rotulo: "Justificativa", ajuda: "O candidato verá que o vínculo não foi confirmado e poderá corrigir os dados.", botao: "Rejeitar", variante: "perigo" },
  suspender: { titulo: "Suspender acesso", rotulo: "Justificativa", ajuda: "O acesso é bloqueado na hora e pode ser reativado depois.", botao: "Suspender", variante: "perigo" },
  reativar: { titulo: "Reativar acesso", rotulo: "Justificativa", ajuda: "O diretor volta a acessar a escola do vínculo.", botao: "Reativar", variante: "primario" },
  revogar: { titulo: "Revogar acesso", rotulo: "Justificativa", ajuda: "Encerra o vínculo. Voltar exige nova solicitação e nova aprovação.", botao: "Revogar", variante: "perigo" },
};

const ESTADOS: Record<SolicitacaoVinculo["estado"], { texto: string; tom: "ambar" | "verde" | "vermelho" | "neutro" | "azul" }> = {
  pendente: { texto: "Pendente", tom: "ambar" },
  aprovado: { texto: "Ativo", tom: "verde" },
  suspenso: { texto: "Suspenso", tom: "vermelho" },
  rejeitado: { texto: "Rejeitado", tom: "neutro" },
  revogado: { texto: "Revogado", tom: "neutro" },
};

const data = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("pt-BR") : "—");

function acoesDisponiveis(v: SolicitacaoVinculo): AcaoVinculo[] {
  if (v.estado === "pendente") return ["aprovar", "rejeitar"];
  if (v.estado === "aprovado") return ["suspender", "revogar"];
  if (v.estado === "suspenso") return ["reativar", "revogar"];
  return [];
}

export function VinculosSecretario({ eu, onMudou }: { eu: Eu; onMudou?: () => void }) {
  const [aba, setAba] = useState<Aba>("pendentes");
  const [lista, setLista] = useState<SolicitacaoVinculo[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [decisao, setDecisao] = useState<{ vinculo: SolicitacaoVinculo; acao: AcaoVinculo } | null>(null);
  const [versao, setVersao] = useState(0);

  useEffect(() => {
    let cancelado = false;
    listarVinculos(aba)
      .then((dados) => !cancelado && setLista(dados))
      .catch((falha) => !cancelado && setErro((falha as Error).message));
    return () => {
      cancelado = true;
    };
  }, [aba, versao]);

  function recarregar(novaAba: Aba = aba) {
    setLista(null);
    setAba(novaAba);
    setVersao((v) => v + 1);
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <p className="text-xs font-extrabold uppercase tracking-wider text-accent">
        Secretaria municipal · {eu.escopo.municipio}/{eu.escopo.uf}
      </p>
      <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Vínculos de diretores</h1>
      <p className="mt-2 max-w-3xl text-[15px] text-gray-600">
        Confirme que quem pediu acesso é de fato diretor(a) da escola, usando os registros da rede. A confirmação de e-mail só prova
        o controle da caixa de correio, não o cargo.
      </p>

      <div role="tablist" aria-label="Situação dos vínculos" className="mt-6 flex gap-1 border-b border-black/10">
        {ABAS.map((item) => (
          <button
            key={item.id}
            role="tab"
            aria-selected={aba === item.id}
            onClick={() => { recarregar(item.id); setAviso(null); }}
            className={`-mb-px border-b-[3px] px-4 py-2 text-sm font-bold ${aba === item.id ? "border-accent text-gov-blue-dark" : "border-transparent text-gray-500 hover:text-gov-blue-dark"}`}
          >
            {item.rotulo}
          </button>
        ))}
      </div>

      {aviso && (
        <p role="status" className="mt-4 rounded-lg bg-[#e7f3ec] px-4 py-2 text-[13px] text-[#2f7a55]">
          {aviso}
        </p>
      )}
      <div className="mt-4">
        <Erro mensagem={erro} />
      </div>

      <Cartao className="overflow-x-auto">
        {lista === null ? (
          <p role="status" className="p-5 text-sm text-gray-500">Carregando…</p>
        ) : lista.length === 0 ? (
          <p className="p-5 text-sm text-gray-600">
            {aba === "pendentes" ? "Nenhuma solicitação aguardando validação." : "Nenhum vínculo nesta situação."}
          </p>
        ) : (
          <table className="w-full min-w-[820px] text-left text-[13px]">
            <thead className="border-b border-black/5 text-[11px] uppercase tracking-wider text-gray-500">
              <tr>
                <th scope="col" className="px-4 py-2.5">Pessoa</th>
                <th scope="col" className="px-4 py-2.5">Escola</th>
                <th scope="col" className="px-4 py-2.5">Pedido</th>
                <th scope="col" className="px-4 py-2.5">Situação</th>
                <th scope="col" className="px-4 py-2.5"><span className="sr-only">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              {lista.map((v) => (
                <tr key={v.id} className="border-b border-black/5 last:border-0">
                  <td className="px-4 py-3 align-top">
                    <div className="font-bold text-ink">{v.nome}</div>
                    <div className="text-[12px] text-gray-500">{v.email}</div>
                    {!v.emailConfirmado && <div className="mt-1"><Selo tom="ambar">E-mail não confirmado</Selo></div>}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <div>{v.escola}</div>
                    <div className="text-[12px] text-gray-500">INEP {v.coEntidade}</div>
                  </td>
                  <td className="px-4 py-3 align-top text-gray-600">
                    {data(v.criadoEm)}
                    {v.decididoEm && <div className="text-[12px]">Decidido em {data(v.decididoEm)}</div>}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <Selo tom={ESTADOS[v.estado].tom}>{ESTADOS[v.estado].texto}</Selo>
                    {(v.metodoVerificacao || v.justificativa) && (
                      <div className="mt-1 max-w-[220px] text-[12px] text-gray-500">{v.justificativa ?? v.metodoVerificacao}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right align-top">
                    <div className="flex justify-end gap-2">
                      {acoesDisponiveis(v).map((acao) => (
                        <Botao
                          key={acao}
                          variante={ACOES[acao].variante === "primario" ? "primario" : "perigo"}
                          className="px-3 py-1.5 text-[12px]"
                          disabled={acao === "aprovar" && !v.emailConfirmado}
                          title={acao === "aprovar" && !v.emailConfirmado ? "O candidato ainda não confirmou o e-mail" : undefined}
                          onClick={() => setDecisao({ vinculo: v, acao })}
                        >
                          {ACOES[acao].botao}
                        </Botao>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Cartao>

      {decisao && (
        <DecisaoModal
          vinculo={decisao.vinculo}
          acao={decisao.acao}
          onFechar={() => setDecisao(null)}
          onConcluir={(mensagem) => { setDecisao(null); setAviso(`${decisao.vinculo.nome}: ${mensagem}`); recarregar(); onMudou?.(); }}
        />
      )}
    </div>
  );
}

function DecisaoModal({
  vinculo,
  acao,
  onFechar,
  onConcluir,
}: {
  vinculo: SolicitacaoVinculo;
  acao: AcaoVinculo;
  onFechar: () => void;
  onConcluir: (mensagem: string) => void;
}) {
  const config = ACOES[acao];
  const [texto, setTexto] = useState("");
  const [categoria, setCategoria] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function confirmar(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setErro(null);
    try {
      const resposta = await decidirVinculo(vinculo.id, acao, categoria, texto);
      onConcluir(resposta.mensagem);
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo={config.titulo} subtitulo={`${vinculo.nome} · ${vinculo.escola} (INEP ${vinculo.coEntidade})`} onFechar={onFechar}>
      <form onSubmit={confirmar}>
        {acao === "aprovar" && (
          <div className="mb-3">
            <Aviso>Aprove só depois de conferir nos registros da rede. O candidato não aprova o próprio pedido, e a aprovação fica registrada com seu nome e data.</Aviso>
          </div>
        )}
        <Selecao id="motivo-decisao" rotulo="Motivo" opcoes={MOTIVOS[acao]} value={categoria} onChange={(e) => setCategoria(e.target.value)} required />
        <CampoTexto id="texto-decisao" rotulo={config.rotulo} ajuda={`${config.ajuda} ${AVISO_TEXTO_LIVRE}`} value={texto} onChange={(e) => setTexto(e.target.value)} required minLength={5} />
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>Cancelar</Botao>
          <Botao type="submit" variante={config.variante === "primario" ? "primario" : "perigo"} disabled={enviando || !categoria || texto.trim().length < 5}>
            {enviando ? "Registrando…" : config.botao}
          </Botao>
        </div>
      </form>
    </Modal>
  );
}
