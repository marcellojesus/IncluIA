import { AppHeader } from "@/shared/components/AppHeader";
import { Footer } from "@/shared/components/Footer";
import { GovTopBar } from "@/shared/components/GovTopBar";

// Shell das telas pós-login (Mapa, Município) — ver interface.md §0. A tela de Login não usa
// este layout (só tem o GovTopBar, sem o AppHeader com usuário/logout).
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <GovTopBar />
      <AppHeader />
      {/* min-h-0 é necessário: sem ele, o padrão de flexbox (min-height:auto) impede este
          div de encolher, e conteúdo mais alto que a tela fica cortado em vez de rolar. */}
      <div className="min-h-0 flex-1 overflow-hidden">{children}</div>
      <Footer />
    </div>
  );
}
