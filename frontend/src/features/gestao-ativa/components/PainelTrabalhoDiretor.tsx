"use client";

// Topo do dashboard do diretor: o que depende dele agora (pendências, com a mais urgente em destaque)
// e a situação de cada registro da escola (Declaração, Plano de Ação, publicação, ações municipais).
import Link from "next/link";
import { useEffect, useState } from "react";

import { getAcoesMunicipaisDaEscola } from "../api";
import { dataCurta } from "../rotulos";
import type { AcoesMunicipaisDaEscola, DashboardEscola } from "../types";
import { Cartao, Selo } from "./ui";

type Tarefa = {
  id: string;
  titulo: string;
  detalhe: string;
  botao: string;
  href: string;
  urgente?: boolean;
  citacao?: string | null;
};

function tarefas(d: DashboardEscola): Tarefa[] {
  const lista: Tarefa[] = [];
  const dec = d.declaracao;
  const plano = d.plano;
  const faltam = dec.total - dec.comPosicao;

  if (
    plano &&
    (plano.estado === "ajustes_solicitados" || plano.estado === "reprovado")
  ) {
    const ajustes = plano.estado === "ajustes_solicitados";
    lista.push({
      id: "ajustar",
      titulo: ajustes
        ? `Ajuste solicitado no Plano de Ação v${plano.versao}`
        : `Plano de Ação v${plano.versao} reprovado`,
      detalhe: `${plano.decididaEm ? `Decisão da secretaria em ${dataCurta(plano.decididaEm)}. ` : ""}Os pontos marcados aparecem destacados no plano.`,
      citacao: plano.comentario,
      botao: ajustes ? "Ajustar o plano" : "Revisar o plano",
      href: "/gestao/diretor/plano",
      urgente: true,
    });
  }
  if (dec.estado === "rascunho" && d.barreiras.length > 0) {
    lista.push(
      faltam > 0
        ? {
            id: "registrar",
            titulo: "Registrar obstáculos",
            detalhe: `${dec.comPosicao} de ${dec.total} barreiras com posição. Faltam ${faltam} para emitir a Declaração.`,
            botao: "Registrar obstáculos",
            href: "/gestao/diretor/declaracao",
          }
        : {
            id: "emitir",
            titulo: "Emitir a Declaração de Obstáculos",
            detalhe:
              "Todas as barreiras têm posição. Emita para enviar à secretaria e começar o Plano de Ação.",
            botao: "Revisar e emitir",
            href: "/gestao/diretor/declaracao",
          },
    );
  } else if (dec.haAlteracoes) {
    lista.push({
      id: "reemitir",
      titulo: "Emitir nova versão da Declaração",
      detalhe: `Há alterações depois da v${dec.versao}. A secretaria só vê o que foi emitido.`,
      botao: "Revisar a Declaração",
      href: "/gestao/diretor/declaracao",
    });
  }
  if (plano && plano.estado === "rascunho") {
    lista.push({
      id: "fazer-plano",
      titulo: "Realizar o Plano de Ação",
      detalhe: plano.acoesNoRascunho
        ? `${plano.acoesNoRascunho} ${plano.acoesNoRascunho === 1 ? "ação" : "ações"} no rascunho. Revise e envie à secretaria.`
        : `A Declaração v${plano.declaracaoBase} está emitida. Monte as ações da escola com apoio do assistente.`,
      botao: plano.acoesNoRascunho ? "Continuar o plano" : "Começar o plano",
      href: "/gestao/diretor/plano",
    });
  }
  if (plano?.desatualizado && plano.estado !== "sem_declaracao") {
    lista.push({
      id: "atualizar-base",
      titulo: "Atualizar a base do Plano de Ação",
      detalhe: `O plano usa a Declaração v${plano.declaracaoBase}, mas já existe uma versão mais nova.`,
      botao: "Abrir o plano",
      href: "/gestao/diretor/plano",
    });
  }
  if (plano?.versaoAceita && plano.versaoPublicada !== plano.versaoAceita) {
    lista.push(
      dec.estado === "publicada"
        ? {
            id: "publicar-plano",
            titulo: "Publicar o Plano de Ação aceito",
            detalhe: `A v${plano.versaoAceita} foi aceita pela secretaria. Publique para dar transparência à comunidade.`,
            botao: "Publicar o plano",
            href: "/gestao/diretor/plano",
          }
        : {
            id: "publicar-declaracao",
            titulo: "Publicar a Declaração de Obstáculos",
            detalhe:
              "O plano aceito só aparece na página pública junto com a Declaração publicada.",
            botao: "Publicar a Declaração",
            href: "/gestao/diretor/declaracao",
          },
    );
  }
  return lista;
}

type Status = {
  rotulo: string;
  tom: "pendente" | "andamento" | "ok" | "alerta" | "neutro";
  detalhe: string;
};

const CORES: Record<Status["tom"], string> = {
  pendente: "bg-[#fff4df] text-[#8a5a00]",
  andamento: "bg-gov-blue-lt text-gov-blue",
  ok: "bg-[#e7f3ec] text-[#2f7a55]",
  alerta: "bg-[#fdece8] text-accent-dark",
  neutro: "bg-black/[.05] text-gray-600",
};

function statusDeclaracao(d: DashboardEscola): Status {
  const dec = d.declaracao;
  if (dec.estado === "rascunho")
    return {
      rotulo: "Pendente",
      tom: "pendente",
      detalhe: `${dec.comPosicao} de ${dec.total} barreiras com posição`,
    };
  if (dec.estado === "publicada")
    return {
      rotulo: `Publicada · v${dec.versao}`,
      tom: "ok",
      detalhe: `Publicada em ${dataCurta(dec.publicadaEm)}`,
    };
  return {
    rotulo: `Registrada · v${dec.versao}`,
    tom: "andamento",
    detalhe: `Emitida em ${dataCurta(dec.emitidaEm)}; ainda não publicada`,
  };
}

function statusPlano(d: DashboardEscola): Status {
  const p = d.plano;
  if (!p || p.estado === "sem_declaracao")
    return {
      rotulo: "Pendente",
      tom: "neutro",
      detalhe: "Começa depois de emitir a Declaração",
    };
  if (p.versaoPublicada)
    return {
      rotulo: `Publicado · v${p.versaoPublicada}`,
      tom: "ok",
      detalhe: "Aceito pela secretaria e na página pública",
    };
  switch (p.estado) {
    case "rascunho":
      return {
        rotulo: "Pendente",
        tom: "pendente",
        detalhe: p.acoesNoRascunho
          ? `${p.acoesNoRascunho} ações no rascunho, não enviado`
          : "Ainda não iniciado",
      };
    case "aguardando_analise":
      return {
        rotulo: `Em análise · v${p.versao}`,
        tom: "andamento",
        detalhe: "Aguardando a decisão da secretaria",
      };
    case "ajustes_solicitados":
      return {
        rotulo: `Ajustes solicitados · v${p.versao}`,
        tom: "alerta",
        detalhe: "Revise os pontos marcados e reenvie",
      };
    case "reprovado":
      return {
        rotulo: `Reprovado · v${p.versao}`,
        tom: "alerta",
        detalhe: "Revise e envie nova versão",
      };
    case "aceito":
      return {
        rotulo: `Aceito · v${p.versao}`,
        tom: "ok",
        detalhe: "Aceito pela secretaria; ainda não publicado",
      };
  }
}

function LinhaStatus({
  titulo,
  status,
  href,
}: {
  titulo: string;
  status: Status;
  href?: string;
}) {
  const conteudo = (
    <>
      <div>
        <div className="text-[13px] font-extrabold text-ink">{titulo}</div>
        <div className="text-[12px] text-gray-600">{status.detalhe}</div>
      </div>
      <span
        className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-extrabold ${CORES[status.tom]}`}
      >
        {status.rotulo}
      </span>
    </>
  );
  return href ? (
    <Link
      href={href}
      className="flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 hover:bg-black/[.03]"
    >
      {conteudo}
    </Link>
  ) : (
    <div className="flex items-center justify-between gap-3 px-2 py-2.5">
      {conteudo}
    </div>
  );
}

export function PainelTrabalhoDiretor({ dados }: { dados: DashboardEscola }) {
  const lista = tarefas(dados);
  const [municipais, setMunicipais] = useState<AcoesMunicipaisDaEscola | null>(
    null,
  );

  useEffect(() => {
    getAcoesMunicipaisDaEscola()
      .then(setMunicipais)
      .catch(() => setMunicipais(null));
  }, []);
  const [primeira, ...demais] = lista;

  return (
    <>
      <section
        className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]"
        aria-label="Pendências e situação da escola"
      >
        <div>
          <h2 className="text-lg font-extrabold text-gov-blue-dark">
            Suas pendências{" "}
            {lista.length > 0 && (
              <span className="ml-1 rounded-full bg-accent px-2 py-0.5 align-middle text-[12px] font-extrabold text-white">
                {lista.length}
              </span>
            )}
          </h2>
          {lista.length === 0 ? (
            <Cartao className="mt-3 p-5">
              <p className="text-[15px] font-extrabold text-[#2f7a55]">
                Nenhuma pendência no momento.
              </p>
              <p className="mt-1 text-[13px] text-gray-600">
                {dados.plano?.estado === "aguardando_analise"
                  ? "O Plano de Ação está com a secretaria. Você será avisado aqui quando houver decisão."
                  : "Os registros da escola estão em dia."}
              </p>
            </Cartao>
          ) : (
            <div className="mt-3 space-y-3">
              <div
                role="status"
                className={`flex flex-col gap-3 rounded-lg border-l-[6px] p-5 md:flex-row md:items-center md:justify-between ${primeira.urgente ? "border-accent bg-[#fdece8]" : "border-gov-blue bg-gov-blue-lt"}`}
              >
                <div>
                  <p
                    className={`text-xs font-extrabold uppercase tracking-wider ${primeira.urgente ? "text-accent-dark" : "text-gov-blue"}`}
                  >
                    {primeira.urgente ? "Ação necessária" : "Próximo passo"}
                  </p>
                  <h3 className="mt-1 text-xl font-extrabold text-gov-blue-dark">
                    {primeira.titulo}
                  </h3>
                  {primeira.citacao && (
                    <blockquote className="mt-2 border-l-2 border-accent/40 pl-3 text-[14px] text-ink">
                      “{primeira.citacao}”
                    </blockquote>
                  )}
                  <p className="mt-1 text-[13px] text-gray-600">
                    {primeira.detalhe}
                  </p>
                </div>
                <Link
                  href={primeira.href}
                  className="chamar-atencao inline-flex shrink-0 items-center justify-center rounded-lg bg-accent px-6 py-3 text-[15px] font-extrabold text-white shadow-md hover:bg-accent-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                >
                  {primeira.botao} →
                </Link>
              </div>
              {demais.map((t) => (
                <Cartao
                  key={t.id}
                  className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="text-[14px] font-extrabold text-ink">
                      {t.titulo}
                    </p>
                    <p className="text-[12px] text-gray-600">{t.detalhe}</p>
                  </div>
                  <Link
                    href={t.href}
                    className="shrink-0 rounded-lg border-2 border-accent px-4 py-2 text-[13px] font-bold text-accent-dark hover:bg-[#fdece8]"
                  >
                    {t.botao} →
                  </Link>
                </Cartao>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="text-lg font-extrabold text-gov-blue-dark">
            Situação
          </h2>
          <Cartao className="mt-3 divide-y divide-black/5 p-2">
            <LinhaStatus
              titulo="Declaração de Obstáculos"
              status={statusDeclaracao(dados)}
              href={
                dados.barreiras.length
                  ? "/gestao/diretor/declaracao"
                  : undefined
              }
            />
            <LinhaStatus
              titulo="Plano de Ação"
              status={statusPlano(dados)}
              href={
                dados.plano && dados.plano.estado !== "sem_declaracao"
                  ? "/gestao/diretor/plano"
                  : undefined
              }
            />
            <LinhaStatus
              titulo="Ações municipais"
              status={
                municipais?.acoes.length
                  ? {
                      rotulo: `${municipais.acoes.length} para a escola`,
                      tom: "ok",
                      detalhe: `Plano municipal v${municipais.versao}, confirmado em ${dataCurta(municipais.confirmadaEm)}`,
                    }
                  : {
                      rotulo: "Nenhuma",
                      tom: "neutro",
                      detalhe:
                        "Ações da secretaria para a escola aparecem aqui",
                    }
              }
              href={municipais?.acoes.length ? "#acoes-municipais" : undefined}
            />
          </Cartao>
        </div>
      </section>
      {municipais && municipais.acoes.length > 0 && (
        <section
          id="acoes-municipais"
          className="mt-6 scroll-mt-4"
          aria-labelledby="titulo-acoes-municipais"
        >
          <h2
            id="titulo-acoes-municipais"
            className="text-lg font-extrabold text-gov-blue-dark"
          >
            Ações da secretaria para a sua escola
          </h2>
          <p className="mt-1 text-[13px] text-gray-600">
            Do Plano Estratégico Municipal v{municipais.versao}, confirmado em{" "}
            {dataCurta(municipais.confirmadaEm)}. Planejamento da rede: não é
            garantia de orçamento nem de execução.
          </p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {municipais.acoes.map((a, i) => (
              <Cartao key={i} className="p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="flex-1 text-[14px] font-bold text-ink">
                    {a.acao}
                  </p>
                  <Selo tom={a.cobertura === "total" ? "verde" : "ambar"}>
                    {a.cobertura === "total"
                      ? "Atende o plano da escola"
                      : "Atende em parte"}
                  </Selo>
                </div>
                <p className="mt-1 text-[12px] text-gray-500">
                  {[
                    a.responsavel,
                    a.prazo,
                    a.horizonte === "LOA"
                      ? "LOA · exercício corrente"
                      : "PPA · até quatro anos",
                    `atende ${a.escolasAtendidas} ${a.escolasAtendidas === 1 ? "escola" : "escolas"} da rede`,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </Cartao>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
