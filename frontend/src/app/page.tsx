import { redirect } from "next/navigation";

// RN-06 de docs/business-rules/login.md: o sistema é público — a porta de entrada é o Mapa,
// não mais o Login. Só a aba Diagnóstico IA exige autenticação (gate em MunicipioClient.tsx).
export default function RootPage() {
  redirect("/mapa");
}
