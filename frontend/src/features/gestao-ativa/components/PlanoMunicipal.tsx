"use client";

// Plano Estratégico Municipal (requirements/secretario/plano-estrategico-municipal.md). A base vem dos
// Planos de Ação aceitos das escolas e do Censo; a IA propõe ações para a rede por barreira; o
// secretário decide, edita e confirma versões. Números de escolas são calculados pelo sistema.
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import {
  PDF,
  aceitarSugestaoMunicipal,
  confirmarPlanoMunicipal,
  descartarSugestaoMunicipal,
  editarAcaoMunicipal,
  getPlanoMunicipal,
  incluirAcaoMunicipal,
  removerAcaoMunicipal,
  sugerirAcoesMunicipais,
} from "../api";
import { dataCurta } from "../rotulos";
import type { AcaoMunicipal, BarreiraDaRede, Cobertura, EscolaAtendida, EstadoPlanoMunicipal, NovaAcaoMunicipal, Prioridade, SugestaoMunicipal } from "../types";
import { NarrativaExecutiva } from "./NarrativaExecutiva";
import { Fontes } from "./PartesPlano";
import { BotaoPdf } from "./BotaoPdf";
import { Aviso, Botao, Campo, CampoTexto, Cartao, Erro, Selo } from "./ui";

const PRIORIDADE: Record<Prioridade, { texto: string; tom: "vermelho" | "ambar" | "neutro" }> = {
  alta: { texto: "Prioridade alta", tom: "vermelho" },
  media: { texto: "Prioridade média", tom: "ambar" },
  baixa: { texto: "Prioridade baixa", tom: "neutro" },
};

function Escolas({ escolas }: { escolas: EscolaAtendida[] }) {
  if (!escolas.length) return <p className="mt-1 text-[12px] text-gray-500">Ação sistêmica, sem escola vinculada.</p>;
  return (
    <div className="mt-1.5">
      <div className="text-[11px] font-bold text-gray-500">
        Atende {escolas.length} {escolas.length === 1 ? "escola" : "escolas"}
      </div>
      <ul className="mt-0.5 flex flex-wrap gap-1">
        {escolas.map((e) => (
          <li key={e.coEntidade} className="rounded-full bg-white px-2 py-0.5 text-[11px] text-ink ring-1 ring-black/10">
            {e.escola}
            {e.cobertura === "parcial" && <span className="ml-1 font-bold text-[#8a5a00]">· parcial</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Linha({ a }: { a: { responsavel: string | null; prazo: string | null; horizonte: string; custoEstimado: string | null } }) {
  const texto = [a.responsavel, a.prazo, a.horizonte, a.custoEstimado && `Custo: ${a.custoEstimado}`].filter(Boolean).join(" · ");
  return texto ? <p className="mt-1 text-[12px] text-gray-600">{texto}</p> : null;
}

export function PlanoMunicipal({ foco = null }: { foco?: string | null }) {
  const [estado, setEstado] = useState<EstadoPlanoMunicipal | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [gerando, setGerando] = useState<string | null>(null);
  const [orientacoes, setOrientacoes] = useState<Record<string, string>>({});
  const [formulario, setFormulario] = useState<{ codigo: string; acao?: AcaoMunicipal; sugestao?: SugestaoMunicipal } | null>(null);
  const [confirmar, setConfirmar] = useState(false);
  const [narrativa, setNarrativa] = useState<number | null>(null);

  useEffect(() => {
    getPlanoMunicipal().then(setEstado).catch((falha) => setErro((falha as Error).message));
  }, []);

  // Vindo do Analítico, abre a tela já na barreira escolhida.
  const carregado = estado !== null;
  useEffect(() => {
    if (!carregado || !foco) return;
    const alvo = document.getElementById(`rede-${foco}`);
    alvo?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [carregado, foco]);

  async function executar(acao: () => Promise<EstadoPlanoMunicipal>, mensagem?: string) {
    setErro(null);
    try {
      const novo = await acao();
      setEstado(novo);
      setAviso(novo.avisoGuardiao ?? mensagem ?? null);
    } catch (falha) {
      setErro((falha as Error).message);
    }
  }

  async function sugerir(codigo: string) {
    setGerando(codigo);
    await executar(() => sugerirAcoesMunicipais(codigo, orientacoes[codigo]), "Sugestões prontas. Revise antes de incluir no plano municipal.");
    setOrientacoes((atual) => ({ ...atual, [codigo]: "" }));
    setGerando(null);
  }

  if (!estado) return erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Carregando a base da rede…</p>;

  const eixos = [...new Set(estado.barreiras.map((b) => b.eixo))];
  const loa = estado.acoes.filter((a) => a.horizonte === "LOA").length;
  const ultima = estado.versoes.at(-1);

  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          [estado.escolasComPlanoAceito, `de ${estado.escolasMunicipais} escolas com plano aceito`],
          [estado.acoes.length, "ações municipais no rascunho"],
          [estado.escolasAtendidas, "escolas atendidas pelo rascunho"],
          [ultima ? `v${ultima.versao}` : "—", ultima ? `confirmada em ${dataCurta(ultima.confirmadaEm)}` : "nenhuma versão confirmada"],
        ].map(([valor, rotulo]) => (
          <Cartao key={String(rotulo)} className="p-4">
            <div className="text-2xl font-extrabold text-gov-blue-dark">{valor}</div>
            <div className="text-[12px] text-gray-500">{rotulo}</div>
          </Cartao>
        ))}
      </div>
      <div className="mt-3">
        <Aviso>
          A base usa só os Planos de Ação aceitos pela secretaria. O assistente propõe ações para a rede juntando necessidades comuns; os
          números de escolas são calculados pelo sistema. Confirmar o plano não é aprovação orçamentária, financiamento nem execução, e não
          altera os planos das escolas.
        </Aviso>
      </div>
      {aviso && <p role="status" className="mt-3 rounded-lg bg-[#e7f3ec] px-4 py-2 text-[13px] text-[#2f7a55]">{aviso}</p>}
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>

      <div className="mt-2 grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section aria-label="Barreiras da rede" className="space-y-6">
          {estado.barreiras.length === 0 && <Cartao className="p-5 text-sm text-gray-600">Nenhuma barreira identificada na rede.</Cartao>}
          {eixos.map((eixo) => {
            const doEixo = estado.barreiras.filter((b) => b.eixo === eixo);
            return (
              <div key={eixo} className="space-y-3">
                <h3 className="rounded-lg bg-gov-blue-lt/60 px-3 py-2 text-[13px] font-extrabold uppercase tracking-wider text-gov-blue-dark">
                  Eixo {eixo} · {doEixo[0].eixoNome}
                </h3>
                {doEixo.map((b) => (
                  <CartaoBarreira
                    key={b.codigo}
                    barreira={b}
                    estado={estado}
                    gerando={gerando}
                    orientacao={orientacoes[b.codigo] ?? ""}
                    onOrientacao={(texto) => setOrientacoes((atual) => ({ ...atual, [b.codigo]: texto }))}
                    onSugerir={() => sugerir(b.codigo)}
                    onEscrever={() => setFormulario({ codigo: b.codigo })}
                    onIncluir={(s) => executar(() => aceitarSugestaoMunicipal(s.id), "Ação incluída no plano municipal.")}
                    onEditarSugestao={(s) => setFormulario({ codigo: s.codigo, sugestao: s })}
                    onDescartar={(s) => executar(() => descartarSugestaoMunicipal(s.id))}
                    onEditar={(a) => setFormulario({ codigo: a.codigos[0], acao: a })}
                    onRemover={(a) => executar(() => removerAcaoMunicipal(a.id))}
                  />
                ))}
              </div>
            );
          })}
        </section>

        <aside className="space-y-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:self-start lg:overflow-y-auto">
          <Cartao className="p-4">
            <h2 className="text-lg font-extrabold text-gov-blue-dark">Resumo do plano municipal</h2>
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
            <ul className="mt-3 space-y-1" aria-label="Barreiras">
              {estado.barreiras.map((b) => {
                const n = estado.acoes.filter((a) => a.codigos.includes(b.codigo)).length;
                return (
                  <li key={b.codigo}>
                    <a href={`#rede-${b.codigo}`} className="flex items-center gap-2 rounded-md px-1.5 py-1 text-[12px] hover:bg-black/[.03]">
                      <span aria-hidden className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-extrabold ${n ? "bg-[#2f9e6b] text-white" : "bg-gray-200 text-gray-600"}`}>
                        {n ? "✓" : "•"}
                      </span>
                      <span className="flex-1 text-ink">{b.nome}</span>
                      <span className="sr-only">{n ? `${n} ações municipais` : "sem ação municipal"}</span>
                      {n > 0 && <span aria-hidden className="text-[11px] text-gray-500">{n}</span>}
                    </a>
                  </li>
                );
              })}
            </ul>
            <Botao variante="coral" className="mt-4 w-full" disabled={!estado.acoes.length} onClick={() => setConfirmar(true)}>
              Confirmar versão do plano
            </Botao>
            {!estado.acoes.length && <p className="mt-1 text-[12px] text-gray-500">Inclua ao menos uma ação municipal.</p>}
          </Cartao>
          {estado.versoes.length > 0 && (
            <Cartao className="p-4">
              <h2 className="text-sm font-extrabold text-gov-blue-dark">Versões confirmadas</h2>
              <ul className="mt-2 space-y-1.5 text-[12px]">
                {[...estado.versoes].reverse().map((v) => (
                  <li key={v.versao}>
                    v{v.versao} · {dataCurta(v.confirmadaEm)} · {v.acoes} ações · {v.escolasAtendidas} escolas
                    {v.confirmadaPor && <span className="text-gray-500"> · {v.confirmadaPor}</span>}
                    <button
                      type="button"
                      onClick={() => setNarrativa(v.versao)}
                      className="ml-1 font-bold text-gov-blue underline-offset-2 hover:underline"
                    >
                      Narrativa executiva
                    </button>
                    <BotaoPdf comoLink caminho={PDF.planoMunicipal(v.versao)} rotulo="PDF" />
                  </li>
                ))}
              </ul>
            </Cartao>
          )}
        </aside>
      </div>

      {formulario && (
        <FormularioMunicipal
          estado={estado}
          codigo={formulario.codigo}
          inicial={formulario.acao ?? formulario.sugestao}
          titulo={formulario.acao ? "Editar ação municipal" : formulario.sugestao ? "Editar sugestão e incluir" : "Nova ação municipal"}
          onFechar={() => setFormulario(null)}
          onSalvar={async (dados) => {
            const { acao, sugestao } = formulario;
            const novo = acao
              ? await editarAcaoMunicipal(acao.id, dados)
              : sugestao
                ? await aceitarSugestaoMunicipal(sugestao.id, dados)
                : await incluirAcaoMunicipal(dados);
            setEstado(novo);
            setAviso(novo.avisoGuardiao ?? (acao ? "Ação municipal atualizada." : "Ação incluída no plano municipal."));
            setFormulario(null);
          }}
        />
      )}
      {confirmar && (
        <ConfirmarPlanoMunicipal
          estado={estado}
          onFechar={() => setConfirmar(false)}
          onConfirmado={async (versao) => {
            setConfirmar(false);
            setAviso(`Plano municipal v${versao} confirmado. Cada diretor passa a ver as ações que atendem a própria escola.`);
            setEstado(await getPlanoMunicipal());
          }}
        />
      )}
      {narrativa !== null && <NarrativaExecutiva numero={narrativa} onFechar={() => setNarrativa(null)} />}
    </div>
  );
}

function CartaoBarreira({
  barreira: b,
  estado,
  gerando,
  orientacao,
  onOrientacao,
  onSugerir,
  onEscrever,
  onIncluir,
  onEditarSugestao,
  onDescartar,
  onEditar,
  onRemover,
}: {
  barreira: BarreiraDaRede;
  estado: EstadoPlanoMunicipal;
  gerando: string | null;
  orientacao: string;
  onOrientacao: (texto: string) => void;
  onSugerir: () => void;
  onEscrever: () => void;
  onIncluir: (s: SugestaoMunicipal) => void;
  onEditarSugestao: (s: SugestaoMunicipal) => void;
  onDescartar: (s: SugestaoMunicipal) => void;
  onEditar: (a: AcaoMunicipal) => void;
  onRemover: (a: AcaoMunicipal) => void;
}) {
  const sugestoes = estado.sugestoes.filter((s) => s.codigo === b.codigo);
  const acoes = estado.acoes.filter((a) => a.codigos.includes(b.codigo));
  return (
    <Cartao className="scroll-mt-4 p-4">
      <div id={`rede-${b.codigo}`} className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="text-[15px] font-extrabold text-ink">{b.nome}</h4>
        {acoes.length > 0 ? <Selo tom="teal">{acoes.length} no plano municipal</Selo> : <Selo tom="neutro">Sem ação municipal</Selo>}
      </div>
      <p className="mt-1 text-[12px] text-gray-600">
        {b.escolasComBarreira} {b.escolasComBarreira === 1 ? "escola tem" : "escolas têm"} a barreira no Censo · {b.escolasComAcao}{" "}
        {b.escolasComAcao === 1 ? "escola trouxe ação" : "escolas trouxeram ação"} no plano aceito
      </p>

      {b.itens.length > 0 && (
        <details className="mt-2 rounded-lg bg-black/[.02] p-2.5 text-[12px]">
          <summary className="cursor-pointer font-bold text-gray-600 hover:text-gov-blue">Ver as {b.itens.length} ações das escolas</summary>
          <ul className="mt-2 space-y-1.5">
            {b.itens.map((i) => (
              <li key={i.itemId}>
                <span className="font-bold text-ink">{i.escola}:</span> {i.acao}
                <span className="text-gray-500"> ({[i.horizonte, i.prazo, i.custoEstimado].filter(Boolean).join(" · ")})</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {acoes.length > 0 && (
        <div className="mt-3">
          <div className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">No plano municipal</div>
          <ul className="mt-1.5 space-y-2">
            {acoes.map((a) => (
              <li key={a.id} className="rounded-lg border border-black/10 bg-white p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="flex-1 text-[13px] font-bold text-ink">{a.acao}</p>
                  <div className="flex gap-1">
                    <Selo tom={PRIORIDADE[a.prioridade].tom}>{PRIORIDADE[a.prioridade].texto}</Selo>
                    <Selo tom={a.origem === "ia" ? "teal" : "neutro"}>{a.origem === "ia" ? (a.editada ? "Sugerida pela IA · editada" : "Sugerida pela IA") : "Escrita pela secretaria"}</Selo>
                  </div>
                </div>
                <Linha a={a} />
                <Escolas escolas={a.escolas} />
                <details className="mt-1.5 text-[12px]">
                  <summary className="cursor-pointer font-bold text-gray-500 hover:text-gov-blue">Detalhes</summary>
                  {a.justificativa && <p className="mt-1 text-gray-700">{a.justificativa}</p>}
                  {a.premissas && <p className="mt-1 text-gray-600"><strong>Premissas:</strong> {a.premissas}</p>}
                  <Fontes ids={a.fontes} citacoes={estado.fontes} />
                </details>
                <div className="mt-2 flex gap-3">
                  <button onClick={() => onEditar(a)} className="text-[12px] font-bold text-gov-blue hover:underline">Editar</button>
                  <button onClick={() => onRemover(a)} className="text-[12px] font-bold text-gov-red hover:underline">Remover</button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 border-t border-black/5 pt-3">
        {b.itens.length > 0 ? (
          <>
            <label htmlFor={`orientacao-rede-${b.codigo}`} className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">
              Propor ações para a rede com o assistente
            </label>
            <input
              id={`orientacao-rede-${b.codigo}`}
              value={orientacao}
              onChange={(e) => onOrientacao(e.target.value)}
              maxLength={1000}
              placeholder="Orientação opcional (ex.: priorizar contratação conjunta)"
              className="mt-1.5 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-[13px] outline-none focus:border-gov-blue"
            />
            <p className="mt-1 text-[11px] text-gray-500">
              Vai para um assistente de IA externo, sem os nomes das escolas. Não identifique estudantes nem profissionais.
            </p>
          </>
        ) : (
          <p className="text-[12px] text-gray-500">Nenhum plano aceito traz ação para esta barreira; o assistente não tem base para propor.</p>
        )}
        <div className="mt-2 flex flex-wrap gap-2">
          {b.itens.length > 0 && (
            <Botao onClick={onSugerir} disabled={gerando !== null}>
              {gerando === b.codigo ? "Analisando os planos…" : orientacao.trim() ? "Propor com esta orientação" : sugestoes.length ? "Pedir outra proposta" : "Propor ações municipais"}
            </Botao>
          )}
          <Botao variante="discreto" onClick={onEscrever}>Escrever ação municipal</Botao>
        </div>
      </div>

      {sugestoes.map((s) => (
        <div key={s.id} className="mt-3 rounded-lg border border-gov-blue/30 bg-gov-blue-lt p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-extrabold uppercase tracking-wider text-gov-blue-mid">Sugestão do assistente</span>
            <Selo tom={PRIORIDADE[s.prioridade].tom}>{PRIORIDADE[s.prioridade].texto}</Selo>
          </div>
          <p className="mt-1 text-[14px] font-bold text-ink">{s.acao}</p>
          {s.justificativa && <p className="mt-1 text-[13px] text-gray-700">{s.justificativa}</p>}
          <Linha a={s} />
          <Escolas escolas={s.escolas} />
          <Fontes ids={s.fontes} citacoes={estado.fontes} />
          {s.incertezas && <p className="mt-1 text-[12px] text-gray-600"><strong>Incertezas:</strong> {s.incertezas}</p>}
          {s.lacunas.length > 0 && <p className="mt-1 text-[12px] text-gray-600"><strong>Lacunas:</strong> {s.lacunas.join(" ")}</p>}
          <div className="mt-2 flex flex-wrap gap-2">
            <Botao className="px-3 py-1.5 text-[12px]" onClick={() => onIncluir(s)} disabled={gerando !== null}>Incluir no plano</Botao>
            <Botao variante="contorno" className="px-3 py-1.5 text-[12px]" onClick={() => onEditarSugestao(s)} disabled={gerando !== null}>Editar e incluir</Botao>
            <Botao variante="discreto" className="px-3 py-1.5 text-[12px]" onClick={() => onDescartar(s)} disabled={gerando !== null}>Descartar</Botao>
          </div>
        </div>
      ))}
    </Cartao>
  );
}

function FormularioMunicipal({
  estado,
  codigo,
  inicial,
  titulo,
  onFechar,
  onSalvar,
}: {
  estado: EstadoPlanoMunicipal;
  codigo: string;
  inicial?: AcaoMunicipal | SugestaoMunicipal;
  titulo: string;
  onFechar: () => void;
  onSalvar: (dados: NovaAcaoMunicipal) => Promise<void>;
}) {
  const [codigos, setCodigos] = useState<string[]>(inicial && "codigos" in inicial ? inicial.codigos : [codigo]);
  const [campos, setCampos] = useState({
    acao: inicial?.acao ?? "",
    justificativa: inicial?.justificativa ?? "",
    responsavel: inicial?.responsavel ?? "secretaria municipal de educação",
    prazo: inicial?.prazo ?? "",
    horizonte: inicial?.horizonte ?? "PPA",
    custoEstimado: inicial?.custoEstimado ?? "",
    premissas: inicial?.premissas ?? "",
    prioridade: (inicial?.prioridade ?? "media") as Prioridade,
  });
  const [escolas, setEscolas] = useState<Record<number, { itemIds: string[]; cobertura: Cobertura }>>(
    Object.fromEntries((inicial?.escolas ?? []).map((e) => [e.coEntidade, { itemIds: e.itemIds, cobertura: e.cobertura }])),
  );
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Escolas com ação nas barreiras escolhidas: as que a ação municipal pode atender.
  const itens = estado.barreiras.filter((b) => codigos.includes(b.codigo)).flatMap((b) => b.itens);
  const candidatas = [...new Map(itens.map((i) => [i.coEntidade, i.escola])).entries()];
  const mudar = (campo: keyof typeof campos) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setCampos((atual) => ({ ...atual, [campo]: e.target.value }));

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await onSalvar({
        codigos,
        ...campos,
        escolas: Object.entries(escolas).map(([co, v]) => ({ coEntidade: Number(co), itemIds: v.itemIds, cobertura: v.cobertura })),
      });
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal amplo titulo={titulo} subtitulo={`Plano Estratégico Municipal · ${estado.municipio}/${estado.uf}`} onFechar={onFechar}>
      <form onSubmit={salvar}>
        <fieldset className="mb-3">
          <legend className="mb-1 text-xs font-bold text-gray-700">Barreiras que a ação enfrenta</legend>
          <div className="grid gap-1 sm:grid-cols-2">
            {estado.barreiras.map((b) => (
              <label key={b.codigo} className="flex items-center gap-2 text-[13px]">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[#0e7c6b]"
                  checked={codigos.includes(b.codigo)}
                  onChange={(e) => setCodigos((atual) => (e.target.checked ? [...atual, b.codigo] : atual.filter((c) => c !== b.codigo)))}
                />
                {b.nome}
              </label>
            ))}
          </div>
        </fieldset>
        <CampoTexto id="mun-acao" rotulo="Ação municipal" rows={2} value={campos.acao} onChange={mudar("acao")} required />
        <CampoTexto id="mun-justificativa" rotulo="Por que atende às escolas" rows={2} value={campos.justificativa} onChange={mudar("justificativa")} />
        <div className="grid gap-x-3 sm:grid-cols-2">
          <Campo id="mun-responsavel" rotulo="Responsável (órgão ou setor)" value={campos.responsavel} onChange={mudar("responsavel")} ajuda="Nunca o nome da pessoa." />
          <Campo id="mun-prazo" rotulo="Prazo" value={campos.prazo} onChange={mudar("prazo")} placeholder="Ex.: até 12 meses" />
          <Campo id="mun-custo" rotulo="Custo estimado" value={campos.custoEstimado} onChange={mudar("custoEstimado")} ajuda="Estimativa não é orçamento aprovado." />
          <div className="mb-3">
            <label htmlFor="mun-prioridade" className="mb-1 block text-xs font-bold text-gray-700">Prioridade</label>
            <select id="mun-prioridade" value={campos.prioridade} onChange={mudar("prioridade")} className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm">
              <option value="alta">Alta</option>
              <option value="media">Média</option>
              <option value="baixa">Baixa</option>
            </select>
          </div>
        </div>
        <fieldset className="mb-3">
          <legend className="mb-1 text-xs font-bold text-gray-700">Horizonte</legend>
          <div className="flex gap-4 text-[13px]">
            {(["LOA", "PPA"] as const).map((h) => (
              <label key={h} className="flex items-center gap-1.5">
                <input type="radio" name="mun-horizonte" value={h} checked={campos.horizonte === h} onChange={mudar("horizonte")} className="accent-[#0e7c6b]" />
                {h === "LOA" ? "LOA · exercício corrente" : "PPA · até quatro anos"}
              </label>
            ))}
          </div>
        </fieldset>
        <CampoTexto id="mun-premissas" rotulo="Premissas" rows={2} value={campos.premissas} onChange={mudar("premissas")} ajuda="Não inclua nomes nem dados de estudantes." />

        <fieldset className="mb-3">
          <legend className="mb-1 text-xs font-bold text-gray-700">Escolas atendidas</legend>
          {candidatas.length === 0 ? (
            <p className="text-[12px] text-gray-500">Nenhuma escola com plano aceito nas barreiras escolhidas: a ação fica como sistêmica.</p>
          ) : (
            <ul className="space-y-1.5">
              {candidatas.map(([co, nome]) => {
                const marcada = escolas[co];
                return (
                  <li key={co} className="flex flex-wrap items-center gap-3 text-[13px]">
                    <label className="flex flex-1 items-center gap-2">
                      <input
                        type="checkbox"
                        className="h-4 w-4 accent-[#0e7c6b]"
                        checked={!!marcada}
                        onChange={(e) =>
                          setEscolas((atual) => {
                            const novo = { ...atual };
                            if (e.target.checked) novo[co] = { itemIds: itens.filter((i) => i.coEntidade === co).map((i) => i.itemId), cobertura: "total" };
                            else delete novo[co];
                            return novo;
                          })
                        }
                      />
                      {nome}
                    </label>
                    {marcada && (
                      <select
                        aria-label={`Cobertura para ${nome}`}
                        value={marcada.cobertura}
                        onChange={(e) => setEscolas((atual) => ({ ...atual, [co]: { ...atual[co], cobertura: e.target.value as Cobertura } }))}
                        className="rounded-lg border border-gray-300 bg-white px-2 py-1 text-[12px]"
                      >
                        <option value="total">Cobertura total</option>
                        <option value="parcial">Cobertura parcial</option>
                      </select>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </fieldset>
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>Cancelar</Botao>
          <Botao type="submit" disabled={enviando || campos.acao.trim().length < 10 || !codigos.length}>{enviando ? "Salvando…" : "Salvar"}</Botao>
        </div>
      </form>
    </Modal>
  );
}

function ConfirmarPlanoMunicipal({ estado, onFechar, onConfirmado }: { estado: EstadoPlanoMunicipal; onFechar: () => void; onConfirmado: (versao: number) => void }) {
  const [ok, setOk] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const proxima = (estado.versoes.at(-1)?.versao ?? 0) + 1;
  const semAcao = estado.barreiras.filter((b) => b.escolasComBarreira > 0 && !estado.acoes.some((a) => a.codigos.includes(b.codigo)));

  async function confirmar() {
    setErro(null);
    setEnviando(true);
    try {
      onConfirmado((await confirmarPlanoMunicipal()).versao);
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo={`Confirmar o plano municipal v${proxima}`} subtitulo={`${estado.municipio}/${estado.uf}`} onFechar={onFechar}>
      <p className="text-[14px] text-ink">
        {estado.acoes.length} ações municipais, atendendo {estado.escolasAtendidas} de {estado.escolasMunicipais} escolas da rede.
      </p>
      {semAcao.length > 0 && (
        <div className="mt-3">
          <Aviso tom="atencao">
            {semAcao.length} {semAcao.length === 1 ? "barreira presente na rede fica" : "barreiras presentes na rede ficam"} sem ação municipal:{" "}
            {semAcao.map((b) => b.nome).join("; ")}.
          </Aviso>
        </div>
      )}
      <div className="mt-3">
        <Aviso>
          A versão fica congelada. Cada diretor passa a ver as ações que atendem a própria escola. Confirmar não é aprovação orçamentária,
          financiamento nem execução, e não altera os planos das escolas.
        </Aviso>
      </div>
      <label className="mt-3 flex items-start gap-2 text-[13px] text-ink">
        <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#0e7c6b]" checked={ok} onChange={(e) => setOk(e.target.checked)} />
        Revisei as ações, escolas atendidas, prioridades e estimativas.
      </label>
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>
      <div className="flex justify-end gap-2">
        <Botao variante="discreto" onClick={onFechar}>Voltar</Botao>
        <Botao variante="coral" onClick={confirmar} disabled={!ok || enviando}>{enviando ? "Confirmando…" : "Confirmar versão"}</Botao>
      </div>
    </Modal>
  );
}
