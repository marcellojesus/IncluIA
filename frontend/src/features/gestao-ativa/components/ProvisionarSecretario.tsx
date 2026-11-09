"use client";

// Fluxo 1 do acesso (RF-06): a equipe do produto habilita o secretário municipal depois de
// confirmar a função por canal institucional. Não existe cadastro público de secretário.
import { useState } from "react";

import { provisionarSecretario } from "../api";
import { AVISO_TEXTO_LIVRE, Aviso, Botao, Cartao, Campo, CampoTexto, Erro, MOTIVOS, Selecao } from "./ui";

export function ProvisionarSecretario() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [municipio, setMunicipio] = useState("");
  const [metodo, setMetodo] = useState("");
  const [categoria, setCategoria] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    setEnviando(true);
    try {
      const resposta = await provisionarSecretario({ nome, email, coMunicipio: Number(municipio), categoria, metodoVerificacao: metodo });
      setSucesso(resposta.mensagem);
      setNome("");
      setEmail("");
      setMunicipio("");
      setMetodo("");
      setCategoria("");
    } catch (falha) {
      setErro((falha as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-6">
      <p className="text-xs font-extrabold uppercase tracking-wider text-accent">Administração</p>
      <h1 className="mt-1 text-3xl font-extrabold text-gov-blue-dark">Habilitar secretaria municipal</h1>
      <p className="mt-2 text-[15px] text-gray-600">
        Use contatos obtidos por canal institucional independente, não os informados por quem pediu o acesso.
      </p>
      <Cartao className="mt-5 p-5">
        <form onSubmit={enviar}>
          <Campo id="sec-nome" rotulo="Nome completo" value={nome} onChange={(e) => setNome(e.target.value)} required />
          <Campo id="sec-email" rotulo="E-mail institucional" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Campo
            id="sec-municipio"
            rotulo="Código IBGE do município"
            inputMode="numeric"
            maxLength={7}
            ajuda="7 dígitos. O acesso fica limitado à rede municipal deste município. No DF, use 5300108 (Brasília): o acesso é à rede distrital."
            value={municipio}
            onChange={(e) => setMunicipio(e.target.value.replace(/\D/g, ""))}
            required
          />
          <Selecao id="sec-categoria" rotulo="Como a função foi confirmada" opcoes={MOTIVOS.provisionar} value={categoria} onChange={(e) => setCategoria(e.target.value)} required />
          <CampoTexto
            id="sec-metodo"
            rotulo="Referência da confirmação"
            ajuda={`Detalhe a referência, por exemplo o número do ofício. ${AVISO_TEXTO_LIVRE}`}
            value={metodo}
            onChange={(e) => setMetodo(e.target.value)}
            required
            minLength={5}
          />
          <Erro mensagem={erro} />
          {sucesso && <div className="mb-3"><Aviso>{sucesso}</Aviso></div>}
          <Botao type="submit" disabled={enviando || municipio.length !== 7 || !categoria}>
            {enviando ? "Habilitando…" : "Habilitar e enviar código"}
          </Botao>
        </form>
      </Cartao>
    </div>
  );
}
