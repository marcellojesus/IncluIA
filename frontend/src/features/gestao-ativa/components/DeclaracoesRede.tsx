"use client";

// Declarações emitidas pelas escolas da rede (RN-DO-07). Só versões emitidas aparecem, nunca
// rascunho; escola sem declaração é "sem registro emitido", não escola sem dificuldade (RN-SAB-04).
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { getDeclaracoesRede, getVersaoDaRede } from "../api";
import { dataCurta } from "../rotulos";
import type { DeclaracoesDaRede, VersaoDeclaracao } from "../types";
import { ListaPorEixo } from "./ModaisDeclaracao";
import { Aviso, Cartao, Erro, Selo } from "./ui";

export function DeclaracoesRede() {
  const [rede, setRede] = useState<DeclaracoesDaRede | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aberta, setAberta] = useState<VersaoDeclaracao | null>(null);

  useEffect(() => {
    getDeclaracoesRede().then(setRede).catch((falha) => setErro((falha as Error).message));
  }, []);

  async function abrir(coEntidade: number, versao: number) {
    setErro(null);
    try {
      setAberta(await getVersaoDaRede(coEntidade, versao));
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  if (!rede) return erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Carregando…</p>;

  const semRegistro = rede.escolasMunicipais - rede.comDeclaracao;

  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Cartao className="p-4">
          <div className="text-[12px] text-gray-500">Escolas municipais</div>
          <div className="text-2xl font-extrabold text-gov-blue-dark">{rede.escolasMunicipais}</div>
        </Cartao>
        <Cartao className="p-4">
          <div className="text-[12px] text-gray-500">Com Declaração emitida</div>
          <div className="text-2xl font-extrabold text-gov-blue-dark">{rede.comDeclaracao}</div>
        </Cartao>
        <Cartao className="p-4">
          <div className="text-[12px] text-gray-500">Sem registro emitido</div>
          <div className="text-2xl font-extrabold text-gov-blue-dark">{semRegistro}</div>
        </Cartao>
      </div>
      <div className="mt-3">
        <Aviso>
          Escola sem Declaração emitida não significa escola sem dificuldade: significa que ainda não há registro da escola. Versões não
          publicadas são documentos internos da rede; não as divulgue.
        </Aviso>
      </div>
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>

      <Cartao className="mt-1 overflow-x-auto">
        {rede.escolas.length === 0 ? (
          <p className="p-5 text-sm text-gray-600">Nenhuma escola da rede emitiu a Declaração de Obstáculos ainda.</p>
        ) : (
          <table className="w-full min-w-[760px] text-left text-[13px]">
            <thead className="border-b border-black/5 text-[11px] uppercase tracking-wider text-gray-500">
              <tr>
                <th scope="col" className="px-4 py-2.5">Escola</th>
                <th scope="col" className="px-4 py-2.5">Versão</th>
                <th scope="col" className="px-4 py-2.5">Posições</th>
                <th scope="col" className="px-4 py-2.5">Página pública</th>
                <th scope="col" className="px-4 py-2.5"><span className="sr-only">Abrir</span></th>
              </tr>
            </thead>
            <tbody>
              {rede.escolas.map((e) => (
                <tr key={e.coEntidade} className="border-b border-black/5 last:border-0">
                  <td className="px-4 py-3 align-top">
                    <div className="font-bold text-ink">{e.escola}</div>
                    <div className="text-[12px] text-gray-500">INEP {e.coEntidade}</div>
                  </td>
                  <td className="px-4 py-3 align-top">
                    v{e.versao}
                    <div className="text-[12px] text-gray-500">emitida em {dataCurta(e.emitidaEm)}</div>
                  </td>
                  <td className="px-4 py-3 align-top text-[12px] text-gray-700">
                    {e.obstaculos} obstáculo(s) · {e.divergencias} divergência(s) · {e.semRelato} sem relato
                  </td>
                  <td className="px-4 py-3 align-top">
                    {e.retiradaEm ? (
                      <Selo tom="neutro">Retirada em {dataCurta(e.retiradaEm)}</Selo>
                    ) : e.publicadaEm ? (
                      <Selo tom="verde">Publicada em {dataCurta(e.publicadaEm)}</Selo>
                    ) : (
                      <Selo tom="neutro">Não publicada</Selo>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right align-top">
                    <button onClick={() => abrir(e.coEntidade, e.versao)} className="rounded-lg px-3 py-1.5 text-[12px] font-bold text-gov-blue hover:bg-gov-blue-lt">
                      Ler declaração
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Cartao>

      {aberta && (
        <Modal titulo={`Declaração v${aberta.versao}`} subtitulo={`${aberta.escola} · emitida em ${dataCurta(aberta.emitidaEm)}`} onFechar={() => setAberta(null)}>
          <div className="max-h-[60vh] overflow-y-auto pr-1">
            <ListaPorEixo
              itens={aberta.itens.map((i) => ({ codigo: i.codigo, eixo: i.eixo, nome: i.barreira, dadoCenso: i.dadoCenso, posicao: i.posicao, texto: i.texto }))}
            />
          </div>
          <p className="mt-3 text-[12px] text-gray-500">
            Versão emitida pela escola; os dados do Censo e o score não mudam com a declaração.
            {aberta.publicadaEm && !aberta.retiradaEm ? " Esta versão está publicada." : " Documento interno da rede: não divulgue."}
          </p>
        </Modal>
      )}
    </div>
  );
}
