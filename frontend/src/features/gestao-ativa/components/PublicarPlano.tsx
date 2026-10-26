"use client";

// Publicação do Plano de Ação aceito (decisões de 2026-10-26): o diretor vê a versão pública com a
// checagem de dados pessoais e publica; o plano aparece ao público junto com a Declaração publicada.
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { getPreviaPlanoPublico, publicarPlano, retirarPlano } from "../api";
import { dataCurta } from "../rotulos";
import type { PreviaPlanoPublico } from "../types";
import { MOTIVOS_RETIRADA } from "./ModaisDeclaracao";
import { Aviso, Botao, Erro, Selecao, Selo } from "./ui";

export function PublicarPlano({ numero, onFechar, onMudou }: { numero: number; onFechar: () => void; onMudou: () => void }) {
  const [previa, setPrevia] = useState<PreviaPlanoPublico | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [motivo, setMotivo] = useState("");

  useEffect(() => {
    getPreviaPlanoPublico(numero).then(setPrevia).catch((falha) => setErro((falha as Error).message));
  }, [numero]);

  async function executar(acao: () => Promise<PreviaPlanoPublico>) {
    setErro(null);
    setEnviando(true);
    try {
      setPrevia(await acao());
      onMudou();
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  const publicado = !!previa?.publicadoEm && !previa.retiradoEm;
  const barreiras = previa ? [...new Set(previa.itens.map((i) => i.barreira))] : [];

  return (
    <Modal amplo titulo={`Plano de Ação v${numero} na página pública`} subtitulo={previa?.escola} onFechar={onFechar}>
      {!previa ? (
        erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Preparando a versão pública…</p>
      ) : (
        <>
          {publicado ? (
            <Aviso>
              Publicado em {dataCurta(previa.publicadoEm)}. Aparece na ficha da escola, junto com a Declaração de Obstáculos publicada.
            </Aviso>
          ) : (
            <Aviso>
              Esta é a versão que o público vai ler, junto com a Declaração publicada. Sem autoria, sem rascunho e sem sugestões do assistente.
              Aceite da secretaria não é garantia de orçamento: a página diz isso.
            </Aviso>
          )}
          {previa.motivo && !publicado && (
            <div className="mt-3">
              <Aviso tom="atencao">{previa.motivo}</Aviso>
            </div>
          )}

          {previa.pontos.length > 0 && !publicado && (
            <section className="mt-4" aria-labelledby="titulo-pontos-plano">
              <h2 id="titulo-pontos-plano" className="text-[11px] font-extrabold uppercase tracking-wider text-accent">Pontos de atenção</h2>
              <ul className="mt-2 space-y-1.5 text-[13px]">
                {previa.pontos.map((p, i) => (
                  <li key={i} className={`rounded-md px-3 py-2 ${p.bloqueia ? "bg-[#fbe9e7]" : "bg-[#fff4df]"}`}>
                    <Selo tom={p.bloqueia ? "vermelho" : "ambar"}>{p.bloqueia ? "Impede publicar" : "Revise"}</Selo>{" "}
                    <strong>{p.item}</strong>: {p.mensagem}
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-[12px] text-gray-500">
                Para mudar o texto, edite a ação no plano e envie nova versão à secretaria. A versão aceita não é alterada.
              </p>
            </section>
          )}

          <section className="mt-4" aria-labelledby="titulo-versao-publica">
            <h2 id="titulo-versao-publica" className="text-[11px] font-extrabold uppercase tracking-wider text-accent">Como o público vai ler</h2>
            <div className="mt-2 space-y-2 rounded-lg border border-black/10 bg-white p-3">
              <p className="text-[12px] text-gray-500">
                Versão {previa.versao}{previa.aceitoEm ? `, aceita pela secretaria municipal em ${dataCurta(previa.aceitoEm)}` : ""}. Custos e prazos são
                estimativas; o aceite não é garantia de orçamento nem de execução.
              </p>
              {barreiras.map((b) => (
                <div key={b} className="rounded border border-gray-100 p-2.5">
                  <div className="text-[13px] font-bold text-gray-700">{b}</div>
                  <ul className="mt-1 space-y-1.5">
                    {previa.itens
                      .filter((i) => i.barreira === b)
                      .map((i, n) => (
                        <li key={n} className="border-l-2 border-gov-blue/40 pl-2 text-[12px]">
                          <p className="font-bold text-ink">{i.acao}</p>
                          {i.relacao && <p className="text-gray-600">{i.relacao}</p>}
                          <p className="text-[11px] text-gray-500">
                            {[i.responsavel, i.prazo, i.horizonte, i.custoEstimado && `Custo: ${i.custoEstimado}`].filter(Boolean).join(" · ")}
                          </p>
                          {i.fontes.length > 0 && <p className="text-[10px] text-gray-400">Fontes: {i.fontes.join("; ")}</p>}
                        </li>
                      ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <div className="mt-4 border-t border-black/10 pt-4">
            <Erro mensagem={erro} />
            {publicado ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  executar(() => retirarPlano(numero, motivo));
                }}
              >
                <p className="mb-2 text-[13px] text-gray-600">Retirar tira o plano da página pública na hora. A versão aceita continua guardada.</p>
                <Selecao id="motivo-retirada-plano" rotulo="Motivo" opcoes={MOTIVOS_RETIRADA} value={motivo} onChange={(e) => setMotivo(e.target.value)} required />
                <div className="flex justify-end gap-2">
                  <Botao type="button" variante="discreto" onClick={onFechar}>Fechar</Botao>
                  <Botao type="submit" variante="perigo" disabled={!motivo || enviando}>{enviando ? "Retirando…" : "Retirar da página pública"}</Botao>
                </div>
              </form>
            ) : (
              <>
                <label className="flex items-start gap-2 text-[13px] text-ink">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 accent-[#0e7c6b]"
                    checked={confirmado}
                    disabled={!previa.podePublicar}
                    onChange={(e) => setConfirmado(e.target.checked)}
                  />
                  Revisei a versão pública e aprovo a publicação do plano.
                </label>
                <div className="mt-3 flex justify-end gap-2">
                  <Botao variante="discreto" onClick={onFechar}>Voltar</Botao>
                  <Botao variante="coral" disabled={!previa.podePublicar || !confirmado || enviando} onClick={() => executar(() => publicarPlano(numero))}>
                    {enviando ? "Publicando…" : "Publicar na página pública"}
                  </Botao>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </Modal>
  );
}
