"use client";

// Modais da Declaração de Obstáculos (protótipo v2): revisar obstáculo, divergência, declaração
// consolidada e versão emitida. Textos do diretor passam pelo Guardião LGPD no servidor; a tela
// mostra o texto como ficou gravado (com marcadores como [NOME]).
import Link from "next/link";
import { useEffect, useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { emitirDeclaracao, getPreviaPublica, publicarDeclaracao, registrarPosicao, retirarPublicacao } from "../api";
import { NOMES_EIXOS, POSICOES, dataCurta } from "../rotulos";
import type { BarreiraDeclaracao, EstadoDeclaracao, PreviaPublica, VersaoDeclaracao } from "../types";
import { Aviso, Botao, CampoTexto, Erro, Passos, Selecao, Selo } from "./ui";

const AVISO_DADOS = "Não inclua nomes nem dados que identifiquem estudantes ou profissionais. O texto passa por um filtro antes de ser gravado.";

export function RevisarObstaculo({
  barreira,
  escola,
  relato,
  proposta,
  onFechar,
  onRegistrado,
}: {
  barreira: BarreiraDeclaracao;
  escola: string;
  relato: string;
  proposta: { texto: string; resumo: string };
  onFechar: () => void;
  onRegistrado: (estado: EstadoDeclaracao) => void;
}) {
  const [texto, setTexto] = useState(proposta.texto);
  const [resumo, setResumo] = useState(proposta.resumo);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function confirmar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      onRegistrado(await registrarPosicao(barreira.codigo, { posicao: "obstaculo", texto, resumo: resumo || null }));
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo="Revisar obstáculo formalizado" subtitulo={`${barreira.codigo} · ${barreira.nome}`} onFechar={onFechar}>
      <form onSubmit={confirmar}>
        <Aviso>
          <strong>Barreira (Censo):</strong> {barreira.dadoCenso}
          <br />
          <strong>Escola:</strong> {escola}
        </Aviso>
        {relato && (
          <div className="mt-3 rounded-lg bg-black/[.03] p-3">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-gray-500">Seu relato original</div>
            <p className="mt-1 whitespace-pre-line text-[13px] text-gray-700">{relato}</p>
          </div>
        )}
        <div className="mt-3">
          <CampoTexto
            id="texto-obstaculo"
            rotulo={proposta.texto ? "Texto formal proposto pela IA · factual e neutro · edite antes de confirmar" : "Texto formal do obstáculo"}
            rows={6}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="A gestão escolar relata que…"
            ajuda={AVISO_DADOS}
            required
          />
          <CampoTexto
            id="resumo-obstaculo"
            rotulo="Resumo do obstáculo (aparece no dashboard)"
            rows={2}
            maxLength={300}
            value={resumo}
            onChange={(e) => setResumo(e.target.value)}
          />
        </div>
        <p className="mb-3 text-[12px] text-gray-500">O relato original e o texto confirmado ficam guardados com autoria e data.</p>
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>
            Voltar à conversa
          </Botao>
          <Botao type="submit" disabled={enviando || texto.trim().length < 10}>
            {enviando ? "Registrando…" : "Confirmar obstáculo"}
          </Botao>
        </div>
      </form>
    </Modal>
  );
}

export function Divergencia({
  barreira,
  onFechar,
  onRegistrado,
}: {
  barreira: BarreiraDeclaracao;
  onFechar: () => void;
  onRegistrado: (estado: EstadoDeclaracao) => void;
}) {
  const [texto, setTexto] = useState(barreira.posicao === "divergencia" ? barreira.texto ?? "" : "");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function registrar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      onRegistrado(await registrarPosicao(barreira.codigo, { posicao: "divergencia", texto }));
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo="Divergência com o dado do Censo" subtitulo={`${barreira.codigo} · ${barreira.nome}`} onFechar={onFechar}>
      <form onSubmit={registrar}>
        <p className="mb-3 text-[13px] text-gray-600">
          <strong>Dado do Censo:</strong> {barreira.dadoCenso}
        </p>
        <CampoTexto
          id="texto-divergencia"
          rotulo="Qual é a realidade da escola?"
          rows={4}
          placeholder="Ex.: a sala existe desde 2024, mas não foi declarada no Censo."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          ajuda={AVISO_DADOS}
          required
        />
        <p className="mb-3 text-[12px] text-gray-500">Não altera o dado do Censo, o score nem a faixa.</p>
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando || texto.trim().length < 10}>
            {enviando ? "Registrando…" : "Registrar divergência"}
          </Botao>
        </div>
      </form>
    </Modal>
  );
}

export function ListaPorEixo({ itens }: { itens: { codigo: string; eixo: string; nome: string; dadoCenso: string; posicao: BarreiraDeclaracao["posicao"]; texto: string | null }[] }) {
  const eixos = [...new Set(itens.map((i) => i.eixo))];
  return (
    <div className="space-y-4">
      {eixos.map((eixo) => (
        <section key={eixo}>
          <h3 className="text-[12px] font-extrabold uppercase tracking-wider text-gov-blue-dark">
            Eixo {eixo} · {NOMES_EIXOS[eixo]}
          </h3>
          <ul className="mt-2 space-y-2">
            {itens
              .filter((i) => i.eixo === eixo)
              .map((i) => (
                <li key={i.codigo} className="rounded-lg border border-black/5 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[13px] font-bold text-ink">{i.nome}</span>
                    <Selo tom={POSICOES[i.posicao].tom}>{POSICOES[i.posicao].texto}</Selo>
                  </div>
                  <div className="mt-0.5 text-[12px] text-gray-500">Censo: {i.dadoCenso}</div>
                  {i.texto && <p className="mt-1 text-[13px] text-gray-700">{i.texto}</p>}
                </li>
              ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

export function DeclaracaoConsolidada({
  estado,
  onFechar,
  onEmitida,
  onPublicar,
  onRetirar,
}: {
  estado: EstadoDeclaracao;
  onFechar: () => void;
  onEmitida: (versao: VersaoDeclaracao) => void;
  onPublicar: (numero: number) => void;
  onRetirar: (numero: number) => void;
}) {
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const ultima = estado.versoes.at(-1);
  const comPosicao = estado.barreiras.length - estado.faltam;

  async function emitir() {
    setErro(null);
    setEnviando(true);
    try {
      onEmitida(await emitirDeclaracao());
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo="Declaração de Obstáculos" subtitulo={`${estado.escola} · ${comPosicao} de ${estado.barreiras.length} barreiras com posição`} onFechar={onFechar}>
      <Aviso>
        Ao emitir, esta versão fica congelada com sua autoria e data, passa a ser visível à secretaria municipal e serve de base para o
        Plano de Ação. Os dados do Censo e o score não mudam.
      </Aviso>
      <div className="mt-4 max-h-[45vh] overflow-y-auto pr-1">
        <ListaPorEixo itens={estado.barreiras} />
      </div>
      <p className="mt-3 text-[12px] text-gray-500">
        {ultima
          ? `Última versão emitida: v${ultima.versao} em ${dataCurta(ultima.emitidaEm)}${
              ultima.retiradaEm ? `, retirada da página pública em ${dataCurta(ultima.retiradaEm)}` : ultima.publicadaEm ? `, publicada em ${dataCurta(ultima.publicadaEm)}` : ", não publicada"
            }${estado.haAlteracoes ? ". Há alterações desde então." : "."}`
          : "Nenhuma versão emitida ainda."}
      </p>
      <div className="mt-3">
        <Erro mensagem={erro} />
      </div>
      <div className="flex flex-wrap justify-end gap-2">
        <Botao variante="discreto" onClick={onFechar}>
          Continuar registrando
        </Botao>
        {ultima && !ultima.publicadaEm && !estado.haAlteracoes && (
          <Botao variante="contorno" onClick={() => onPublicar(ultima.versao)}>
            Publicar versão v{ultima.versao}
          </Botao>
        )}
        {ultima && ultima.publicadaEm && !ultima.retiradaEm && (
          <Botao variante="perigo" onClick={() => onRetirar(ultima.versao)}>
            Retirar v{ultima.versao} da página pública
          </Botao>
        )}
        {estado.faltam > 0 ? (
          <Botao variante="coral" disabled>
            Faltam {estado.faltam} {estado.faltam === 1 ? "barreira" : "barreiras"} sem posição
          </Botao>
        ) : (
          <Botao variante="coral" onClick={emitir} disabled={enviando || !estado.podeEmitir}>
            {enviando ? "Emitindo…" : estado.podeEmitir ? `Emitir declaração v${(ultima?.versao ?? 0) + 1}` : "Sem alterações para emitir"}
          </Botao>
        )}
      </div>
    </Modal>
  );
}

export function VersaoEmitida({ versao, onFechar, onPublicar }: { versao: VersaoDeclaracao; onFechar: () => void; onPublicar: () => void }) {
  return (
    <Modal titulo={`Declaração v${versao.versao} emitida`} subtitulo={`${versao.escola} · ${dataCurta(versao.emitidaEm)}`} onFechar={onFechar}>
      <Passos
        passos={[
          { titulo: "Emitida e congelada", texto: `Versão ${versao.versao}, com sua autoria e data. Mudanças futuras geram nova versão.`, feito: true },
          { titulo: "Visível à secretaria da rede", texto: "A secretaria municipal passa a consultar esta versão.", feito: true },
          { titulo: "Base para o Plano de Ação", texto: "O Plano de Ação da escola usará esta versão como contexto.", feito: true },
        ]}
      />
      <Aviso tom="atencao">A versão ainda não é pública. Publique quando quiser, depois da checagem de dados pessoais.</Aviso>
      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <Botao variante="discreto" onClick={onFechar}>Fechar</Botao>
        <Botao variante="contorno" onClick={onPublicar}>Publicar agora</Botao>
        <Link
          href="/gestao/diretor/plano"
          className="inline-flex items-center rounded-lg bg-accent px-4 py-2 text-sm font-bold text-white hover:bg-accent-dark"
        >
          Ir para o Plano de Ação →
        </Link>
      </div>
    </Modal>
  );
}

export function PublicarDeclaracao({ numero, onFechar, onPublicada }: { numero: number; onFechar: () => void; onPublicada: () => void }) {
  const [previa, setPrevia] = useState<PreviaPublica | null>(null);
  const [aprovado, setAprovado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    getPreviaPublica(numero).then(setPrevia).catch((falha) => setErro((falha as Error).message));
  }, [numero]);

  async function publicar() {
    setErro(null);
    setEnviando(true);
    try {
      await publicarDeclaracao(numero);
      onPublicada();
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo={`Publicar Declaração v${numero}`} subtitulo="Versão pública · prévia" onFechar={onFechar}>
      {!previa ? (
        erro ? <Erro mensagem={erro} /> : <p role="status" className="text-sm text-gray-500">Preparando a versão pública…</p>
      ) : (
        <>
          {previa.pontos.length > 0 ? (
            <Aviso tom="atencao">
              <strong>Checagem de dados pessoais: {previa.pontos.length} {previa.pontos.length === 1 ? "ponto" : "pontos"} para revisar.</strong>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {previa.pontos.map((p, i) => (
                  <li key={`${p.codigo}-${i}`}>
                    <strong>{p.barreira}:</strong> {p.mensagem}
                  </li>
                ))}
              </ul>
            </Aviso>
          ) : (
            <Aviso>A checagem não encontrou possível dado pessoal. Mesmo assim, leia a versão pública antes de aprovar.</Aviso>
          )}

          <h3 className="mt-4 text-[12px] font-extrabold uppercase tracking-wider text-gray-500">Como o público verá</h3>
          <div className="mt-2 max-h-[40vh] space-y-2 overflow-y-auto pr-1">
            {previa.itens.map((item) => (
              <div key={item.codigo} className="rounded-lg border border-black/5 p-3">
                <div className="text-[13px] font-bold text-ink">{item.barreira}</div>
                <div className="text-[12px] text-gray-500">Censo: {item.dadoCenso}</div>
                <p className="mt-1 text-[13px] text-gray-700">{item.textoPublico}</p>
              </div>
            ))}
          </div>

          <label className="mt-4 flex items-start gap-2 text-[13px] text-ink">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 accent-[#0e7c6b]"
              checked={aprovado}
              disabled={!previa.podePublicar}
              onChange={(e) => setAprovado(e.target.checked)}
            />
            <span>
              Revisei a versão pública e aprovo a publicação.
              <span className="block text-[12px] text-gray-500">Para mudar um texto, retifique a posição e emita nova versão.</span>
            </span>
          </label>
          <div className="mt-3">
            <Erro mensagem={erro} />
          </div>
          <div className="flex justify-end gap-2">
            <Botao variante="discreto" onClick={onFechar}>Não publicar agora</Botao>
            <Botao variante="coral" onClick={publicar} disabled={!previa.podePublicar || !aprovado || enviando}>
              {enviando ? "Publicando…" : "Publicar na página da escola"}
            </Botao>
          </div>
        </>
      )}
    </Modal>
  );
}

export const MOTIVOS_RETIRADA = [
  { valor: "decisao_da_escola", texto: "Decisão da escola" },
  { valor: "dado_pessoal", texto: "Encontrei dado pessoal no texto publicado" },
  { valor: "erro_de_conteudo", texto: "Erro de conteúdo" },
  { valor: "outro", texto: "Outro" },
];

export function RetirarPublicacao({ numero, onFechar, onRetirada }: { numero: number; onFechar: () => void; onRetirada: () => void }) {
  const [motivo, setMotivo] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function retirar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await retirarPublicacao(numero, motivo);
      onRetirada();
    } catch (falha) {
      setErro((falha as Error).message);
      setEnviando(false);
    }
  }

  return (
    <Modal titulo={`Retirar a Declaração v${numero} da página pública`} subtitulo="A versão emitida continua guardada" onFechar={onFechar}>
      <form onSubmit={retirar}>
        <p className="mb-3 text-[13px] text-gray-600">
          A versão sai da página pública da escola na hora. Ela continua guardada e visível à secretaria municipal. Para voltar a publicar,
          emita e publique uma nova versão.
        </p>
        <Selecao id="motivo-retirada" rotulo="Motivo" opcoes={MOTIVOS_RETIRADA} value={motivo} onChange={(e) => setMotivo(e.target.value)} required />
        <Erro mensagem={erro} />
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>Cancelar</Botao>
          <Botao type="submit" variante="perigo" disabled={!motivo || enviando}>{enviando ? "Retirando…" : "Retirar da página pública"}</Botao>
        </div>
      </form>
    </Modal>
  );
}
