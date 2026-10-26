"use client";

// Registrar obstáculos (view-obstacles do protótipo v2; requirements/diretor/declaracao-obstaculos.md).
// Uma barreira por vez: conversa com o assistente, divergência com o Censo ou "sem relato nesta
// versão". A IA propõe; só o diretor confirma (RN-DO-02). Com todas as posições, emite a Declaração.
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { conversar, getConversa, getDeclaracao, registrarPosicao, retificarPosicao } from "../api";
import { NOMES_EIXOS, POSICOES, POSICOES_FINAIS } from "../rotulos";
import type { BarreiraDeclaracao, EstadoDeclaracao, MensagemConversa, VersaoDeclaracao } from "../types";
import { DeclaracaoConsolidada, Divergencia, PublicarDeclaracao, RetirarPublicacao, RevisarObstaculo, VersaoEmitida } from "./ModaisDeclaracao";
import { Aviso, Botao, Cartao, Erro, Selo } from "./ui";

type Modal =
  | { tipo: "obstaculo"; proposta: { texto: string; resumo: string } }
  | { tipo: "divergencia" }
  | { tipo: "declaracao" }
  | { tipo: "emitida"; versao: VersaoDeclaracao }
  | { tipo: "publicar"; numero: number }
  | { tipo: "retirar"; numero: number }
  | null;

const finalizada = (b: BarreiraDeclaracao) => POSICOES_FINAIS.includes(b.posicao);

export function DeclaracaoObstaculos({ eixo }: { eixo: string | null }) {
  const [estado, setEstado] = useState<EstadoDeclaracao | null>(null);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [conversa, setConversa] = useState<MensagemConversa[]>([]);
  const [proposta, setProposta] = useState<{ texto: string; resumo: string } | null>(null);
  const [resposta, setResposta] = useState("");
  const [modal, setModal] = useState<Modal>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [aguardando, setAguardando] = useState(false);

  const noEscopo = useMemo(
    () => (estado ? estado.barreiras.filter((b) => !eixo || b.eixo === eixo) : []),
    [estado, eixo],
  );
  const barreira = estado?.barreiras.find((b) => b.codigo === selecionada) ?? null;

  const aplicarEstado = useCallback(
    (novo: EstadoDeclaracao, avancar: boolean) => {
      setEstado(novo);
      if (!avancar) return;
      const escopo = novo.barreiras.filter((b) => !eixo || b.eixo === eixo);
      const proxima = escopo.find((b) => !finalizada(b)) ?? null;
      setSelecionada(proxima?.codigo ?? escopo[0]?.codigo ?? null);
      if (!proxima && novo.faltam === 0) setModal({ tipo: "declaracao" });
    },
    [eixo],
  );

  useEffect(() => {
    getDeclaracao()
      .then((dados) => aplicarEstado(dados, true))
      .catch((falha) => setErro((falha as Error).message));
  }, [aplicarEstado]);

  useEffect(() => {
    if (!barreira || finalizada(barreira)) return;
    let ativo = true;
    getConversa(barreira.codigo)
      .then((mensagens) => ativo && setConversa(mensagens))
      .catch(() => ativo && setConversa([]));
    return () => {
      ativo = false;
    };
  }, [barreira]);

  function escolher(codigo: string) {
    setSelecionada(codigo);
    setConversa([]);
    setProposta(null);
    setResposta("");
    setErro(null);
  }

  async function enviarResposta(formalizar: boolean) {
    if (!barreira) return;
    setErro(null);
    setAguardando(true);
    try {
      const retorno = await conversar(barreira.codigo, formalizar ? { formalizar: true } : { mensagem: resposta });
      setResposta("");
      setConversa(await getConversa(barreira.codigo));
      if (retorno.textoFormal) {
        const nova = { texto: retorno.textoFormal, resumo: retorno.resumo ?? "" };
        setProposta(nova);
        if (formalizar) setModal({ tipo: "obstaculo", proposta: nova });
      } else if (formalizar) {
        setAviso(retorno.resposta);
      }
      if (estado && barreira.posicao === "sem_posicao") setEstado(await getDeclaracao());
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setAguardando(false);
    }
  }

  async function semRelato() {
    if (!barreira) return;
    setErro(null);
    try {
      aplicarEstado(await registrarPosicao(barreira.codigo, { posicao: "sem_relato" }), true);
      setAviso("Registrado: sem relato nesta versão.");
      setProposta(null);
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  async function retificar() {
    if (!barreira) return;
    setErro(null);
    try {
      aplicarEstado(await retificarPosicao(barreira.codigo), false);
      setAviso("Posição reaberta. A retificação entra na próxima versão emitida da Declaração.");
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  function aoRegistrar(novo: EstadoDeclaracao, mensagem: string) {
    setModal(null);
    setProposta(null);
    setConversa([]);
    setAviso(mensagem);
    aplicarEstado(novo, true);
  }

  if (!estado) {
    return erro ? (
      <p role="alert" className="mx-auto mt-10 max-w-md rounded-lg bg-[#fbe9e7] p-4 text-sm text-[#b23838]">{erro}</p>
    ) : (
      <p role="status" className="mt-16 text-center text-sm text-gray-500">Carregando a Declaração…</p>
    );
  }

  const semPosicaoNoEscopo = noEscopo.filter((b) => !finalizada(b)).length;
  const indice = barreira ? noEscopo.findIndex((b) => b.codigo === barreira.codigo) + 1 : 0;
  const relato = conversa.filter((m) => m.papel === "diretor").map((m) => m.texto).join("\n\n");

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <nav className="text-xs text-gray-500" aria-label="Trilha">
        <Link href="/gestao/diretor" className="font-bold text-gov-blue hover:underline">← Dashboard da escola</Link> / Declaração de Obstáculos
      </nav>
      <p className="mt-3 text-xs font-extrabold uppercase tracking-wider text-accent">Diretor · {estado.escola}</p>
      <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Registrar obstáculos</h1>
      <p className="mt-2 max-w-3xl text-[15px] text-gray-600">
        Para cada barreira, relate o obstáculo, informe divergência com o dado do Censo ou indique que não há relato nesta versão. Com
        todas as barreiras com posição, você emite a Declaração.
      </p>
      <div className="mt-4">
        <Aviso>
          <strong>{eixo ? `Registrando o Eixo ${eixo} · ${NOMES_EIXOS[eixo]}.` : "Registrando todos os eixos."}</strong>{" "}
          {semPosicaoNoEscopo} {semPosicaoNoEscopo === 1 ? "barreira" : "barreiras"} sem posição. Ao registrar uma posição, você segue para a
          próxima barreira.
        </Aviso>
      </div>

      {aviso && (
        <p role="status" className="mt-4 rounded-lg bg-[#e7f3ec] px-4 py-2 text-[13px] text-[#2f7a55]">
          {aviso}
        </p>
      )}

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div>
          {barreira ? (
            <Cartao className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-[12px] font-bold text-gray-500">Barreira {indice} de {noEscopo.length}</span>
                <Selo tom={POSICOES[barreira.posicao].tom}>{POSICOES[barreira.posicao].texto}</Selo>
              </div>
              <div className="mt-2">
                <Selo tom="teal">Eixo {barreira.eixo} · {NOMES_EIXOS[barreira.eixo]}</Selo>
              </div>
              <h2 className="mt-2 text-xl font-extrabold text-ink">{barreira.nome}</h2>
              <p className="mt-1 text-[13px] text-gray-600">
                <strong>Dado do Censo {estado.censoVersao}:</strong> {barreira.dadoCenso}
                {barreira.nota && <span className="text-gray-500"> ({barreira.nota})</span>}
              </p>

              {finalizada(barreira) ? (
                <div className="mt-4">
                  {barreira.texto ? (
                    <div className="rounded-lg bg-black/[.03] p-3 text-[14px] text-ink">
                      {barreira.texto}
                      {barreira.resumo && <div className="mt-2 text-[12px] text-gray-500">Resumo: {barreira.resumo}</div>}
                    </div>
                  ) : (
                    <p className="text-[14px] text-gray-600">A escola escolheu não apresentar relato sobre esta barreira nesta versão.</p>
                  )}
                  <div className="mt-4 flex flex-wrap items-center gap-3">
                    <Botao variante="contorno" onClick={retificar}>Retificar posição</Botao>
                    <span className="text-[12px] text-gray-500">A retificação entra na próxima versão emitida da Declaração.</span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="mt-4 space-y-3" aria-live="polite">
                    <Mensagem papel="ia" texto={barreira.perguntaInicial} />
                    {conversa.map((m, i) => (
                      <Mensagem key={`${m.criadoEm}-${i}`} papel={m.papel} texto={m.texto} />
                    ))}
                    {aguardando && <p role="status" className="text-[13px] text-gray-500">O assistente está escrevendo…</p>}
                  </div>

                  {proposta && (
                    <div className="mt-4 rounded-lg border border-gov-blue/30 bg-gov-blue-lt p-3">
                      <div className="text-[11px] font-extrabold uppercase tracking-wider text-gov-blue-mid">Texto formal proposto pela IA</div>
                      <p className="mt-1 text-[14px] text-ink">{proposta.texto}</p>
                      <Botao className="mt-2" onClick={() => setModal({ tipo: "obstaculo", proposta })}>Revisar e confirmar</Botao>
                    </div>
                  )}

                  <div className="mt-4">
                    <label htmlFor="resposta-obstaculo" className="mb-1 block text-xs font-bold text-gray-700">Sua resposta</label>
                    <textarea
                      id="resposta-obstaculo"
                      rows={3}
                      value={resposta}
                      onChange={(e) => setResposta(e.target.value)}
                      placeholder="Conte a situação com suas palavras…"
                      className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gov-blue focus:ring-2 focus:ring-gov-blue/20"
                    />
                    <p className="mt-1 text-[11px] text-gray-500">
                      Não inclua nomes ou dados de estudantes. O texto passa por um filtro de dados pessoais antes de ir para a IA.
                    </p>
                  </div>
                  <Erro mensagem={erro} />
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Botao onClick={() => enviarResposta(false)} disabled={aguardando || resposta.trim().length < 3}>Adicionar resposta</Botao>
                    <Botao variante="contorno" onClick={() => enviarResposta(true)} disabled={aguardando || !conversa.some((m) => m.papel === "diretor")}>
                      Revisar texto formal
                    </Botao>
                    <Botao variante="discreto" onClick={() => setModal({ tipo: "obstaculo", proposta: { texto: "", resumo: "" } })}>
                      Escrever o texto direto
                    </Botao>
                  </div>

                  <div className="mt-5 border-t border-black/5 pt-4">
                    <span className="mr-2 text-[12px] font-bold text-gray-500">Outras posições:</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Botao variante="contorno" onClick={() => setModal({ tipo: "divergencia" })}>Informar divergência com o dado do Censo</Botao>
                      <Botao variante="discreto" onClick={semRelato}>Sem relato nesta versão</Botao>
                    </div>
                  </div>
                </>
              )}
            </Cartao>
          ) : (
            <Cartao className="p-5 text-sm text-gray-600">Nenhuma barreira identificada para a escola neste recorte.</Cartao>
          )}
        </div>

        <aside className="space-y-4">
          <Cartao className="p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-extrabold text-gov-blue-dark">Barreiras por eixo</h2>
              <Selo tom="neutro">{estado.barreiras.length - estado.faltam} de {estado.barreiras.length} com posição</Selo>
            </div>
            {[...new Set(estado.barreiras.map((b) => b.eixo))].map((e) => {
              const doEixo = estado.barreiras.filter((b) => b.eixo === e);
              return (
                <div key={e} className="mt-3">
                  <div className="flex items-center justify-between text-[12px] font-bold text-gray-600">
                    <span>Eixo {e} · {NOMES_EIXOS[e]}</span>
                    <span>{doEixo.filter(finalizada).length}/{doEixo.length}</span>
                  </div>
                  <ul className="mt-1 space-y-1">
                    {doEixo.map((b) => (
                      <li key={b.codigo}>
                        <button
                          onClick={() => escolher(b.codigo)}
                          aria-current={b.codigo === selecionada}
                          className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left text-[12px] ${b.codigo === selecionada ? "bg-gov-blue-lt font-bold" : "hover:bg-black/[.03]"}`}
                        >
                          <span className="text-ink">{b.nome}</span>
                          <Selo tom={POSICOES[b.posicao].tom}>{POSICOES[b.posicao].texto}</Selo>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </Cartao>

          <Cartao className="p-4">
            <h2 className="text-sm font-extrabold text-gov-blue-dark">Declaração de Obstáculos</h2>
            <p className="mt-1 text-[12px] text-gray-600">
              Emita quando todas as barreiras tiverem posição. A versão emitida vai para a secretaria e é a base do Plano de Ação. Os dados do
              Censo não são alterados.
            </p>
            <Botao variante="coral" className="mt-3 w-full" onClick={() => setModal({ tipo: "declaracao" })}>
              Revisar e emitir declaração
            </Botao>
          </Cartao>

          {estado.versoes.length > 0 && (
            <Cartao className="p-4">
              <h2 className="text-sm font-extrabold text-gov-blue-dark">Plano de Ação Escolar</h2>
              <p className="mt-1 text-[12px] text-gray-600">
                Com a Declaração v{estado.versoes[estado.versoes.length - 1].versao} emitida, monte as ações da escola com apoio do assistente.
              </p>
              <Link
                href="/gestao/diretor/plano"
                className="mt-3 flex w-full items-center justify-center rounded-lg border-2 border-gov-blue px-4 py-2 text-sm font-bold text-gov-blue hover:bg-gov-blue-lt"
              >
                Ir para o Plano de Ação →
              </Link>
            </Cartao>
          )}

          <Aviso>
            <strong>Seu relato, sua confirmação.</strong> A IA estrutura o texto; o conteúdo só vira registro depois da sua revisão.
          </Aviso>
          <Link href="/gestao/diretor" className="block text-center text-sm font-bold text-gov-blue hover:underline">
            Salvar e voltar ao dashboard
          </Link>
        </aside>
      </div>

      {modal?.tipo === "obstaculo" && barreira && (
        <RevisarObstaculo
          barreira={barreira}
          escola={estado.escola}
          relato={relato}
          proposta={modal.proposta}
          onFechar={() => setModal(null)}
          onRegistrado={(novo) => aoRegistrar(novo, "Obstáculo confirmado. Dado do Censo preservado.")}
        />
      )}
      {modal?.tipo === "divergencia" && barreira && (
        <Divergencia barreira={barreira} onFechar={() => setModal(null)} onRegistrado={(novo) => aoRegistrar(novo, "Divergência registrada. O dado do Censo não foi alterado.")} />
      )}
      {modal?.tipo === "declaracao" && (
        <DeclaracaoConsolidada
          estado={estado}
          onFechar={() => setModal(null)}
          onPublicar={(numero) => setModal({ tipo: "publicar", numero })}
          onRetirar={(numero) => setModal({ tipo: "retirar", numero })}
          onEmitida={async (versao) => {
            setModal({ tipo: "emitida", versao });
            setEstado(await getDeclaracao());
          }}
        />
      )}
      {modal?.tipo === "emitida" && (
        <VersaoEmitida versao={modal.versao} onFechar={() => setModal(null)} onPublicar={() => setModal({ tipo: "publicar", numero: modal.versao.versao })} />
      )}
      {modal?.tipo === "retirar" && (
        <RetirarPublicacao
          numero={modal.numero}
          onFechar={() => setModal(null)}
          onRetirada={async () => {
            setModal(null);
            setAviso(`Declaração v${modal.numero} retirada da página pública. A versão continua guardada.`);
            setEstado(await getDeclaracao());
          }}
        />
      )}
      {modal?.tipo === "publicar" && (
        <PublicarDeclaracao
          numero={modal.numero}
          onFechar={() => setModal(null)}
          onPublicada={async () => {
            setModal(null);
            setAviso(`Declaração v${modal.numero} publicada na página pública da escola.`);
            setEstado(await getDeclaracao());
          }}
        />
      )}
    </div>
  );
}

function Mensagem({ papel, texto }: { papel: "diretor" | "ia"; texto: string }) {
  const daIa = papel === "ia";
  return (
    <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[14px] ${daIa ? "bg-black/[.04] text-ink" : "ml-auto bg-gov-blue text-white"}`}>
      <div className={`text-[10px] font-extrabold uppercase tracking-wider ${daIa ? "text-gov-blue-mid" : "text-white/70"}`}>
        {daIa ? "Assistente de registro" : "Você"}
      </div>
      <p className="mt-0.5 whitespace-pre-line">{texto}</p>
    </div>
  );
}
