"use client";

// Analítico de Barreiras (requirements/secretario/analitico-barreiras.md; view analytics do protótipo v2).
// Números calculados pelo sistema e síntese da IA ficam separados (RN-SAB-02 e 03); a IA não propõe ações
// aqui: cada barreira leva ao Plano Estratégico Municipal (decisão de 2026-10-27).
import { useEffect, useState } from "react";

import { formatarMatriculasEsp } from "@/shared/lib/formatters";

import { gerarSinteseAnalitica, getAnalitico } from "../api";
import { ESTADOS_VERSAO_PLANO, POSICOES } from "../rotulos";
import type { AchadoAnalitico, Analitico, BarreiraAnalitica } from "../types";
import { Aviso, Botao, Cartao, Erro, Selo } from "./ui";

const inteiro = (valor: number) => valor.toLocaleString("pt-BR");
const porcento = (parte: number, total: number) => (total ? `${Math.round((100 * parte) / total)}%` : "—");

const TIPOS: Record<AchadoAnalitico["tipo"], { texto: string; tom: "azul" | "ambar" | "verde" }> = {
  observacao: { texto: "Observação", tom: "azul" },
  hipotese: { texto: "Hipótese", tom: "ambar" },
  recomendacao: { texto: "Recomendação", tom: "verde" },
};

export function AnaliticoBarreiras({ onPlanejar }: { onPlanejar: (codigo: string) => void }) {
  const [dados, setDados] = useState<Analitico | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [gerando, setGerando] = useState(false);
  const [aberta, setAberta] = useState<string | null>(null);

  useEffect(() => {
    getAnalitico().then(setDados).catch((falha) => setErro((falha as Error).message));
  }, []);

  async function atualizar() {
    setGerando(true);
    setErro(null);
    try {
      setDados(await gerarSinteseAnalitica());
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setGerando(false);
    }
  }

  if (!dados) {
    return erro ? <Erro mensagem={erro} /> : <p role="status" className="mt-10 text-center text-sm text-gray-500">Carregando o analítico da rede…</p>;
  }

  const total = dados.escolasMunicipais;

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Numero valor={dados.comDeclaracao} base={`de ${inteiro(total)} escolas`} titulo="Com Declaração emitida" />
        <Numero valor={dados.comPlano} base={`de ${inteiro(total)} escolas`} titulo="Com Plano de Ação enviado" />
        <Numero valor={dados.altaRecorrencia} base="barreiras em 90% ou mais das escolas" titulo="Alta recorrência na rede" />
        <Numero valor={dados.alunos} base={`matrículas da educação especial · Censo ${dados.censoVersao ?? ""}`} titulo="Alunos na rede" />
      </div>
      <p className="text-[13px] text-gray-600">
        Contagens calculadas por regra, a partir do Censo, das Declarações emitidas e dos planos enviados. Escola sem Declaração ou sem
        plano aparece como sem registro, não como escola sem dificuldade.
      </p>

      <SinteseIA dados={dados} gerando={gerando} onAtualizar={atualizar} erro={erro} />

      <section aria-labelledby="titulo-barreiras-rede">
        <div className="flex flex-wrap items-center gap-3">
          <h2 id="titulo-barreiras-rede" className="text-lg font-extrabold text-gov-blue-dark">Barreiras da rede</h2>
          <Selo tom="teal">Métrica calculada · Censo {dados.censoVersao}</Selo>
        </div>
        <p className="mt-1 text-[13px] text-gray-600">
          Da barreira que atinge mais alunos da educação especial para a que atinge menos (soma das matrículas das escolas com a barreira).
        </p>
        <ol className="mt-3 space-y-2">
          {dados.barreiras.map((b) => (
            <LinhaBarreira
              key={b.codigo}
              barreira={b}
              total={total}
              aberta={aberta === b.codigo}
              onAlternar={() => setAberta(aberta === b.codigo ? null : b.codigo)}
              onPlanejar={() => onPlanejar(b.codigo)}
            />
          ))}
        </ol>
      </section>
    </div>
  );
}

function Numero({ valor, base, titulo }: { valor: number; base: string; titulo: string }) {
  return (
    <Cartao className="p-4">
      <div className="text-[12px] font-bold text-gray-600">{titulo}</div>
      <div className="mt-1 text-3xl font-extrabold text-gov-blue-dark">{inteiro(valor)}</div>
      <div className="mt-0.5 text-[12px] text-gray-500">{base}</div>
    </Cartao>
  );
}

function SinteseIA({ dados, gerando, onAtualizar, erro }: { dados: Analitico; gerando: boolean; onAtualizar: () => void; erro: string | null }) {
  const sintese = dados.sintese;
  const semRegistros = dados.comDeclaracao === 0 && dados.comPlano === 0;
  return (
    <Cartao className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-extrabold text-gov-blue-dark">
            Síntese assistida por IA <Selo tom="ambar">Hipóteses para análise</Selo>
          </h2>
          <p className="mt-1 max-w-3xl text-[13px] text-gray-600">
            O assistente lê as contagens e os resumos das posições das escolas, sem nomes de escolas nem do município, e separa observação,
            hipótese e recomendação. Não é veredito: confira as evidências antes de decidir.
          </p>
        </div>
        <Botao variante={sintese ? "contorno" : "primario"} onClick={onAtualizar} disabled={gerando}>
          {gerando ? "Analisando a rede…" : sintese ? "Atualizar análise" : "Gerar análise"}
        </Botao>
      </div>
      <div className="mt-3">
        <Erro mensagem={erro} />
        {dados.avisoGuardiao && <Aviso tom="atencao">{dados.avisoGuardiao}</Aviso>}
      </div>

      {!sintese ? (
        <p className="mt-3 text-[13px] text-gray-600">
          {semRegistros
            ? "Nenhuma escola emitiu Declaração ou enviou plano ainda. A análise pode ser gerada só com o Censo, mas dirá pouco sobre os obstáculos."
            : "Nenhuma análise gerada ainda."}
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          <p className="text-[12px] text-gray-500">
            Gerada em {new Date(sintese.geradaEm).toLocaleString("pt-BR")} por {sintese.modelo}.
            {sintese.relatosFora > 0 && ` ${sintese.relatosFora} resumo(s) com dado sensível não foram ao assistente.`}
          </p>
          {sintese.desatualizada && (
            <Aviso tom="atencao">Há Declarações ou planos novos desde esta análise. Atualize para incluí-los.</Aviso>
          )}
          <ul className="space-y-2">
            {sintese.achados.map((a, i) => (
              <li key={i} className="rounded-lg border border-black/5 bg-white p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Selo tom={TIPOS[a.tipo].tom}>{TIPOS[a.tipo].texto}</Selo>
                  {a.barreiras.map((c) => (
                    <span key={c} className="text-[11px] font-bold text-gray-500">{c}</span>
                  ))}
                </div>
                <p className="mt-1.5 text-[14px] text-ink">{a.texto}</p>
                {a.evidencias.length > 0 && (
                  <p className="mt-1 text-[12px] text-gray-500">
                    Base: {a.evidencias.map((e) => `${e.escola} (${e.codigo})`).join("; ")}
                  </p>
                )}
              </li>
            ))}
          </ul>
          {sintese.limitacoes.length > 0 && (
            <div className="text-[12px] text-gray-600">
              <strong>Limitações apontadas:</strong> {sintese.limitacoes.join(" ")}
            </div>
          )}
        </div>
      )}
    </Cartao>
  );
}

function LinhaBarreira({
  barreira: b,
  total,
  aberta,
  onAlternar,
  onPlanejar,
}: {
  barreira: BarreiraAnalitica;
  total: number;
  aberta: boolean;
  onAlternar: () => void;
  onPlanejar: () => void;
}) {
  return (
    <li>
      <Cartao className="p-4">
        <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold text-gray-500">{b.codigo} · Eixo {b.eixo}</span>
              {b.altaRecorrencia && <Selo tom="vermelho">Alta recorrência</Selo>}
            </div>
            <h3 className="mt-0.5 text-[15px] font-extrabold text-ink">{b.nome}</h3>
            <p className="mt-1 text-[13px] text-gray-600">
              <strong>{formatarMatriculasEsp(b.alunos)}</strong> alunos da educação especial em <strong>{inteiro(b.escolas)}</strong> de {inteiro(total)} escolas (
              {porcento(b.escolas, total)}){b.nota && ` · ${b.nota}`}
            </p>
            <p className="mt-1 text-[12px] text-gray-500">
              Declarações: {b.obstaculos} obstáculo(s), {b.divergencias} divergência(s), {b.semRelato} sem relato
              {b.comDeclaracao < b.escolas && ` · ${b.escolas - b.comDeclaracao} escola(s) sem registro emitido`} · Planos enviados com ação:{" "}
              {b.comAcao} ({b.comAcaoAceita} aceitos)
            </p>
          </div>
          <div className="flex flex-wrap gap-2 md:justify-end">
            <Botao variante="discreto" onClick={onAlternar} aria-expanded={aberta} disabled={b.evidencias.length === 0}>
              {b.evidencias.length === 0 ? "Sem registros" : aberta ? "Ocultar evidências" : `Ver evidências (${b.evidencias.length})`}
            </Botao>
            <Botao variante="contorno" onClick={onPlanejar}>
              Planejar no plano municipal →
            </Botao>
          </div>
        </div>
        {aberta && (
          <ul className="mt-3 divide-y divide-black/5 border-t border-black/5">
            {b.evidencias.map((e) => (
              <li key={e.coEntidade} className="py-2.5 text-[13px]">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-ink">{e.escola}</strong>
                  {e.posicao ? <Selo tom={POSICOES[e.posicao].tom}>{POSICOES[e.posicao].texto}</Selo> : <Selo tom="neutro">Sem Declaração emitida</Selo>}
                  {e.planoEstado && <Selo tom={ESTADOS_VERSAO_PLANO[e.planoEstado].tom}>Plano: {ESTADOS_VERSAO_PLANO[e.planoEstado].texto}</Selo>}
                </div>
                {e.resumo && <p className="mt-1 text-gray-700">{e.resumo}</p>}
                {e.acoes.length > 0 && (
                  <ul className="mt-1 list-disc pl-5 text-[12px] text-gray-600">
                    {e.acoes.map((acao, i) => (
                      <li key={i}>{acao}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </Cartao>
    </li>
  );
}
