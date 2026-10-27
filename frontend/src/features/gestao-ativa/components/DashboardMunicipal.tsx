"use client";

// Dashboard municipal do secretário (requirements/secretario/dashboard-municipal.md; view
// secretary-dashboard do protótipo v2). Gravidade (Censo) e andamento (registros das escolas)
// aparecem separados (RN-DMS-05); escola sem registro não é escola sem dificuldade (RN-DMS-04).
import { useEffect, useState } from "react";

import { classificarFaixa, formatarScore } from "@/shared/lib/score";

import { getDashboardMunicipal } from "../api";
import { ESTADOS_VERSAO_PLANO, dataCurta } from "../rotulos";
import type { DashboardMunicipal as Dados, EscolaPrioritaria } from "../types";
import { Aviso, Botao, Cartao, Selo } from "./ui";

export type DestinoDashboard = "planos" | "analitico" | "municipal" | "declaracoes";

function tomDaFaixa(faixa: string): "verde" | "ambar" | "vermelho" {
  if (faixa === "Crítico" || faixa === "Insuficiente") return "vermelho";
  if (faixa === "Em desenvolvimento") return "ambar";
  return "verde";
}

const inteiro = (valor: number) => valor.toLocaleString("pt-BR");
const pontos = (valor: number) => valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function listaEixos(eixos: string[]) {
  if (eixos.length === 0) return "sem eixo crítico";
  const nomes = eixos.length === 1 ? eixos[0] : `${eixos.slice(0, -1).join(", ")} e ${eixos[eixos.length - 1]}`;
  return `${eixos.length === 1 ? "Eixo" : "Eixos"} ${nomes} ${eixos.length === 1 ? "crítico" : "críticos"}`;
}

export function DashboardMunicipal({ onAbrir }: { onAbrir: (destino: DestinoDashboard) => void }) {
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    getDashboardMunicipal().then(setDados).catch((falha) => setErro((falha as Error).message));
  }, []);

  if (erro) return <p role="alert" className="mx-auto mt-10 max-w-md rounded-lg bg-[#fbe9e7] p-4 text-sm text-[#b23838]">{erro}</p>;
  if (!dados) return <p role="status" className="mt-16 text-center text-sm text-gray-500">Carregando a situação da rede…</p>;

  const { cobertura } = dados;
  const somaTop = dados.prioridades.reduce((soma, p) => soma + p.peso, 0);

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <section className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-gov-blue-dark">Situação da rede municipal</h1>
          <p className="mt-2 max-w-2xl text-[15px] text-gray-600">
            Visão de gestão das {inteiro(cobertura.escolasMunicipais)} escolas municipais. Os dados públicos continuam na página pública; aqui
            estão reunidas as prioridades da rede e o que as escolas já registraram.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Botao variante="coral" onClick={() => onAbrir("planos")}>Analisar Planos de Ação</Botao>
            <Botao variante="contorno" onClick={() => onAbrir("municipal")}>Plano Estratégico Municipal</Botao>
          </div>
        </div>
        {dados.score !== null && dados.faixa && (
          <div className="rounded-lg bg-gov-blue-dark px-6 py-5 text-white">
            <div className="text-[11px] font-bold uppercase tracking-wider text-white/60">Score da rede municipal · Censo {dados.censoVersao}</div>
            <div className="mt-1 flex items-baseline gap-3">
              <span className="text-5xl font-extrabold">{formatarScore(dados.score)}</span>
              <span className="rounded-full px-2.5 py-0.5 text-[11px] font-bold text-white" style={{ backgroundColor: classificarFaixa(dados.score).cor }}>
                {dados.faixa}
              </span>
            </div>
            <div className="mt-2 text-[12px] text-white/70">
              {dados.ponderacao === "alunos_esp"
                ? `Ponderado por ${inteiro(dados.alunosEsp)} alunos da educação especial`
                : "Média simples: a rede não registra alunos da educação especial"}
            </div>
            {dados.scoreMunicipio !== null && (
              <div className="mt-1 text-[11px] text-white/50">
                Município com todas as redes ({inteiro(dados.escolasMunicipio)} escolas): {formatarScore(dados.scoreMunicipio)}, o valor da página pública.
              </div>
            )}
          </div>
        )}
      </section>

      {cobertura.escolasMunicipais === 0 ? (
        <div className="mt-6">
          <Aviso tom="atencao">O Censo {dados.censoVersao ?? ""} não registra escolas da rede municipal com score calculado neste município.</Aviso>
        </div>
      ) : (
        <>
          <section className="mt-8" aria-labelledby="titulo-eixos-rede">
            <div className="flex flex-wrap items-center gap-3">
              <h2 id="titulo-eixos-rede" className="text-lg font-extrabold text-gov-blue-dark">Eixos por criticidade</h2>
              <Selo tom="teal">Dados do Censo Escolar {dados.censoVersao}</Selo>
            </div>
            <p className="mt-1 text-[13px] text-gray-600">Ordenados pelo score do eixo na rede, do menor para o maior. O assistente de IA não define esta ordem.</p>
            <ol className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {dados.eixos.map((eixo, i) => (
                <li key={eixo.eixo}>
                  <Cartao className="h-full p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-extrabold text-ink">{i + 1}º · Eixo {eixo.eixo} · {eixo.nome}</h3>
                      <Selo tom={tomDaFaixa(eixo.faixa)}>{eixo.faixa}</Selo>
                    </div>
                    <div className="mt-2 text-2xl font-extrabold text-gov-blue-dark">{formatarScore(eixo.score)}</div>
                    <div className="mt-1 text-[12px] text-gray-500">Peso de {eixo.peso}% no score</div>
                  </Cartao>
                </li>
              ))}
            </ol>
          </section>

          <section className="mt-8" aria-labelledby="titulo-cobertura">
            <h2 id="titulo-cobertura" className="text-lg font-extrabold text-gov-blue-dark">Cobertura dos registros</h2>
            <p className="mt-1 text-[13px] text-gray-600">
              Cada número informa sua base. Escola sem Declaração ou sem plano enviado não é escola sem dificuldade.
            </p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Indicador valor={cobertura.escolasComBarreiras} base={`de ${inteiro(cobertura.escolasMunicipais)} escolas da rede`} titulo="Escolas com barreiras no Censo" />
              <Indicador valor={cobertura.comDeclaracao} base={`de ${inteiro(cobertura.escolasComBarreiras)} escolas com barreiras`} titulo="Com Declaração emitida" />
              <Indicador valor={cobertura.comPlanoEnviado} base={`de ${inteiro(cobertura.escolasComBarreiras)} escolas com barreiras`} titulo="Com Plano de Ação enviado" />
              <Indicador
                valor={cobertura.aguardandoAnalise}
                base={cobertura.planoMaisAntigo ? `o mais antigo enviado em ${dataCurta(cobertura.planoMaisAntigo)}` : "planos com decisão pendente"}
                titulo="Aguardando sua análise"
                destaque={cobertura.aguardandoAnalise > 0}
              />
            </div>
          </section>

          <section className="mt-8 grid gap-4 lg:grid-cols-[2fr_1fr]" aria-labelledby="titulo-prioridades">
            <Cartao className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 id="titulo-prioridades" className="text-lg font-extrabold text-gov-blue-dark">Escolas prioritárias</h2>
                <Selo tom="neutro">
                  {dados.prioridades.length} de {inteiro(dados.escolasNoRanking)} escolas
                </Selo>
              </div>
              <p className="mt-1 text-[13px] text-gray-600">
                Ordenadas pelos pontos que cada escola tira do score da rede. Juntas, estas {dados.prioridades.length} respondem por{" "}
                {pontos(somaTop)} dos {pontos(10 - (dados.score ?? 10))} pontos que faltam para a rede chegar a 10.
              </p>
              <ol className="mt-3">
                {dados.prioridades.map((p, i) => (
                  <Prioridade key={p.coEntidade} posicao={i + 1} escola={p} />
                ))}
              </ol>
              <details className="mt-3 text-[13px] text-gray-600">
                <summary className="cursor-pointer font-bold text-gov-blue">Entender o critério</summary>
                <div className="mt-2 space-y-2">
                  <p>
                    Peso da escola = (10 − score da escola) × alunos da educação especial da escola ÷ alunos da educação especial da rede. É a
                    mesma ponderação do score municipal, então a soma dos pesos de todas as escolas é exatamente o que falta para a rede chegar a 10.
                  </p>
                  <p>
                    Uma escola com score baixo e poucos alunos pode pesar menos que outra com score médio e muitos alunos. O peso mostra onde
                    está a maior parte da lacuna da rede, não a causa dela.
                  </p>
                  {dados.escolasSemAlunosEsp > 0 && (
                    <p>
                      {inteiro(dados.escolasSemAlunosEsp)} {dados.escolasSemAlunosEsp === 1 ? "escola não registra" : "escolas não registram"} alunos da
                      educação especial no Censo e {dados.escolasSemAlunosEsp === 1 ? "fica" : "ficam"} fora desta lista, porque não {dados.escolasSemAlunosEsp === 1 ? "pesa" : "pesam"} no
                      score da rede. Elas continuam na página pública e podem registrar Declaração.
                    </p>
                  )}
                  <p>Contagens abaixo de 5 alunos aparecem como “menos de 5” para não identificar estudantes.</p>
                </div>
              </details>
            </Cartao>

            <div className="space-y-4">
              <Cartao className="p-5">
                <h2 className="text-base font-extrabold text-gov-blue-dark">Fila de análise</h2>
                <p className="mt-1 text-[13px] text-gray-600">
                  {cobertura.aguardandoAnalise === 0
                    ? "Nenhum Plano de Ação aguarda sua decisão."
                    : `${cobertura.aguardandoAnalise} ${cobertura.aguardandoAnalise === 1 ? "plano aguarda" : "planos aguardam"} sua decisão. A fila é separada da lista de prioridades: segue a ordem de envio, não a gravidade.`}
                </p>
                <Botao variante="contorno" className="mt-3" onClick={() => onAbrir("planos")}>Abrir fila →</Botao>
              </Cartao>
              <Cartao className="p-5">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">Planejamento</p>
                <h2 className="mt-1 text-base font-extrabold text-gov-blue-dark">Plano Estratégico Municipal</h2>
                <p className="mt-1 text-[13px] text-gray-600">Junte as necessidades comuns dos planos aceitos em ações da rede.</p>
                <Botao variante="contorno" className="mt-3" onClick={() => onAbrir("municipal")}>Construir plano municipal →</Botao>
              </Cartao>
              <Cartao className="p-5">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">Análise</p>
                <h2 className="mt-1 flex items-center gap-2 text-base font-extrabold text-gov-blue-dark">
                  Analítico de Barreiras
                </h2>
                <p className="mt-1 text-[13px] text-gray-600">
                  Cruze barreiras, obstáculos e propostas para identificar padrões da rede, com uma síntese assistida por IA.
                </p>
                <Botao variante="contorno" className="mt-3" onClick={() => onAbrir("analitico")}>Abrir analítico →</Botao>
              </Cartao>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Indicador({ valor, base, titulo, destaque = false }: { valor: number; base: string; titulo: string; destaque?: boolean }) {
  return (
    <Cartao className={`p-4 ${destaque ? "border-l-4 border-l-accent" : ""}`}>
      <div className="text-[12px] font-bold text-gray-600">{titulo}</div>
      <div className="mt-1 text-3xl font-extrabold text-gov-blue-dark">{inteiro(valor)}</div>
      <div className="mt-0.5 text-[12px] text-gray-500">{base}</div>
    </Cartao>
  );
}

function Prioridade({ posicao, escola }: { posicao: number; escola: EscolaPrioritaria }) {
  const plano = escola.plano ? ESTADOS_VERSAO_PLANO[escola.plano] : null;
  return (
    <li className="grid grid-cols-[28px_1fr_auto] items-start gap-3 border-b border-black/5 py-3 last:border-0">
      <span className="text-sm font-extrabold text-gray-400">{posicao}</span>
      <div>
        <div className="text-[14px] font-bold text-ink">{escola.escola}</div>
        <div className="text-[12px] text-gray-500">
          Score {formatarScore(escola.score)} · {escola.alunosEsp === null ? "menos de 5" : inteiro(escola.alunosEsp)} alunos da educação especial ·{" "}
          {listaEixos(escola.eixosCriticos)}
        </div>
        <div className="mt-1 flex flex-wrap gap-1.5 text-[11px]">
          <span className="text-gray-500">Andamento:</span>
          <Selo tom={escola.declaracao ? "azul" : "neutro"}>{escola.declaracao ? "Declaração emitida" : "Sem Declaração emitida"}</Selo>
          {plano ? <Selo tom={plano.tom}>Plano: {plano.texto}</Selo> : <Selo tom="neutro">Sem plano enviado</Selo>}
        </div>
      </div>
      <div className="text-right">
        <div className="text-[15px] font-extrabold text-gov-blue-dark">−{pontos(escola.peso)}</div>
        <div className="text-[11px] text-gray-500">pts na rede</div>
        <div className="mt-1">
          <Selo tom={tomDaFaixa(escola.faixa)}>{escola.faixa}</Selo>
        </div>
      </div>
    </li>
  );
}
