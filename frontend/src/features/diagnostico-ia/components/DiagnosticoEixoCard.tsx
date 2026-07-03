// Ver interface.md §7 "Corpo do diagnóstico" — título, análise, alerta legal, recomendações, chat.
import type { DiagnosticoEixo, RecomendacaoIA } from "../types";
import { ChatEixo } from "./ChatEixo";

const TITULO_POR_EIXO: Record<DiagnosticoEixo["eixo"], string> = {
  I: "⚖️ Eixo I — Oferta de Atendimento Educacional Especializado (AEE)",
  II: "♿ Eixo II — Acessibilidade Física",
  III: "👩‍🏫 Eixo III — Profissionais Especializados",
  IV: "🏫 Eixo IV — Inclusão em Classe Comum",
};

export function DiagnosticoEixoCard({
  diagnostico,
  codigoIbge,
  onRecomendacoesAtualizadas,
  onDiagnosticoReprocessado,
}: {
  diagnostico: DiagnosticoEixo;
  codigoIbge: number;
  onRecomendacoesAtualizadas: (eixo: DiagnosticoEixo["eixo"], recomendacoes: RecomendacaoIA[]) => void;
  onDiagnosticoReprocessado: (eixo: DiagnosticoEixo["eixo"], diagnostico: DiagnosticoEixo) => void;
}) {
  return (
    <div className="mb-5">
      <div className="mb-2 flex items-center justify-between border-b border-gov-blue-lt pb-1.5">
        <span className="text-xs font-bold uppercase tracking-wide text-gov-blue">
          {TITULO_POR_EIXO[diagnostico.eixo]}
        </span>
      </div>

      <p className="mb-2 text-sm leading-relaxed text-gray-600">{diagnostico.analise}</p>

      {diagnostico.alertaLegal && (
        <div className="my-2 rounded-r border-l-[3px] border-gov-red bg-red-50 px-3.5 py-2.5 text-xs text-red-900">
          🚨 <strong>Alerta:</strong> {diagnostico.alertaLegal}
        </div>
      )}

      {diagnostico.reprocessadoEm ? (
        <p className="mb-1 text-[11px] font-semibold text-gov-green">
          🔄 Diagnóstico reprocessado via chat em {new Date(diagnostico.reprocessadoEm).toLocaleString("pt-BR")}
        </p>
      ) : (
        diagnostico.recomendacaoAjustadaEm && (
          <p className="mb-1 text-[11px] font-semibold text-gov-green">
            ✏️ Recomendação ajustada em {new Date(diagnostico.recomendacaoAjustadaEm).toLocaleString("pt-BR")}
          </p>
        )
      )}

      {diagnostico.recomendacoes.map((rec, i) => (
        <div
          key={i}
          className="my-2 rounded-r border-l-[3px] border-gov-blue bg-gov-blue-lt px-3.5 py-2.5 text-xs text-gov-blue-dark"
        >
          💡 <strong>Recomendação:</strong> {rec.acao} — custo estimado {rec.custoEstimado}, prazo{" "}
          {rec.prazo}. Impacto estimado: {rec.impactoAlunos} alunos.{" "}
          <span className="text-gray-500">{rec.fundamentacao}</span>
        </div>
      ))}

      {diagnostico.referenciaMunicipio && (
        <p className="mt-2 text-xs text-gray-400">📍 {diagnostico.referenciaMunicipio}</p>
      )}

      <ChatEixo
        codigoIbge={codigoIbge}
        eixo={diagnostico.eixo}
        onRecomendacoesAtualizadas={(recomendacoes) =>
          onRecomendacoesAtualizadas(diagnostico.eixo, recomendacoes)
        }
        onDiagnosticoReprocessado={(novoDiagnostico) =>
          onDiagnosticoReprocessado(diagnostico.eixo, novoDiagnostico)
        }
      />
    </div>
  );
}
