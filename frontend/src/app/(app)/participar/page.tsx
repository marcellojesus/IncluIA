import { PaginaEmConstrucao } from "@/shared/components/PaginaEmConstrucao";

export default function ParticiparPage() {
  return (
    <PaginaEmConstrucao
      titulo="Registrar uma barreira"
      descricao="Faltou intérprete de Libras, material em Braille, vaga em classe comum ou acessibilidade física? Em breve, seu registro vira dado público e gera alerta aos órgãos de controle."
      specs={[
        "Formulário de registro (escola, tipo de barreira, descrição)",
        "Geração de protocolo público e acompanhamento de status",
        "Lista de barreiras registradas por escola/município",
        "Encaminhamento a Conselhos, Ministério Público e Defensoria",
        "Backend de denúncias — ainda não existe",
      ]}
    />
  );
}
