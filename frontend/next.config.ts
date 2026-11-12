import path from "node:path";
import type { NextConfig } from "next";

// Raiz real do monorepo (um nível acima de frontend/) — evita que o Next.js precise adivinhar
// sozinho por causa de lockfiles, o que pode escolher raízes diferentes em ambientes diferentes
// (ex.: um package-lock.json solto em C:\Projeto\, no Windows local, fora do nosso controle,
// vs. o build Linux limpo da Vercel) e causar falhas de build sem mensagem de erro clara.
// `turbopack.root` e `outputFileTracingRoot` precisam apontar para o mesmo lugar.
const raizDoMonorepo = path.join(__dirname, "..");

const nextConfig: NextConfig = {
  turbopack: {
    root: raizDoMonorepo,
  },
  outputFileTracingRoot: raizDoMonorepo,
  // /documentacao: página HTML avulsa em public/documentacao/, sem link a partir do sistema.
  async rewrites() {
    return [{ source: "/documentacao", destination: "/documentacao/index.html" }];
  },
};

export default nextConfig;
