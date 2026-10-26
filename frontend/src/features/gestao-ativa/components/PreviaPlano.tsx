"use client";

// Prévia do Plano de Ação antes do envio (PAE-RF-06): sumário executivo calculado do próprio
// rascunho, sem IA, e o plano como a secretaria vai recebê-lo. Aponta pendências para o diretor
// revisar (barreira sem ação, ação sem responsável ou prazo, marcador do Guardião no texto).
import { useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { submeterPlano } from "../api";
import { NOMES_EIXOS, POSICOES } from "../rotulos";
import type { AcaoPlano, EstadoPlano } from "../types";
import { Detalhes, Fontes, SeloOrigem } from "./PartesPlano";
import { Aviso, Botao, Erro, Selo } from "./ui";

const MARCADOR = /\[[A-Z_]+\]/;

function temMarcador(a: AcaoPlano) {
  return [a.acao, a.relacao, a.responsavel, a.prazo, a.custoEstimado, a.premissas].some((t) => t && MARCADOR.test(t));
}

function Numero({ valor, rotulo }: { valor: number | string; rotulo: string }) {
  return (
    <div className="rounded-lg border border-black/5 bg-gov-blue-lt/40 p-3">
      <div className="text-2xl font-extrabold text-gov-blue-dark">{valor}</div>
      <div className="text-[12px] leading-tight text-gray-600">{rotulo}</div>
    </div>
  );
}

export function PreviaPlano({ estado, onFechar, onEnviado }: { estado: EstadoPlano; onFechar: () => void; onEnviado: (versao: number) => void }) {
  const [confirmado, setConfirmado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const acoes = estado.acoes;
  const loa = acoes.filter((a) => a.horizonte === "LOA").length;
  const comRelato = estado.barreiras.filter((b) => b.posicao === "obstaculo" || b.posicao === "divergencia");
  const cobertas = comRelato.filter((b) => acoes.some((a) => a.codigo === b.codigo));
  const semAcao = comRelato.filter((b) => !acoes.some((a) => a.codigo === b.codigo));
  const daIA = acoes.filter((a) => a.origem === "ia");
  const editadas = daIA.filter((a) => a.editada).length;
  const semResponsavel = acoes.filter((a) => !a.responsavel);
  const semPrazo = acoes.filter((a) => !a.prazo);
  const comMarcador = acoes.filter(temMarcador);
  const aEstimar = acoes.filter((a) => !a.custoEstimado || /estimar/i.test(a.custoEstimado)).length;
  const semCusto = acoes.filter((a) => a.custoEstimado && /sem custo/i.test(a.custoEstimado)).length;
  const pendencias = semAcao.length + semResponsavel.length + semPrazo.length + comMarcador.length;

  async function enviar() {
    setErro(null);
    setEnviando(true);
    try {
      onEnviado((await submeterPlano()).versao);
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal amplo titulo="Prévia do Plano de Ação" subtitulo={`${estado.escola} · baseado na Declaração v${estado.declaracaoBase}`} onFechar={onFechar}>
      <section aria-labelledby="titulo-sumario">
        <h2 id="titulo-sumario" className="text-[11px] font-extrabold uppercase tracking-wider text-accent">Sumário executivo</h2>
        <p className="mt-2 text-[14px] leading-relaxed text-ink">
          O plano reúne <strong>{acoes.length} {acoes.length === 1 ? "ação" : "ações"}</strong> para{" "}
          <strong>{cobertas.length} de {comRelato.length} barreiras</strong> com obstáculo ou divergência registrados na Declaração v
          {estado.declaracaoBase}. São <strong>{loa} no exercício corrente (LOA)</strong> e <strong>{acoes.length - loa} plurianuais (PPA)</strong>.{" "}
          {daIA.length > 0 && (
            <>
              {daIA.length} {daIA.length === 1 ? "partiu" : "partiram"} de sugestões do assistente ({editadas} editadas pela escola) e{" "}
              {acoes.length - daIA.length} {acoes.length - daIA.length === 1 ? "foi escrita" : "foram escritas"} pela escola.{" "}
            </>
          )}
          {semCusto > 0 && `${semCusto} sem custo direto para a escola; `}
          {aEstimar > 0 ? `${aEstimar} com custo a estimar.` : "todas com custo indicado."}
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Numero valor={acoes.length} rotulo="ações no plano" />
          <Numero valor={`${cobertas.length}/${comRelato.length}`} rotulo="barreiras com relato cobertas" />
          <Numero valor={loa} rotulo="LOA · exercício corrente" />
          <Numero valor={acoes.length - loa} rotulo="PPA · até quatro anos" />
        </div>
      </section>

      <section aria-labelledby="titulo-pendencias" className="mt-5">
        <h2 id="titulo-pendencias" className="text-[11px] font-extrabold uppercase tracking-wider text-accent">
          Pontos para revisar {pendencias === 0 && "· nenhum"}
        </h2>
        {pendencias > 0 ? (
          <ul className="mt-2 space-y-1.5 text-[13px] text-ink">
            {semAcao.length > 0 && (
              <li>
                <Selo tom="ambar">Sem ação</Selo> {semAcao.map((b) => b.barreira).join("; ")}. Não é obrigatório, mas a secretaria verá a barreira sem
                resposta no plano.
              </li>
            )}
            {comMarcador.length > 0 && (
              <li>
                <Selo tom="ambar">Marcador no texto</Selo> {comMarcador.length} {comMarcador.length === 1 ? "ação tem" : "ações têm"} trecho trocado pelo
                filtro de dados pessoais (como [NOME]). Confira se a frase continua clara e edite se preciso.
              </li>
            )}
            {semResponsavel.length > 0 && (
              <li>
                <Selo tom="ambar">Sem responsável</Selo> {semResponsavel.length} {semResponsavel.length === 1 ? "ação" : "ações"}.
              </li>
            )}
            {semPrazo.length > 0 && (
              <li>
                <Selo tom="ambar">Sem prazo</Selo> {semPrazo.length} {semPrazo.length === 1 ? "ação" : "ações"}.
              </li>
            )}
          </ul>
        ) : (
          <p className="mt-1 text-[13px] text-gray-600">Todas as barreiras com relato têm ação, com responsável e prazo.</p>
        )}
        {estado.desatualizado && (
          <div className="mt-2">
            <Aviso tom="atencao">
              O plano usa a Declaração v{estado.declaracaoBase}, mas a escola já emitiu a v{estado.ultimaDeclaracao}. A secretaria verá esse aviso.
            </Aviso>
          </div>
        )}
      </section>

      <section aria-labelledby="titulo-acoes-previa" className="mt-5">
        <h2 id="titulo-acoes-previa" className="text-[11px] font-extrabold uppercase tracking-wider text-accent">
          O plano, como a secretaria vai receber
        </h2>
        <div className="mt-2 space-y-3">
          {estado.barreiras.map((b) => {
            const doCodigo = acoes.filter((a) => a.codigo === b.codigo);
            if (!doCodigo.length && b.posicao === "sem_relato") return null;
            return (
              <div key={b.codigo} className="rounded-lg border border-black/10 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="text-[11px] text-gray-500">Eixo {b.eixo} · {NOMES_EIXOS[b.eixo]}</div>
                    <h3 className="text-[14px] font-extrabold text-ink">{b.barreira}</h3>
                  </div>
                  <Selo tom={POSICOES[b.posicao].tom}>{POSICOES[b.posicao].texto}</Selo>
                </div>
                {b.resumo && <p className="mt-1 text-[12px] text-gray-600">Relato: {b.resumo}</p>}
                {doCodigo.length === 0 ? (
                  <p className="mt-2 text-[13px] italic text-gray-500">Nenhuma ação para esta barreira.</p>
                ) : (
                  <ol className="mt-2 space-y-2">
                    {doCodigo.map((a, i) => (
                      <li key={a.id} className={`rounded-md bg-gov-blue-lt/40 p-2.5 ${temMarcador(a) ? "ring-2 ring-gov-orange" : ""}`}>
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <p className="text-[13px] font-bold text-ink">
                            {i + 1}. {a.acao}
                          </p>
                          <div className="flex gap-1">
                            <Selo tom="neutro">{a.horizonte}</Selo>
                            <SeloOrigem acao={a} />
                          </div>
                        </div>
                        {a.relacao && <p className="mt-1 text-[12px] text-gray-700">{a.relacao}</p>}
                        <Detalhes campos={a} />
                        <Fontes ids={a.fontes} citacoes={estado.fontes} />
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <div className="mt-5 border-t border-black/10 pt-4">
        <Aviso>
          A versão enviada fica congelada e aguardando análise. Mudanças depois disso geram uma nova versão. Custos e prazos são estimativas;
          o envio não é pedido de orçamento aprovado.
        </Aviso>
        <label className="mt-3 flex items-start gap-2 text-[13px] text-ink">
          <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#0e7c6b]" checked={confirmado} onChange={(e) => setConfirmado(e.target.checked)} />
          Revisei o plano e confirmo o envio à secretaria.
        </label>
        <div className="mt-3">
          <Erro mensagem={erro} />
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Botao variante="discreto" onClick={onFechar}>Voltar e editar</Botao>
          <Botao variante="coral" onClick={enviar} disabled={!confirmado || enviando}>
            {enviando ? "Enviando…" : "Enviar à secretaria"}
          </Botao>
        </div>
      </div>
    </Modal>
  );
}
