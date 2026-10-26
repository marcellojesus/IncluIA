import { CaixaTeste } from "@/features/gestao-ativa/components/CaixaTeste";

// Só útil em desenvolvimento: o backend responde 404 a esta caixa fora de AMBIENTE=dev.
export default function CaixaTestePage() {
  return <CaixaTeste />;
}
