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
