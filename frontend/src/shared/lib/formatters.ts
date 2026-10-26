export function formatarNumero(valor: number): string {
  return valor.toLocaleString("pt-BR");
}

// Ex.: 2458159 -> "2,46M" — usado nas estatísticas de impacto (ver interface.md §2).
export function formatarCompacto(valor: number): string {
  if (valor >= 1_000_000) {
    return `${(valor / 1_000_000).toFixed(2).replace(".", ",")}M`;
  }
  return formatarNumero(valor);
}

// Supressão de célula pequena (decisão de 2026-10-25, pendência 13 da arquitetura): na tela
// pública, de 1 a 4 matrículas da educação especial aparecem como "menos de 5". Ao lado da
// Declaração publicada pela escola, o número exato ajudaria a identificar uma criança. Mesma regra
// de backend/app/shared/contexto_ia/barreiras.py (LIMIAR_CELULA_PEQUENA).
export const LIMIAR_CELULA_PEQUENA = 5;

export function formatarMatriculasEsp(quantidade: number): string {
  return quantidade > 0 && quantidade < LIMIAR_CELULA_PEQUENA ? `menos de ${LIMIAR_CELULA_PEQUENA}` : String(quantidade);
}
