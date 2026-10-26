"use client";

// Fila e revisão de Planos de Ação pelo secretário (requirements/secretario/fila-revisao-planos.md).
// Só versões enviadas aparecem (RN-SFR-02); a decisão vale para uma versão exata (RN-SFR-03);
// aceitar não é financiamento nem execução (RN-SFR-05).
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { decidirPlano, getFilaPlanos, getRevisaoPlano, getVersaoDaRede } from "../api";
import { ESTADOS_VERSAO_PLANO, NOMES_EIXOS, POSICOES, dataCurta } from "../rotulos";
import type { DecisaoPlano, FilaPlanos as Fila, RevisaoPlano, VersaoDeclaracao } from "../types";
import { ListaPorEixo } from "./ModaisDeclaracao";
import { Detalhes, Fontes, SeloOrigem } from "./PartesPlano";
import { Aviso, Botao, Cartao, CampoTexto, Erro, Selo } from "./ui";

function diasDeEspera(iso: string) {
  const dias = Math.floor((Date.now() - new Date(iso).getTime()) / (24 * 60 * 60 * 1000));
  return dias <= 0 ? "aguarda desde hoje" : `aguarda há ${dias} ${dias === 1 ? "dia" : "dias"}`;
}

export function FilaPlanos({ onMudou }: { onMudou?: () => void } = {}) {
  const [fila, setFila] = useState<Fila | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aberta, setAberta] = useState<RevisaoPlano | null>(null);

  const carregar = () => getFilaPlanos().then(setFila).catch((falha) => setErro((falha as Error).message));
  useEffect(() => {
    carregar();
  }, []);

  async function abrir(coEntidade: number, versao: number) {
    setErro(null);
    try {
      setAberta(await getRevisaoPlano(coEntidade, versao));
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  if (aberta) {
    return (
      <Revisao
        revisao={aberta}
        onVoltar={() => {
          setAberta(null);
          carregar();
        }}
        onAbrirVersao={(n) => abrir(aberta.coEntidade, n)}
        onDecidido={(r) => {
          setAberta(r);
          onMudou?.();
        }}
      />
    );
  }
  if (!fila) return erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Carregando…</p>;

  const contar = (estado: string) => fila.planos.filter((p) => p.estado === estado).length;

  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-4">
        {(["aguardando_analise", "ajustes_solicitados", "aceito", "reprovado"] as const).map((estado) => (
          <Cartao key={estado} className="p-4">
            <div className="text-[12px] text-gray-500">{ESTADOS_VERSAO_PLANO[estado].texto}</div>
            <div className="text-2xl font-extrabold text-gov-blue-dark">{contar(estado)}</div>
          </Cartao>
        ))}
      </div>
      <div className="mt-3">
        <Aviso>
          A fila mostra só escolas que enviaram um Plano de Ação. Escola fora da fila não é escola sem necessidade. Aceitar um plano
          significa que ele pode servir de base ao planejamento municipal; não cria dotação, empenho nem contrato.
        </Aviso>
      </div>
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>

      <Cartao className="mt-1 overflow-x-auto">
        {fila.planos.length === 0 ? (
          <p className="p-5 text-sm text-gray-600">Nenhuma escola da rede enviou Plano de Ação ainda.</p>
        ) : (
          <table className="w-full min-w-[820px] text-left text-[13px]">
            <thead className="border-b border-black/5 text-[11px] uppercase tracking-wider text-gray-500">
              <tr>
                <th scope="col" className="px-4 py-2.5">Escola</th>
                <th scope="col" className="px-4 py-2.5">Versão</th>
                <th scope="col" className="px-4 py-2.5">Ações</th>
                <th scope="col" className="px-4 py-2.5">Base</th>
                <th scope="col" className="px-4 py-2.5">Estado</th>
                <th scope="col" className="px-4 py-2.5"><span className="sr-only">Abrir</span></th>
              </tr>
            </thead>
            <tbody>
              {fila.planos.map((p) => (
                <tr key={p.coEntidade} className={`border-b border-black/5 last:border-0 ${p.estado === "aguardando_analise" ? "bg-[#fdece8] shadow-[inset_4px_0_0_#e5533c]" : ""}`}>
                  <td className="px-4 py-3 align-top">
                    <div className="font-bold text-ink">{p.escola}</div>
                    <div className="text-[12px] text-gray-500">INEP {p.coEntidade}</div>
                  </td>
                  <td className="px-4 py-3 align-top">
                    v{p.versao}
                    <div className="text-[12px] text-gray-500">enviada em {dataCurta(p.submetidaEm)}</div>
                    {p.estado === "aguardando_analise" && <div className="text-[12px] font-bold text-accent-dark">{diasDeEspera(p.submetidaEm)}</div>}
                  </td>
                  <td className="px-4 py-3 align-top text-[12px] text-gray-700">
                    {p.acoes} · {p.loa} LOA · {p.ppa} PPA
                  </td>
                  <td className="px-4 py-3 align-top text-[12px]">
                    Declaração v{p.declaracaoVersao}
                    {p.ultimaDeclaracao > p.declaracaoVersao && <div className="font-bold text-[#8a5a00]">escola já emitiu a v{p.ultimaDeclaracao}</div>}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <Selo tom={ESTADOS_VERSAO_PLANO[p.estado].tom}>{ESTADOS_VERSAO_PLANO[p.estado].texto}</Selo>
                  </td>
                  <td className="px-4 py-3 text-right align-top">
                    <button
                      onClick={() => abrir(p.coEntidade, p.versao)}
                      className={p.estado === "aguardando_analise" ? "rounded-lg bg-accent px-4 py-2 text-[13px] font-extrabold text-white shadow-sm hover:bg-accent-dark" : "rounded-lg px-3 py-1.5 text-[12px] font-bold text-gov-blue hover:bg-gov-blue-lt"}
                    >
                      {p.estado === "aguardando_analise" ? "Analisar" : "Ver plano"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Cartao>
    </div>
  );
}

type Marcas = Record<string, { codigo: string; itemId?: string; texto: string }>;

function NotaRegistrada({ texto }: { texto: string | null }) {
  return (
    <p className="mt-2 rounded-md border-l-4 border-accent bg-[#fdece8] px-3 py-1.5 text-[12px] text-ink">
      <strong className="text-accent-dark">Ajuste apontado</strong>
      {texto ? `: ${texto}` : ""}
    </p>
  );
}

// Caixa de marcação de uma barreira (sem itemId) ou ação (com itemId), com nota curta opcional.
function MarcarAjuste({
  chave,
  codigo,
  itemId,
  rotulo,
  marcas,
  setMarcas,
}: {
  chave: string;
  codigo: string;
  itemId?: string;
  rotulo: string;
  marcas: Marcas;
  setMarcas: React.Dispatch<React.SetStateAction<Marcas>>;
}) {
  const marcada = marcas[chave];
  return (
    <div className="mt-2">
      <label className="inline-flex cursor-pointer items-center gap-2 text-[12px] font-bold text-accent-dark">
        <input
          type="checkbox"
          className="h-4 w-4 accent-[#e5533c]"
          checked={!!marcada}
          onChange={(e) =>
            setMarcas((atual) => {
              const novo = { ...atual };
              if (e.target.checked) novo[chave] = { codigo, itemId, texto: "" };
              else delete novo[chave];
              return novo;
            })
          }
        />
        {rotulo} para ajuste
      </label>
      {marcada && (
        <input
          aria-label={`Nota de ajuste: ${rotulo.toLowerCase()}`}
          value={marcada.texto}
          maxLength={500}
          onChange={(e) => setMarcas((atual) => ({ ...atual, [chave]: { ...atual[chave], texto: e.target.value } }))}
          placeholder="O que a escola deve rever (opcional)"
          className="mt-1.5 w-full rounded-lg border border-accent/50 bg-white px-3 py-1.5 text-[13px] outline-none focus:border-accent"
        />
      )}
    </div>
  );
}

const OPCOES:{ valor: DecisaoPlano; rotulo: string; ajuda: string }[] = [
  { valor: "aceitar", rotulo: "Aceitar", ajuda: "A versão passa a servir de base ao planejamento municipal. Não é aprovação de orçamento." },
  { valor: "ajustes", rotulo: "Solicitar ajustes", ajuda: "A escola revisa e envia nova versão. Escreva uma orientação acionável." },
  { valor: "reprovar", rotulo: "Reprovar", ajuda: "Escreva o motivo. A escola pode enviar nova versão depois." },
];

function Revisao({
  revisao,
  onVoltar,
  onAbrirVersao,
  onDecidido,
}: {
  revisao: RevisaoPlano;
  onVoltar: () => void;
  onAbrirVersao: (versao: number) => void;
  onDecidido: (revisao: RevisaoPlano) => void;
}) {
  const v = revisao.versao;
  const [decisao, setDecisao] = useState<DecisaoPlano | null>(null);
  const [comentario, setComentario] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [declaracao, setDeclaracao] = useState<VersaoDeclaracao | null>(null);
  const [marcas, setMarcas] = useState<Marcas>({});
  const podeDecidir = v.versao === revisao.versaoAtual && v.estado === "aguardando_analise";
  const exigeComentario = decisao === "ajustes" || decisao === "reprovar";
  const podeMarcar = podeDecidir && exigeComentario;

  async function decidir() {
    if (!decisao) return;
    setErro(null);
    setEnviando(true);
    try {
      const apontamentos = exigeComentario
        ? Object.values(marcas).map((m) => ({ codigo: m.codigo, itemId: m.itemId, texto: m.texto.trim() || undefined }))
        : [];
      onDecidido(await decidirPlano(revisao.coEntidade, v.versao, decisao, comentario, apontamentos));
      setDecisao(null);
      setComentario("");
      setMarcas({});
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function lerDeclaracao() {
    setErro(null);
    try {
      setDeclaracao(await getVersaoDaRede(revisao.coEntidade, v.declaracaoVersao));
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  return (
    <div>
      <button onClick={onVoltar} className="text-xs font-bold text-gov-blue hover:underline">← Voltar à fila</button>
      <div className="mt-2 flex flex-wrap items-baseline gap-3">
        <h2 className="text-2xl font-extrabold text-gov-blue-dark">{v.escola}</h2>
        <Selo tom={ESTADOS_VERSAO_PLANO[v.estado].tom}>v{v.versao} · {ESTADOS_VERSAO_PLANO[v.estado].texto}</Selo>
        {v.versao !== revisao.versaoAtual && <Selo tom="neutro">Substituída pela v{revisao.versaoAtual}</Selo>}
      </div>
      <p className="mt-1 text-[13px] text-gray-600">
        Enviada em {dataCurta(v.submetidaEm)} · baseada na Declaração v{v.declaracaoVersao} ·{" "}
        <button onClick={lerDeclaracao} className="font-bold text-gov-blue hover:underline">Ler a Declaração v{v.declaracaoVersao}</button>
      </p>
      {revisao.ultimaDeclaracao > v.declaracaoVersao && (
        <div className="mt-3">
          <Aviso tom="atencao">
            Depois do envio, a escola emitiu a Declaração v{revisao.ultimaDeclaracao}. Este plano usa a v{v.declaracaoVersao}.
          </Aviso>
        </div>
      )}
      {revisao.avisoGuardiao && (
        <div className="mt-3">
          <Aviso tom="atencao">{revisao.avisoGuardiao}</Aviso>
        </div>
      )}
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>

      <div className="mt-2 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section aria-label="Plano por barreira" className="space-y-3">
          {podeMarcar && (
            <Aviso>
              Marque as barreiras e ações que a escola precisa rever. Elas aparecem destacadas para o diretor, com a sua nota.
            </Aviso>
          )}
          {revisao.barreiras.map((b) => {
            const itens = v.itens.filter((i) => i.codigo === b.codigo);
            if (!itens.length && b.posicao === "sem_relato") return null;
            const chaveBarreira = `b:${b.codigo}`;
            const notaBarreira = v.apontamentos.find((a) => a.codigo === b.codigo && !a.itemId);
            const destacada = !!marcas[chaveBarreira] || !!notaBarreira;
            return (
              <Cartao key={b.codigo} className={`p-4 ${destacada ? "ring-2 ring-accent" : ""}`}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="text-[11px] text-gray-500">Eixo {b.eixo} · {NOMES_EIXOS[b.eixo]}</div>
                    <h3 className="text-[15px] font-extrabold text-ink">{b.barreira}</h3>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    <Selo tom={POSICOES[b.posicao].tom}>{POSICOES[b.posicao].texto}</Selo>
                    {!itens.length && <Selo tom="neutro">Sem ação</Selo>}
                  </div>
                </div>
                {b.resumo && <p className="mt-1 text-[12px] text-gray-600">Relato: {b.resumo}</p>}
                {notaBarreira && <NotaRegistrada texto={notaBarreira.texto} />}
                {podeMarcar && <MarcarAjuste chave={chaveBarreira} rotulo="Marcar esta barreira" codigo={b.codigo} marcas={marcas} setMarcas={setMarcas} />}

                {itens.length > 0 && (
                  <ol className="mt-3 space-y-2">
                    {itens.map((i) => {
                      const nota = v.apontamentos.find((a) => a.itemId === i.id);
                      return (
                        <li key={i.id} className={`rounded-lg border p-3 ${marcas[i.id] || nota ? "border-accent ring-1 ring-accent" : "border-black/10"}`}>
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <p className="flex-1 text-[14px] font-bold text-ink">{i.acao}</p>
                            <div className="flex gap-1">
                              <Selo tom="neutro">{i.horizonte}</Selo>
                              <SeloOrigem acao={i} />
                            </div>
                          </div>
                          {i.relacao && <p className="mt-1 text-[13px] text-gray-700">{i.relacao}</p>}
                          <Detalhes campos={i} />
                          <Fontes ids={i.fontes} citacoes={v.fontes} />
                          {nota && <NotaRegistrada texto={nota.texto} />}
                          {podeMarcar && <MarcarAjuste chave={i.id} itemId={i.id} rotulo="Marcar esta ação" codigo={i.codigo} marcas={marcas} setMarcas={setMarcas} />}
                        </li>
                      );
                    })}
                  </ol>
                )}
              </Cartao>
            );
          })}
        </section>


        <aside className="space-y-4">
          {podeDecidir ? (
            <Cartao className="p-4">
              <h3 className="text-lg font-extrabold text-gov-blue-dark">Decisão sobre a v{v.versao}</h3>
              <fieldset className="mt-2 space-y-2">
                <legend className="sr-only">Decisão</legend>
                {OPCOES.map((o) => (
                  <label key={o.valor} className={`block cursor-pointer rounded-lg border p-3 ${decisao === o.valor ? "border-gov-blue bg-gov-blue-lt" : "border-black/10"}`}>
                    <span className="flex items-center gap-2 text-[14px] font-bold text-ink">
                      <input type="radio" name="decisao" value={o.valor} checked={decisao === o.valor} onChange={() => setDecisao(o.valor)} className="accent-[#0e7c6b]" />
                      {o.rotulo}
                    </span>
                    <span className="mt-1 block text-[12px] text-gray-600">{o.ajuda}</span>
                  </label>
                ))}
              </fieldset>
              {decisao && (
                <div className="mt-3">
                  <CampoTexto
                    id="comentario-decisao"
                    rotulo={decisao === "ajustes" ? "Orientação de ajuste" : decisao === "reprovar" ? "Motivo da reprovação" : "Comentário (opcional)"}
                    rows={4}
                    maxLength={2000}
                    value={comentario}
                    onChange={(e) => setComentario(e.target.value)}
                    required={exigeComentario}
                    ajuda="Fica visível ao diretor da escola, com o seu nome. Não inclua dados de estudantes ou profissionais."
                  />
                </div>
              )}
              <Botao className="mt-1 w-full" disabled={!decisao || enviando || (exigeComentario && comentario.trim().length < 10)} onClick={decidir}>
                {enviando ? "Registrando…" : "Registrar decisão"}
              </Botao>
            </Cartao>
          ) : (
            v.decididaEm && (
              <Cartao className="p-4">
                <h3 className="text-sm font-extrabold text-gov-blue-dark">Decisão registrada</h3>
                <p className="mt-1 text-[13px] text-gray-700">
                  {ESTADOS_VERSAO_PLANO[v.estado].texto} em {dataCurta(v.decididaEm)}
                  {v.decididaPor ? ` por ${v.decididaPor}` : ""}.
                </p>
                {v.comentario && <p className="mt-2 text-[13px] text-ink">{v.comentario}</p>}
              </Cartao>
            )
          )}

          <Cartao className="p-4">
            <h3 className="text-sm font-extrabold text-gov-blue-dark">Histórico de versões</h3>
            <ul className="mt-2 space-y-2 text-[13px]">
              {[...revisao.historico].reverse().map((h) => (
                <li key={h.versao}>
                  <div className="flex items-center justify-between gap-2">
                    <button
                      onClick={() => onAbrirVersao(h.versao)}
                      disabled={h.versao === v.versao}
                      className="font-bold text-gov-blue hover:underline disabled:text-ink disabled:no-underline"
                    >
                      v{h.versao} · {dataCurta(h.submetidaEm)}
                    </button>
                    <Selo tom={ESTADOS_VERSAO_PLANO[h.estado].tom}>{ESTADOS_VERSAO_PLANO[h.estado].texto}</Selo>
                  </div>
                  {h.comentario && <p className="mt-0.5 text-[12px] text-gray-600">{h.comentario}</p>}
                </li>
              ))}
            </ul>
          </Cartao>
        </aside>
      </div>

      {declaracao && (
        <Modal titulo={`Declaração v${declaracao.versao}`} subtitulo={`${declaracao.escola} · emitida em ${dataCurta(declaracao.emitidaEm)}`} onFechar={() => setDeclaracao(null)}>
          <div className="max-h-[60vh] overflow-y-auto pr-1">
            <ListaPorEixo
              itens={declaracao.itens.map((i) => ({ codigo: i.codigo, eixo: i.eixo, nome: i.barreira, dadoCenso: i.dadoCenso, posicao: i.posicao, texto: i.texto }))}
            />
          </div>
        </Modal>
      )}
    </div>
  );
}
