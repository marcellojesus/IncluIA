// Copia as metodologias publicadas (fontes de verdade, na raiz do monorepo) para dentro de frontend/,
// para leitura em app/metodologia/. Necessário porque next.config.ts fixa
// `turbopack.root` em frontend/ (workaround para um package-lock.json fora do projeto no Windows)
// — isso impede o build de acessar arquivos fora dessa raiz, o que quebrava silenciosamente o
// build de produção na Vercel (crash em "Collecting page data", sem ler o arquivo do nível acima).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const diretorioAtual = dirname(fileURLToPath(import.meta.url));
const ARQUIVOS = ["metodologia_score.md", "metodologia_barreiras.md"];

for (const arquivo of ARQUIVOS) {
  const origem = join(diretorioAtual, "..", "..", arquivo);
  const destino = join(diretorioAtual, "..", "src", "content", arquivo);
  mkdirSync(dirname(destino), { recursive: true });
  copyFileSync(origem, destino);
  console.log(`${arquivo} sincronizado em ${destino}`);
}
