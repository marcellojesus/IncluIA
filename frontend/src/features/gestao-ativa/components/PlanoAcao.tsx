"use client";

// Plano de Ação Escolar (requirements/diretor/plano-acao-escolar.md; protótipo v2, view-school-plan).
// A IA sugere ações por barreira a partir da Declaração emitida; o diretor aceita, edita, descarta
// ou escreve as próprias (RN-PAE-01) e envia uma versão à secretaria (RN-PAE-04).
import Link from "next/link";
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import {
  SemAcesso,
  aceitarSugestao,
  ajustarSugestao,
  atualizarBasePlano,
  descartarSugestao,
  editarAcao,
  getPlano,
  incluirAcao,
  removerAcao,
  sugerirAcoes,
} from "../api";
import { ESTADOS_VERSAO_PLANO as ESTADOS_VERSAO, NOMES_EIXOS, POSICOES, dataCurta } from "../rotulos";
import type { AcaoPlano, Apontamento, CamposAcao, EstadoPlano, SugestaoPlano } from "../types";
import { Detalhes, Fontes, SeloOrigem } from "./PartesPlano";
import { PreviaPlano } from "./PreviaPlano";
import { PublicarPlano } from "./PublicarPlano";
import { Aviso, Botao, Cartao, Campo, CampoTexto, Erro, Selo } from "./ui";

const AVISO_ESTIMATIVA = "Estimativa não é orçamento aprovado. Não informe valor sem base; indique a premissa.";

export function PlanoAcao() {
  const [estado, setEstado] = useState<EstadoPlano | null>(null);
  const [semDeclaracao, setSemDeclaracao] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [avisoGuardiao, setAvisoGuardiao] = useState<string | null>(null);
  const [gerando, setGerando] = useState<string | null>(null);
  const [orientacoes, setOrientacoes] = useState<Record<string, string>>({});
  const [formulario, setFormulario] = useState<{ acao?: AcaoPlano; sugestao?: SugestaoPlano; codigo: string } | null>(null);
  const [enviar, setEnviar] = useState(false);
  const [publicar, setPublicar] = useState<number | null>(null);

  useEffect(() => {
    getPlano()
      .then(setEstado)
      .catch((falha) => {
        if (falha instanceof SemAcesso) setErro(falha.message);
        else setSemDeclaracao((falha as Error).message);
      });
  }, []);

  async function executar(acao: () => Promise<EstadoPlano>, mensagem?: string) {
    setErro(null);
    try {
      const novo = await acao();
      setEstado(novo);
      setAvisoGuardiao(novo.avisoGuardiao);
      if (mensagem) setAviso(mensagem);
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  async function sugerir(codigo: string) {
    setGerando(codigo);
    await executar(() => sugerirAcoes(codigo, orientacoes[codigo]), "Sugestões prontas. Revise antes de incluir no plano.");
    setOrientacoes((atual) => ({ ...atual, [codigo]: "" }));
    setGerando(null);
  }

  if (semDeclaracao) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-3xl font-extrabold text-gov-blue-dark">Plano de Ação Escolar</h1>
        <div className="mt-4">
          <Aviso tom="atencao">{semDeclaracao}</Aviso>
        </div>
        <Link href="/gestao/diretor/declaracao" className="mt-4 inline-block text-sm font-bold text-gov-blue hover:underline">
          Ir para a Declaração de Obstáculos →
        </Link>
      </div>
    );
  }
  if (!estado) {
    return erro ? <p role="alert" className="mx-auto mt-10 max-w-md rounded-lg bg-[#fbe9e7] p-4 text-sm text-[#b23838]">{erro}</p> : <p role="status" className="mt-16 text-center text-sm text-gray-500">Carregando o plano…</p>;
  }

  const ultimaVersao = estado.versoes.at(-1);
  const aceita = [...estado.versoes].reverse().find((v) => v.estado === "aceito");
  const publicada = estado.versoes.find((v) => v.publicadaEm && !v.retiradaEm);
  const eixos = [...new Set(estado.barreiras.map((b) => b.eixo))];
  const idsDasAcoes = new Set(estado.acoes.map((a) => a.id));
  const apontada = (codigo: string) => estado.apontamentos.some((p) => p.codigo === codigo);
  const loa = estado.acoes.filter((a) => a.horizonte === "LOA").length;
  const comRelatoTotal = estado.barreiras.filter((b) => b.posicao !== "sem_relato").length;
  const cobertas = estado.barreiras.filter((b) => b.posicao !== "sem_relato" && estado.acoes.some((a) => a.codigo === b.codigo)).length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <nav className="text-xs text-gray-500" aria-label="Trilha">
        <Link href="/gestao/diretor" className="font-bold text-gov-blue hover:underline">← Dashboard da escola</Link> / Plano de Ação Escolar
      </nav>
      <p className="mt-3 text-xs font-extrabold uppercase tracking-wider text-accent">Diretor · {estado.escola}</p>
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Plano de Ação Escolar</h1>
        <Selo tom="teal">Baseado na Declaração v{estado.declaracaoBase}</Selo>
        {ultimaVersao && <Selo tom={ESTADOS_VERSAO[ultimaVersao.estado].tom}>v{ultimaVersao.versao} · {ESTADOS_VERSAO[ultimaVersao.estado].texto}</Selo>}
      </div>
      <p className="mt-2 max-w-3xl text-[15px] text-gray-600">
        Para cada barreira com obstáculo ou divergência, peça sugestões ao assistente, inclua as pertinentes e ajuste o que for preciso. Só as
        ações que você incluir entram no plano enviado à secretaria.
      </p>

      {estado.desatualizado && (
        <div className="mt-4">
          <Aviso tom="atencao">
            O plano usa a Declaração v{estado.declaracaoBase}, mas a escola já emitiu a v{estado.ultimaDeclaracao}.{" "}
            <button className="font-bold text-gov-blue underline" onClick={() => executar(atualizarBasePlano, `O plano passou a usar a Declaração v${estado.ultimaDeclaracao}.`)}>
              Usar a Declaração v{estado.ultimaDeclaracao}
            </button>{" "}
            (as ações ficam; sugestões antigas saem).
          </Aviso>
        </div>
      )}
      {ultimaVersao?.comentario && (
        <div className="mt-4">
          <Aviso tom={ultimaVersao.estado === "aceito" ? "info" : "atencao"}>
            <strong>{ultimaVersao.decididaPor ?? "Secretaria"}, sobre a v{ultimaVersao.versao} ({ESTADOS_VERSAO[ultimaVersao.estado].texto.toLowerCase()}):</strong> {ultimaVersao.comentario}
          </Aviso>
        </div>
      )}
      {aviso && <p role="status" className="mt-4 rounded-lg bg-[#e7f3ec] px-4 py-2 text-[13px] text-[#2f7a55]">{aviso}</p>}
      {avisoGuardiao && (
        <div className="mt-3">
          <Aviso tom="atencao">{avisoGuardiao}</Aviso>
        </div>
      )}
      <div className="mt-4">
        <Erro mensagem={erro} />
      </div>


      <div className="mt-2 grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section aria-labelledby="titulo-barreiras-plano" className="space-y-6">
          <h2 id="titulo-barreiras-plano" className="text-lg font-extrabold text-gov-blue-dark">Barreiras da Declaração v{estado.declaracaoBase}</h2>
          {eixos.map((eixo) => {
            const doEixo = estado.barreiras.filter((b) => b.eixo === eixo);
            const eixoApontado = doEixo.some((b) => apontada(b.codigo));
            return (
              <div key={eixo} className="space-y-3">
                <div className={`flex items-center gap-2 rounded-lg px-3 py-2 ${eixoApontado ? "bg-[#fdece8]" : "bg-gov-blue-lt/60"}`}>
                  <h3 className="text-[13px] font-extrabold uppercase tracking-wider text-gov-blue-dark">
                    Eixo {eixo} · {NOMES_EIXOS[eixo]}
                  </h3>
                  {eixoApontado && <Selo tom="vermelho">Ajuste pedido</Selo>}
                </div>
                {doEixo.map((b) => {
                  const sugestoes = estado.sugestoes.filter((s) => s.codigo === b.codigo);
                  const acoes = estado.acoes.filter((a) => a.codigo === b.codigo);
                  const notasDaBarreira = estado.apontamentos.filter((p) => p.codigo === b.codigo && !(p.acaoId && idsDasAcoes.has(p.acaoId)));
                  const comRelato = b.posicao !== "sem_relato";
                  return (
                    <Cartao key={b.codigo} className={`scroll-mt-4 p-4 ${apontada(b.codigo) ? "ring-2 ring-accent" : ""}`}>
                      <div id={`barreira-${b.codigo}`} className="flex flex-wrap items-start justify-between gap-2">
                        <h4 className="text-[15px] font-extrabold text-ink">{b.barreira}</h4>
                        <div className="flex flex-wrap gap-1">
                          <Selo tom={POSICOES[b.posicao].tom}>{POSICOES[b.posicao].texto}</Selo>
                          {acoes.length > 0 ? (
                            <Selo tom="teal">{acoes.length} no plano</Selo>
                          ) : (
                            comRelato && <Selo tom="neutro">Sem ação no plano</Selo>
                          )}
                        </div>
                      </div>

                      {notasDaBarreira.map((p, i) => (
                        <NotaDaSecretaria key={i} texto={p.texto} sobre="esta barreira" />
                      ))}

                      {b.texto ? (
                        <p className="mt-2 text-[13px] text-gray-700">{b.texto}</p>
                      ) : (
                        <p className="mt-2 text-[13px] text-gray-500">A escola não apresentou relato nesta barreira: fica como lacuna, sem sugestão automática.</p>
                      )}

                      {acoes.length > 0 && (
                        <div className="mt-3">
                          <div className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">No plano</div>
                          <ul className="mt-1.5 space-y-2">
                            {acoes.map((a) => (
                              <AcaoCompacta
                                key={a.id}
                                acao={a}
                                citacoes={estado.fontes}
                                nota={estado.apontamentos.find((p) => p.acaoId === a.id)}
                                onEditar={() => setFormulario({ acao: a, codigo: a.codigo })}
                                onRemover={() => executar(() => removerAcao(a.id))}
                              />
                            ))}
                          </ul>
                        </div>
                      )}

                      <div className="mt-4 border-t border-black/5 pt-3">
                        {comRelato && (
                          <>
                            <label htmlFor={`orientacao-${b.codigo}`} className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">
                              Gerar ações com o assistente
                            </label>
                            <input
                              id={`orientacao-${b.codigo}`}
                              value={orientacoes[b.codigo] ?? ""}
                              onChange={(e) => setOrientacoes((atual) => ({ ...atual, [b.codigo]: e.target.value }))}
                              placeholder="Orientação opcional (ex.: priorizar ações sem custo)"
                              aria-describedby={`ajuda-orientacao-${b.codigo}`}
                              maxLength={1000}
                              className="mt-1.5 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-[13px] outline-none focus:border-gov-blue"
                            />
                            <p id={`ajuda-orientacao-${b.codigo}`} className="mt-1 text-[11px] text-gray-500">
                              Vai para um assistente de IA externo. Não identifique estudantes nem profissionais; descreva a necessidade da escola.
                            </p>
                          </>
                        )}
                        <div className="mt-2 flex flex-wrap gap-2">
                          {comRelato && (
                            <Botao onClick={() => sugerir(b.codigo)} disabled={gerando !== null}>
                              {gerando === b.codigo
                                ? "Pensando…"
                                : orientacoes[b.codigo]?.trim()
                                  ? "Pedir proposta com esta orientação"
                                  : sugestoes.length
                                    ? "Pedir outra proposta"
                                    : "Sugerir ações"}
                            </Botao>
                          )}
                          <Botao variante="discreto" onClick={() => setFormulario({ codigo: b.codigo })}>Escrever ação própria</Botao>
                        </div>
                      </div>

                      {sugestoes.map((s) => (
                        <CartaoSugestao
                          key={s.id}
                          sugestao={s}
                          citacoes={estado.fontes}
                          ocupado={gerando !== null}
                          onIncluir={() => executar(() => aceitarSugestao(s.id), "Ação incluída no plano. Você pode editá-la.")}
                          onEditar={() => setFormulario({ sugestao: s, codigo: s.codigo })}
                          onAjustar={async (pedido) => {
                            setGerando(s.id);
                            await executar(() => ajustarSugestao(s.id, pedido), "O assistente reescreveu a sugestão. Revise antes de incluir.");
                            setGerando(null);
                          }}
                          ajustando={gerando === s.id}
                          onDescartar={() => executar(() => descartarSugestao(s.id))}
                        />
                      ))}
                    </Cartao>
                  );
                })}
              </div>
            );
          })}
        </section>

        <aside aria-labelledby="titulo-resumo" className="space-y-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:self-start lg:overflow-y-auto">
          <Cartao className="p-4">
            <h2 id="titulo-resumo" className="text-lg font-extrabold text-gov-blue-dark">Resumo do plano</h2>
            <div className="mt-2 grid grid-cols-3 gap-2 text-center">
              {[
                [estado.acoes.length, "ações"],
                [loa, "LOA"],
                [estado.acoes.length - loa, "PPA"],
              ].map(([valor, rotulo]) => (
                <div key={rotulo} className="rounded-lg bg-gov-blue-lt/60 py-2">
                  <div className="text-xl font-extrabold text-gov-blue-dark">{valor}</div>
                  <div className="text-[11px] text-gray-600">{rotulo}</div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[12px] text-gray-600">
              {cobertas} de {comRelatoTotal} barreiras com relato têm ação no plano.
            </p>
            <ul className="mt-2 space-y-1" aria-label="Barreiras">
              {estado.barreiras.map((b) => {
                const n = estado.acoes.filter((a) => a.codigo === b.codigo).length;
                const status = apontada(b.codigo) ? "ajuste" : n > 0 ? "ok" : b.posicao === "sem_relato" ? "lacuna" : "falta";
                const marca = { ajuste: ["!", "bg-accent text-white"], ok: ["✓", "bg-[#2f9e6b] text-white"], falta: ["•", "bg-gray-200 text-gray-600"], lacuna: ["–", "bg-gray-100 text-gray-400"] }[status];
                return (
                  <li key={b.codigo}>
                    <a href={`#barreira-${b.codigo}`} className="flex items-center gap-2 rounded-md px-1.5 py-1 text-[12px] hover:bg-black/[.03]">
                      <span aria-hidden className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-extrabold ${marca[1]}`}>
                        {marca[0]}
                      </span>
                      <span className={`flex-1 ${status === "ajuste" ? "font-bold text-accent-dark" : "text-ink"}`}>{b.barreira}</span>
                      <span className="sr-only">
                        {status === "ajuste" ? "ajuste pedido pela secretaria" : status === "ok" ? `${n} ações` : status === "falta" ? "sem ação" : "sem relato"}
                      </span>
                      {n > 0 && <span aria-hidden className="text-[11px] text-gray-500">{n}</span>}
                    </a>
                  </li>
                );
              })}
            </ul>
            <Botao variante="coral" className="mt-4 w-full" disabled={!estado.podeSubmeter} onClick={() => setEnviar(true)}>
              Revisar e enviar à secretaria
            </Botao>
            {estado.motivo && <p className="mt-1 text-[12px] text-gray-500">{estado.motivo}</p>}
          </Cartao>

          {aceita && (
            <Cartao className="p-4">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-sm font-extrabold text-gov-blue-dark">Página pública</h2>
                <Selo tom={publicada ? "verde" : "neutro"}>{publicada ? `v${publicada.versao} publicada` : "Não publicado"}</Selo>
              </div>
              <p className="mt-1 text-[12px] text-gray-600">
                {publicada && publicada.versao === aceita.versao
                  ? `Publicado em ${dataCurta(publicada.publicadaEm)}, junto com a Declaração.`
                  : `A v${aceita.versao} foi aceita pela secretaria. Publique para dar transparência à comunidade.`}
              </p>
              <Botao
                variante={publicada && publicada.versao === aceita.versao ? "contorno" : "coral"}
                className="mt-3 w-full"
                onClick={() => setPublicar(aceita.versao)}
              >
                {publicada && publicada.versao === aceita.versao ? "Ver ou retirar publicação" : `Publicar a v${aceita.versao}`}
              </Botao>
            </Cartao>
          )}

          {estado.versoes.length > 0 && (
            <Cartao className="p-4">
              <h2 className="text-sm font-extrabold text-gov-blue-dark">Versões enviadas</h2>
              <ul className="mt-2 space-y-2 text-[12px]">
                {[...estado.versoes].reverse().map((v) => (
                  <li key={v.versao} className="flex items-center justify-between gap-2">
                    <span>v{v.versao} · {dataCurta(v.submetidaEm)}</span>
                    <Selo tom={ESTADOS_VERSAO[v.estado].tom}>{ESTADOS_VERSAO[v.estado].texto}</Selo>
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
          <Aviso>
            <strong>A IA sugere, você decide.</strong> Custos e prazos são estimativas com premissas; incluir uma ação no plano não garante orçamento.
          </Aviso>
        </aside>
      </div>

      {formulario && (
        <FormularioAcao
          barreiras={estado.barreiras}
          inicial={formulario.acao ?? formulario.sugestao}
          titulo={formulario.acao ? "Editar ação" : formulario.sugestao ? "Editar sugestão e incluir" : "Nova ação"}
          rotuloSalvar={formulario.sugestao ? "Incluir no plano" : "Salvar ação"}
          codigo={formulario.codigo}
          onFechar={() => setFormulario(null)}
          onSalvar={async (campos) => {
            const { acao, sugestao } = formulario;
            setErro(null);
            const novo = acao ? await editarAcao(acao.id, campos) : sugestao ? await aceitarSugestao(sugestao.id, campos) : await incluirAcao(campos);
            setEstado(novo);
            setAvisoGuardiao(novo.avisoGuardiao);
            setFormulario(null);
            setAviso(acao ? "Ação atualizada." : "Ação incluída no plano.");
          }}
        />
      )}
      {publicar !== null && (
        <PublicarPlano numero={publicar} onFechar={() => setPublicar(null)} onMudou={() => getPlano().then(setEstado)} />
      )}
      {enviar && (
        <PreviaPlano
          estado={estado}
          onFechar={() => setEnviar(false)}
          onEnviado={async (versao) => {
            setEnviar(false);
            setAviso(`Plano v${versao} enviado à secretaria. Ele fica aguardando análise.`);
            setEstado(await getPlano());
          }}
        />
      )}
    </div>
  );
}

function NotaDaSecretaria({ texto, sobre }: { texto: string | null; sobre: string }) {
  return (
    <p className="mt-2 rounded-md border-l-4 border-accent bg-[#fdece8] px-3 py-2 text-[13px] text-ink">
      <strong className="text-accent-dark">Ajuste pedido pela secretaria</strong> {texto ? `sobre ${sobre}: ${texto}` : `em ${sobre}.`}
    </p>
  );
}

// Uma ação do plano dentro do cartão da barreira: o essencial numa linha, o resto em "Detalhes".
function AcaoCompacta({
  acao,
  citacoes,
  nota,
  onEditar,
  onRemover,
}: {
  acao: AcaoPlano;
  citacoes: Record<string, string>;
  nota?: Apontamento;
  onEditar: () => void;
  onRemover: () => void;
}) {
  const resumo = [acao.responsavel, acao.prazo, acao.horizonte, acao.custoEstimado].filter(Boolean).join(" · ");
  return (
    <li className={`rounded-lg border p-3 ${nota ? "border-accent bg-[#fffaf8] ring-1 ring-accent" : "border-black/10 bg-white"}`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="flex-1 text-[13px] font-bold text-ink">{acao.acao}</p>
        <SeloOrigem acao={acao} />
      </div>
      {resumo && <p className="mt-1 text-[12px] text-gray-600">{resumo}</p>}
      {nota && <NotaDaSecretaria texto={nota.texto} sobre="esta ação" />}
      <details className="mt-1.5 text-[12px]">
        <summary className="cursor-pointer font-bold text-gray-500 hover:text-gov-blue">Detalhes</summary>
        {acao.relacao && <p className="mt-1 text-gray-700">{acao.relacao}</p>}
        <Detalhes campos={acao} />
        <Fontes ids={acao.fontes} citacoes={citacoes} />
      </details>
      <div className="mt-2 flex gap-3">
        <button onClick={onEditar} className="text-[12px] font-bold text-gov-blue hover:underline">Editar</button>
        <button onClick={onRemover} className="text-[12px] font-bold text-gov-red hover:underline">Remover</button>
      </div>
    </li>
  );
}

const PEDIDOS_RAPIDOS =["Reduzir o prazo", "Ação sem custo para a escola", "Detalhar os passos", "Simplificar a ação", "Trocar o responsável"];

function CartaoSugestao({
  sugestao,
  citacoes,
  ocupado,
  ajustando,
  onIncluir,
  onEditar,
  onAjustar,
  onDescartar,
}: {
  sugestao: SugestaoPlano;
  citacoes: Record<string, string>;
  ocupado: boolean;
  ajustando: boolean;
  onIncluir: () => void;
  onEditar: () => void;
  onAjustar: (pedido: string) => Promise<void>;
  onDescartar: () => void;
}) {
  const [ajuste, setAjuste] = useState<string | null>(null);
  const idPedido = `ajuste-${sugestao.id}`;

  return (
    <div className="mt-3 rounded-lg border border-gov-blue/30 bg-gov-blue-lt p-3" aria-busy={ajustando}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-gov-blue-mid">Sugestão do assistente</span>
        {sugestao.ajustada && <Selo tom="teal">Ajustada a seu pedido</Selo>}
      </div>
      <p className="mt-1 text-[14px] font-bold text-ink">{sugestao.acao}</p>
      {sugestao.relacao && <p className="mt-1 text-[13px] text-gray-700">{sugestao.relacao}</p>}
      <Detalhes campos={sugestao} />
      <Fontes ids={sugestao.fontes} citacoes={citacoes} />
      {sugestao.incertezas && <p className="mt-1 text-[12px] text-gray-600"><strong>Incertezas:</strong> {sugestao.incertezas}</p>}
      {sugestao.lacunas.length > 0 && <p className="mt-1 text-[12px] text-gray-600"><strong>Lacunas:</strong> {sugestao.lacunas.join(" ")}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        <Botao className="px-3 py-1.5 text-[12px]" onClick={onIncluir} disabled={ocupado}>Incluir no plano</Botao>
        <Botao variante="contorno" className="px-3 py-1.5 text-[12px]" onClick={() => setAjuste(ajuste === null ? "" : null)} disabled={ocupado} aria-expanded={ajuste !== null} aria-controls={idPedido}>
          Ajustar com a IA
        </Botao>
        <Botao variante="contorno" className="px-3 py-1.5 text-[12px]" onClick={onEditar} disabled={ocupado}>Editar e incluir</Botao>
        <Botao variante="discreto" className="px-3 py-1.5 text-[12px]" onClick={onDescartar} disabled={ocupado}>Descartar</Botao>
      </div>

      {ajuste !== null && (
        <form
          id={idPedido}
          className="mt-3 rounded-lg border border-black/10 bg-paper p-3"
          onSubmit={async (e) => {
            e.preventDefault();
            await onAjustar(ajuste);
          }}
        >
          <label htmlFor={`${idPedido}-texto`} className="text-[12px] font-bold text-gray-700">O que o assistente deve mudar nesta sugestão?</label>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {PEDIDOS_RAPIDOS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setAjuste(p)}
                className={`rounded-full border px-2.5 py-1 text-[11px] font-bold ${ajuste === p ? "border-gov-blue bg-gov-blue-lt text-gov-blue" : "border-black/10 text-gray-600 hover:border-gov-blue"}`}
              >
                {p}
              </button>
            ))}
          </div>
          <textarea
            id={`${idPedido}-texto`}
            rows={2}
            maxLength={1000}
            value={ajuste}
            onChange={(e) => setAjuste(e.target.value)}
            placeholder="Ex.: a escola já tem sala de recursos; foque na contratação do professor de AEE."
            aria-describedby={`${idPedido}-ajuda`}
            className="mt-2 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-[13px] outline-none focus:border-gov-blue"
          />
          <p id={`${idPedido}-ajuda`} className="text-[11px] text-gray-500">
            Vai para um assistente de IA externo. Não identifique estudantes nem profissionais.
          </p>
          <div className="mt-2 flex justify-end gap-2">
            <Botao type="button" variante="discreto" className="px-3 py-1.5 text-[12px]" onClick={() => setAjuste(null)}>Cancelar</Botao>
            <Botao type="submit" className="px-3 py-1.5 text-[12px]" disabled={ocupado || ajuste.trim().length < 3}>
              {ajustando ? "Reescrevendo…" : "Pedir ajuste"}
            </Botao>
          </div>
        </form>
      )}
    </div>
  );
}

function FormularioAcao({
  barreiras,
  inicial,
  titulo,
  rotuloSalvar,
  codigo,
  onFechar,
  onSalvar,
}: {
  barreiras: EstadoPlano["barreiras"];
  inicial?: CamposAcao;
  titulo: string;
  rotuloSalvar: string;
  codigo: string;
  onFechar: () => void;
  onSalvar: (campos: CamposAcao) => Promise<void>;
}) {
  const [campos, setCampos] = useState<CamposAcao>({
    codigo: inicial?.codigo ?? codigo,
    acao: inicial?.acao ?? "",
    relacao: inicial?.relacao ?? "",
    responsavel: inicial?.responsavel ?? "",
    prazo: inicial?.prazo ?? "",
    horizonte: inicial?.horizonte ?? "LOA",
    custoEstimado: inicial?.custoEstimado ?? "",
    premissas: inicial?.premissas ?? "",
  });
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const mudar = (campo: keyof CamposAcao) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setCampos((atual) => ({ ...atual, [campo]: e.target.value }));

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await onSalvar(campos);
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo={titulo} subtitulo="Plano de Ação Escolar" onFechar={onFechar}>
      <form onSubmit={salvar}>
        <div className="mb-3">
          <label htmlFor="acao-barreira" className="mb-1 block text-xs font-bold text-gray-700">Barreira</label>
          <select id="acao-barreira" value={campos.codigo} onChange={mudar("codigo")} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm">
            {barreiras.map((b) => (
              <option key={b.codigo} value={b.codigo}>{b.barreira}</option>
            ))}
          </select>
        </div>
        <Aviso>Não inclua nomes nem dados de estudantes ou profissionais. A ação vai à secretaria como foi escrita.</Aviso>
        <div className="mt-3" />
        <CampoTexto id="acao-texto" rotulo="Ação" rows={2} value={campos.acao} onChange={mudar("acao")} required />
        <CampoTexto id="acao-relacao" rotulo="Como responde ao obstáculo" rows={2} value={campos.relacao ?? ""} onChange={mudar("relacao")} />
        <div className="grid gap-x-3 sm:grid-cols-2">
          <Campo
            id="acao-responsavel"
            rotulo="Responsável (cargo ou órgão)"
            value={campos.responsavel ?? ""}
            onChange={mudar("responsavel")}
            placeholder="Ex.: direção da escola"
            list="responsaveis-sugeridos"
            ajuda="Cargo ou órgão, nunca o nome da pessoa."
          />
          <datalist id="responsaveis-sugeridos">
            {["direção da escola", "coordenação pedagógica", "professor(a) do AEE", "secretaria municipal de educação", "conselho escolar"].map((r) => (
              <option key={r} value={r} />
            ))}
          </datalist>
          <Campo id="acao-prazo" rotulo="Prazo" value={campos.prazo ?? ""} onChange={mudar("prazo")} placeholder="Ex.: até 6 meses" />
        </div>
        <fieldset className="mb-3">
          <legend className="mb-1 text-xs font-bold text-gray-700">Horizonte</legend>
          <div className="flex gap-4 text-[13px]">
            {(["LOA", "PPA"] as const).map((h) => (
              <label key={h} className="flex items-center gap-1.5">
                <input type="radio" name="horizonte" value={h} checked={campos.horizonte === h} onChange={mudar("horizonte")} className="accent-[#0e7c6b]" />
                {h === "LOA" ? "LOA · exercício corrente" : "PPA · até quatro anos"}
              </label>
            ))}
          </div>
        </fieldset>
        <Campo id="acao-custo" rotulo="Custo estimado" value={campos.custoEstimado ?? ""} onChange={mudar("custoEstimado")} ajuda={AVISO_ESTIMATIVA} />
        <CampoTexto id="acao-premissas" rotulo="Premissas" rows={2} value={campos.premissas ?? ""} onChange={mudar("premissas")} ajuda="Não inclua nomes nem dados de estudantes." />
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>Cancelar</Botao>
          <Botao type="submit" disabled={enviando || campos.acao.trim().length < 10}>{enviando ? "Salvando…" : rotuloSalvar}</Botao>
        </div>
      </form>
    </Modal>
  );
}

