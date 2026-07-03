import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Evita que o Next.js detecte a raiz errada por causa de um package-lock.json
  // fora do projeto (ex.: em C:\Projeto\), fora do nosso controle.
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
