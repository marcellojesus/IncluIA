// Fonte oficial e gratuita de geometria dos municípios — ver docs/business-rules/mapa.md RN-03.
//
// Nota de correção: o protótipo original (prototipo_inclua.html) chamava esta API sem o parâmetro
// `intrarregiao=municipio`. Testado diretamente contra a API real: sem esse parâmetro,
// `/malhas/estados/{uf}` devolve **1 único polígono** (o contorno do próprio estado, `codarea`
// = código da UF) — não um polígono por município. Com `intrarregiao=municipio`, devolve um
// polígono por município (`codarea` = código IBGE de 7 dígitos do município), que é o que o
// mapa coroplético precisa.

export async function fetchGeoJsonUf(codigoIbge: number): Promise<GeoJSON.FeatureCollection> {
  const res = await fetch(
    `https://servicodados.ibge.gov.br/api/v3/malhas/estados/${codigoIbge}` +
      `?formato=application%2Fvnd.geo%2Bjson&resolucao=5&intrarregiao=municipio`,
  );
  if (!res.ok) {
    throw new Error(`Falha ao carregar malha do IBGE para UF ${codigoIbge}`);
  }
  return res.json();
}
