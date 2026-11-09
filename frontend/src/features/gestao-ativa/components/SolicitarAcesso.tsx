"use client";

// Fluxo 2 do acesso (requirements/acesso-gestao-ativa.md): dados → código no e-mail → pedido
// pendente. Segue os modais 1 a 3 do protótipo v2.
import { useState } from "react";

import { Modal } from "@/shared/components/Modal";

import { entrar, solicitarAcessoDiretor } from "../api";
import { LinkCaixaTeste } from "./CaixaTeste";
import { Aviso, Botao, Campo, Erro, Passos } from "./ui";

type Etapa = "dados" | "codigo" | "registrada";

export function SolicitarAcesso({ onFechar }: { onFechar: () => void }) {
  const [etapa, setEtapa] = useState<Etapa>("dados");
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [inep, setInep] = useState("");
  const [codigo, setCodigo] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviarDados(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await solicitarAcessoDiretor({ nome, email, coEntidade: Number(inep) });
      setEtapa("codigo");
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function confirmarCodigo(e: React.FormEvent) {
    e.preventDefault();
    if (!/^\d{6}$/.test(codigo)) {
      setErro("Digite os 6 dígitos do código.");
      return;
    }
    setErro(null);
    setEnviando(true);
    try {
      const resposta = await entrar(email, codigo);
      // Conta que já tinha vínculo vigente não abre outra solicitação: só confirmamos o e-mail.
      setMensagem(
        resposta.situacao === "ativo"
          ? "Este e-mail já tem acesso ativo à Gestão Ativa. Use “Já tenho acesso” para entrar."
          : resposta.mensagem,
      );
      setEtapa("registrada");
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  if (etapa === "registrada") {
    return (
      <Modal titulo="Solicitação registrada" subtitulo="Aguardando validação do vínculo" onFechar={onFechar}>
        <Passos
          passos={[
            { titulo: "Solicitação registrada", texto: `Escola INEP ${inep}.`, feito: true },
            { titulo: "E-mail confirmado", texto: "Prova o controle do canal, não o cargo.", feito: true },
            { titulo: "Vínculo em validação", texto: "A secretaria de educação confere os registros funcionais.", feito: false },
            { titulo: "Acesso liberado", texto: "Somente após a aprovação. Depois, entre com seu e-mail.", feito: false },
          ]}
        />
        <Aviso tom="atencao">{mensagem || "Enquanto a solicitação estiver pendente, a Gestão Ativa permanece bloqueada."}</Aviso>
        <div className="mt-4 flex justify-end">
          <Botao onClick={onFechar}>Entendi</Botao>
        </div>
      </Modal>
    );
  }

  if (etapa === "codigo") {
    return (
      <Modal titulo="Confirmar e-mail" subtitulo="Código de uso único" onFechar={onFechar}>
        <form onSubmit={confirmarCodigo}>
          <p className="mb-3 text-sm text-gray-600">
            Se os dados estiverem corretos, enviamos um código para <strong>{email}</strong>. Ele vale por 10 minutos.
          </p>
          <Campo
            id="codigo-solicitacao"
            rotulo="Código"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            placeholder="6 dígitos"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ""))}
            required
          />
          <Erro mensagem={erro} />
          <div className="flex justify-end gap-2">
            <Botao type="button" variante="discreto" onClick={() => setEtapa("dados")}>
              Voltar
            </Botao>
            <Botao type="submit" disabled={enviando}>
              {enviando ? "Confirmando…" : "Confirmar código"}
            </Botao>
          </div>
          <LinkCaixaTeste />
        </form>
      </Modal>
    );
  }

  return (
    <Modal titulo="Solicitar acesso de diretor" subtitulo="Gestão Ativa · primeiro acesso" onFechar={onFechar}>
      <form onSubmit={enviarDados}>
        <Campo id="nome-diretor" rotulo="Nome completo" autoComplete="name" value={nome} onChange={(e) => setNome(e.target.value)} required />
        <Campo
          id="email-diretor"
          rotulo="E-mail institucional"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Campo
          id="inep-diretor"
          rotulo="Código INEP da escola"
          inputMode="numeric"
          maxLength={8}
          ajuda="8 dígitos. Neste piloto, só escolas da rede municipal (no DF, da rede distrital)."
          value={inep}
          onChange={(e) => setInep(e.target.value.replace(/\D/g, ""))}
          required
        />
        <Aviso>
          Não pedimos cópia de documento pessoal. O código INEP sozinho não libera o acesso: o vínculo é validado pela
          secretaria municipal de educação.
        </Aviso>
        <div className="mt-4">
          <Erro mensagem={erro} />
        </div>
        <div className="flex justify-end gap-2">
          <Botao type="button" variante="discreto" onClick={onFechar}>
            Cancelar
          </Botao>
          <Botao type="submit" disabled={enviando || inep.length !== 8}>
            {enviando ? "Enviando…" : "Enviar código de confirmação"}
          </Botao>
        </div>
      </form>
    </Modal>
  );
}
