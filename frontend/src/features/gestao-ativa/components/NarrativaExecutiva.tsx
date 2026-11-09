"use client";

// Narrativa executiva de uma versão confirmada do Plano Estratégico Municipal (RF-30; SPM-RF-05 e 06).
// O texto é da IA e o secretário revisa; os números ao lado são calculados pelo sistema a partir da
// versão congelada, e custos aparecem só como estimativas registradas pela secretaria.
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { editarNarrativaMunicipal, gerarNarrativaMunicipal, getVersaoMunicipal, PDF } from "../api";
import { dataCurta, rotulosAtuais } from "../rotulos";
import type { EdicaoNarrativa, NarrativaExecutiva as Narrativa, VersaoPlanoMunicipal } from "../types";
import { BotaoPdf } from "./BotaoPdf";
import { Aviso, Botao, Cartao, CampoTexto, Erro, Selo } from "./ui";

/** "[A2]" no texto da IA vira "(ação 2)", a numeração da lista de ações desta versão. */
const comAcoes = (texto: string) => texto.replace(/\s*\[A(\d{1,3})\]/g, " (ação $1)");

export function NarrativaExecutiva({ numero, onFechar }: { numero: number; onFechar: () => void }) {
  const [versao, setVersao] = useState<VersaoPlanoMunicipal | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [gerando, setGerando] = useState(false);
  const [editando, setEditando] = useState(false);
  const [substituir, setSubstituir] = useState(false);

  useEffect(() => {
    getVersaoMunicipal(numero).then(setVersao).catch((falha) => setErro((falha as Error).message));
  }, [numero]);

  async function gerar() {
    setGerando(true);
    setErro(null);
    setSubstituir(false);
    try {
      const nova = await gerarNarrativaMunicipal(numero);
      setVersao(nova);
      setAviso(nova.avisoGuardiao ?? "Narrativa pronta. Revise o texto antes de usá-lo.");
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setGerando(false);
    }
  }

  async function salvar(dados: EdicaoNarrativa) {
    const nova = await editarNarrativaMunicipal(numero, dados);
    setVersao(nova);
    setEditando(false);
    setAviso(nova.avisoGuardiao ?? "Texto revisado salvo.");
  }

  const subtitulo = versao ? `v${versao.versao} · confirmada em ${dataCurta(versao.confirmadaEm)}${versao.confirmadaPor ? ` por ${versao.confirmadaPor}` : ""}` : undefined;

  return (
    <Modal titulo="Narrativa executiva do plano municipal" subtitulo={subtitulo} onFechar={onFechar} amplo>
      {!versao ? (
        erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Carregando a versão…</p>
      ) : (
        <div className="space-y-5">
          <Aviso>
            Texto para apresentar o plano a quem decide o orçamento. A narrativa é escrita pelo assistente e revisada pela secretaria; os
            números ao lado são calculados pelo sistema a partir desta versão. Confirmar o plano não é aprovação orçamentária, financiamento
            nem execução.
          </Aviso>
          {aviso && <p role="status" className="rounded-lg bg-[#e7f3ec] px-4 py-2 text-[13px] text-[#2f7a55]">{aviso}</p>}
          <Erro mensagem={erro} />

          {versao.numeros && <Numeros versao={versao} />}

          <Cartao className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <h3 className="flex flex-wrap items-center gap-2 text-lg font-extrabold text-gov-blue-dark">
                Narrativa
                {versao.narrativa &&
                  (versao.narrativa.editada ? <Selo tom="verde">Revisada pela secretaria</Selo> : <Selo tom="ambar">Texto do assistente · revise</Selo>)}
              </h3>
              {!editando && (
                <div className="flex flex-wrap gap-2">
                  {versao.narrativa && (
                    <Botao variante="contorno" onClick={() => setEditando(true)} disabled={gerando}>
                      Editar texto
                    </Botao>
                  )}
                  {versao.narrativa && !gerando && <BotaoPdf caminho={PDF.narrativaMunicipal(versao.versao)} externo />}
                  <Botao
                    variante={versao.narrativa ? "discreto" : "primario"}
                    disabled={gerando}
                    onClick={() => (versao.narrativa?.editada ? setSubstituir(true) : gerar())}
                  >
                    {gerando ? "Escrevendo a narrativa…" : versao.narrativa ? "Gerar de novo" : "Gerar narrativa executiva"}
                  </Botao>
                </div>
              )}
            </div>
            {substituir && (
              <div className="mt-3">
                <Aviso tom="atencao">
                  Gerar de novo substitui o texto revisado pela secretaria.
                  <div className="mt-2 flex gap-2">
                    <Botao variante="coral" onClick={gerar}>Substituir</Botao>
                    <Botao variante="discreto" onClick={() => setSubstituir(false)}>Manter o texto</Botao>
                  </div>
                </Aviso>
              </div>
            )}

            {!versao.narrativa ? (
              <p className="mt-3 text-[13px] text-gray-600">
                O assistente escreve resumo, situação da rede, estratégia, fundamentação legal, próximos passos e incertezas a partir das
                ações desta versão. Ele não recebe o nome do município, das escolas nem os valores de custo.
              </p>
            ) : editando ? (
              <Edicao narrativa={versao.narrativa} total={versao.acoes.length} onCancelar={() => setEditando(false)} onSalvar={salvar} />
            ) : (
              <Texto narrativa={versao.narrativa} versao={versao} />
            )}
          </Cartao>

          <Acoes versao={versao} />
        </div>
      )}
    </Modal>
  );
}

function Numeros({ versao }: { versao: VersaoPlanoMunicipal }) {
  const n = versao.numeros!;
  const itens: [string | number, string][] = [
    [n.acoes, "ações municipais"],
    [n.barreiras, "barreiras enfrentadas"],
    [`${n.escolasAtendidas} de ${n.escolasMunicipais}`, `${rotulosAtuais().escolas} atendidas`],
    [`${n.loa} · ${n.ppa}`, "ações na LOA · no PPA"],
    [n.prioridadeAlta, "ações de prioridade alta"],
    [`${n.comCustoEstimado} de ${n.acoes}`, "ações com custo estimado pela secretaria"],
  ];
  return (
    <section aria-labelledby="numeros-plano">
      <div className="flex flex-wrap items-center gap-2">
        <h3 id="numeros-plano" className="text-sm font-extrabold text-gov-blue-dark">Números do plano</h3>
        <Selo tom="teal">Calculado pelo sistema · v{versao.versao}</Selo>
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-3">
        {itens.map(([valor, rotulo]) => (
          <div key={rotulo} className="rounded-lg bg-gov-blue-lt/60 px-3 py-2">
            <div className="text-xl font-extrabold text-gov-blue-dark">{valor}</div>
            <div className="text-[11px] text-gray-600">{rotulo}</div>
          </div>
        ))}
      </div>
      {n.comCoberturaParcial > 0 && (
        <p className="mt-1.5 text-[12px] text-gray-600">{n.comCoberturaParcial} ação(ões) atendem só parte do que as escolas pediram (cobertura parcial).</p>
      )}
    </section>
  );
}

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-[13px] font-extrabold uppercase tracking-wider text-gray-500">{titulo}</h4>
      <div className="mt-1 text-[14px] leading-relaxed text-ink">{children}</div>
    </div>
  );
}

function Texto({ narrativa: t, versao }: { narrativa: Narrativa; versao: VersaoPlanoMunicipal }) {
  const fontes = t.fontes.filter((f) => versao.fontes[f]);
  return (
    <div className="mt-4 space-y-4">
      <Secao titulo="Resumo">{comAcoes(t.resumo)}</Secao>
      {t.situacao && <Secao titulo="Situação da rede">{comAcoes(t.situacao)}</Secao>}
      {t.estrategia.length > 0 && (
        <Secao titulo="Estratégia">
          <ol className="list-decimal space-y-2 pl-5">
            {t.estrategia.map((b, i) => (
              <li key={i}>
                {comAcoes(b.texto)}
                {b.acoes.length > 0 && (
                  <span className="mt-0.5 block text-[12px] text-gray-500">
                    Ações: {b.acoes.map((a) => a.replace("A", "")).join(", ")}
                  </span>
                )}
              </li>
            ))}
          </ol>
        </Secao>
      )}
      {t.fundamentacao && <Secao titulo="Fundamentação legal">{comAcoes(t.fundamentacao)}</Secao>}
      {t.proximosPassos && <Secao titulo="Próximos passos">{comAcoes(t.proximosPassos)}</Secao>}
      {t.incertezas.length > 0 && (
        <Secao titulo="Incertezas">
          <ul className="list-disc pl-5">
            {t.incertezas.map((i, k) => <li key={k}>{comAcoes(i)}</li>)}
          </ul>
        </Secao>
      )}
      {fontes.length > 0 && (
        <Secao titulo="Fontes citadas">
          <ul className="list-disc pl-5 text-[13px]">
            {fontes.map((f) => <li key={f}>{versao.fontes[f]}</li>)}
          </ul>
        </Secao>
      )}
      {t.lacunas.length > 0 && (
        <p className="text-[12px] text-gray-600">
          <strong>O que a base normativa entregue não sustenta:</strong> {t.lacunas.join(" ")}
        </p>
      )}
      <p className="text-[12px] text-gray-500">
        Gerada em {new Date(t.geradaEm).toLocaleString("pt-BR")} por {t.modelo}.{t.editada && " Texto revisado pela secretaria depois disso."}
      </p>
    </div>
  );
}

function Edicao({
  narrativa,
  total,
  onCancelar,
  onSalvar,
}: {
  narrativa: Narrativa;
  total: number;
  onCancelar: () => void;
  onSalvar: (dados: EdicaoNarrativa) => Promise<void>;
}) {
  const [dados, setDados] = useState<EdicaoNarrativa>({
    resumo: narrativa.resumo,
    situacao: narrativa.situacao,
    estrategia: narrativa.estrategia,
    fundamentacao: narrativa.fundamentacao,
    proximosPassos: narrativa.proximosPassos,
    incertezas: narrativa.incertezas,
    lacunas: narrativa.lacunas,
  });
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const campo = (chave: "resumo" | "situacao" | "fundamentacao" | "proximosPassos") => ({
    value: dados[chave],
    onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => setDados({ ...dados, [chave]: e.target.value }),
  });

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      const linhas = (lista: string[]) => lista.map((i) => i.trim()).filter(Boolean);
      await onSalvar({ ...dados, incertezas: linhas(dados.incertezas), lacunas: linhas(dados.lacunas) });
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="mt-4 space-y-3">
      <p className="text-[12px] text-gray-600">
        Referências como [A2] apontam a ação 2 desta versão (de 1 a {total}). O texto passa pelo filtro de dados pessoais ao salvar e não
        pode ter valores, percentuais, quantidades, nomes de escola, bairro ou município nem descrição de um estudante: os números já
        aparecem ao lado, e a narrativa vai a quem decide o orçamento.
      </p>
      <CampoTexto id="nar-resumo" rotulo="Resumo" rows={4} required {...campo("resumo")} />
      <CampoTexto id="nar-situacao" rotulo="Situação da rede" rows={3} {...campo("situacao")} />
      {dados.estrategia.map((b, i) => (
        <CampoTexto
          key={i}
          id={`nar-estrategia-${i}`}
          rotulo={`Estratégia ${i + 1}${b.acoes.length ? ` · ações ${b.acoes.map((a) => a.replace("A", "")).join(", ")}` : ""}`}
          rows={3}
          value={b.texto}
          onChange={(e) => setDados({ ...dados, estrategia: dados.estrategia.map((x, k) => (k === i ? { ...x, texto: e.target.value } : x)) })}
        />
      ))}
      <CampoTexto id="nar-fundamentacao" rotulo="Fundamentação legal" rows={3} {...campo("fundamentacao")} />
      <CampoTexto id="nar-passos" rotulo="Próximos passos" rows={3} {...campo("proximosPassos")} />
      <CampoTexto
        id="nar-incertezas"
        rotulo="Incertezas"
        ajuda="Uma por linha."
        rows={3}
        value={dados.incertezas.join("\n")}
        onChange={(e) => setDados({ ...dados, incertezas: e.target.value.split("\n") })}
      />
      <CampoTexto
        id="nar-lacunas"
        rotulo="O que a base normativa entregue não sustenta"
        ajuda="Uma por linha."
        rows={2}
        value={dados.lacunas.join("\n")}
        onChange={(e) => setDados({ ...dados, lacunas: e.target.value.split("\n") })}
      />
      <Erro mensagem={erro} />
      <div className="flex gap-2">
        <Botao type="submit" disabled={salvando}>{salvando ? "Salvando…" : "Salvar texto revisado"}</Botao>
        <Botao type="button" variante="discreto" onClick={onCancelar}>Cancelar</Botao>
      </div>
    </form>
  );
}

function Acoes({ versao }: { versao: VersaoPlanoMunicipal }) {
  return (
    <section aria-labelledby="acoes-versao">
      <h3 id="acoes-versao" className="text-sm font-extrabold text-gov-blue-dark">Ações desta versão</h3>
      <ol className="mt-2 space-y-2">
        {versao.acoes.map((a, i) => (
          <li key={a.id} className="rounded-lg border border-black/5 bg-white p-3 text-[13px]">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold text-gray-500">Ação {i + 1} · {a.codigos.join(", ")} · {a.horizonte}</span>
            </div>
            <p className="mt-1 text-ink">{a.acao}</p>
            <p className="mt-1 text-[12px] text-gray-600">
              {a.custoEstimado && a.custoEstimado.trim().toLowerCase() !== "a estimar"
                ? `Estimativa de custo registrada pela secretaria (não verificada): ${a.custoEstimado}`
                : "Custo a estimar"}
              {a.escolas.length > 0 && ` · atende ${a.escolas.length} ${a.escolas.length === 1 ? "escola" : "escolas"}`}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
