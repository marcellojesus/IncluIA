import { AppHeader } from "@/shared/components/AppHeader";
import { BarraAcessibilidade } from "@/shared/components/BarraAcessibilidade";
import { Footer } from "@/shared/components/Footer";
import { GeoFiltroBar } from "@/shared/components/GeoFiltroBar";

// Shell das telas públicas (Início, Escolas, Diagnóstico IA, Comparar, Dados abertos, Sobre,
// Participar) — cabeçalho com navegação + filtro geográfico fixo (Região→UF→Município) + rodapé.
// A Gestão Ativa (/gestao/*) e a Metodologia ficam fora do grupo (app), com moldura própria.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-cream">
      <BarraAcessibilidade />
      <AppHeader />
      <GeoFiltroBar />
      {/* min-h-0 é necessário: sem ele, o padrão de flexbox (min-height:auto) impede este
          div de encolher, e conteúdo mais alto que a tela fica cortado em vez de rolar. */}
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      <Footer />
    </div>
  );
}
