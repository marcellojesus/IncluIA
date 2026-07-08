// Copia metodologia_score.md (fonte de verdade, na raiz do monorepo) para dentro de frontend/,
// para leitura em app/metodologia/page.tsx. Necessário porque next.config.ts fixa
// `turbopack.root` em frontend/ (workaround para um package-lock.json fora do projeto no Windows)
// — isso impede o build de acessar arquivos fora dessa raiz, o que quebrava silenciosamente o
// build de produção na Vercel (crash em "Collecting page data", sem ler o arquivo do nível acima).
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const diretorioAtual = dirname(fileURLToPath(import.meta.url));
const origem = join(diretorioAtual, "..", "..", "metodologia_score.md");
const destino = join(diretorioAtual, "..", "src", "content", "metodologia_score.md");

mkdirSync(dirname(destino), { recursive: true });
copyFileSync(origem, destino);
console.log(`metodologia_score.md sincronizado em ${destino}`);
