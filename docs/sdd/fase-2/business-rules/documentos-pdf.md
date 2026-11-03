# Regras de Negócio — Documentos em PDF

**Status:** Implementada em 2026-11-03 · valor formal sujeito a validação jurídica  
**Rastreabilidade:** RF-31 do PRD da Fase 2 · [requisitos](../requirements/documentos-pdf.md)

## RN-PDF-01 — Só versão congelada vira PDF

O PDF sai de uma versão emitida (Declaração), enviada (Plano Escolar) ou confirmada (Plano Municipal), e nunca do rascunho nem do que está na tela. Duas gerações da mesma versão têm o mesmo conteúdo; só muda a data de geração. A situação da versão aparece como estava no momento da geração: publicação, retirada e decisão da secretaria.

Versão retirada da página pública por **dado pessoal** ou **pedido de titular** não sai em PDF (409), e o Plano Escolar retirado junto com a Declaração também não. A tela continua mostrando a versão aos mesmos usuários (AD-03), mas não sai cópia portátil do que se decidiu bloquear (LGPD, art. 18; revisão do AgLGPD de 2026-11-03, A1; decisão do responsável).

## RN-PDF-02 — Quem pode baixar é quem já vê a versão

O PDF segue exatamente o acesso da tela da versão:
- o diretor baixa só os documentos da própria escola;
- o secretário baixa só os documentos das escolas e do município do próprio vínculo;
- o Plano Municipal é só do secretário.

Versão fora do escopo responde 404, como na tela. O documento não é um canal para chegar a dado que a tela não mostra (PBD-059).

## RN-PDF-03 — O texto passa de novo pelo Guardião

O texto livre já é gravado mascarado, mas antes de montar o PDF todo texto escrito por diretor ou secretário (relatos, ações, premissas, responsável, prazo, custo, comentários e apontamentos) passa outra vez pelas camadas determinísticas do Guardião LGPD (`verificar_regras`, as mesmas da `conferir_saida`). O texto do sistema (dado do Censo, nome da barreira, rótulos) não passa, porque não vem de usuário.

- Achado das camadas determinísticas (documento, contato, saúde, instrução escondida) impede o PDF. A rota responde 409 com aviso e registra no log só o tipo do achado, nunca o texto.
- A camada de nomes também roda. Nome que escapou na gravação é trocado por marcador só no arquivo, que ganha a ressalva correspondente; o PDF pode mostrar menos que a tela, nunca mais. Saúde ligada a um nome impede o PDF. O código de conferência continua sobre o conteúdo congelado.
- Não há como gerar o PDF sem essa conferência: ela roda dentro de `gerar`.

## RN-PDF-04 — Código de conferência

O código de conferência é o resumo criptográfico SHA-256 do conteúdo congelado da versão, mostrado em 12 caracteres. Entram os campos da versão e dos itens em ordem fixa. Ficam de fora a data de geração e o que muda depois (publicação, retirada, decisão e apontamentos da secretaria), para o código continuar o mesmo enquanto o conteúdo enviado for o mesmo. Ele identifica a versão impressa. Não é assinatura e não prova autoria.

## RN-PDF-05 — Ressalvas fixas

Todo PDF traz a ressalva: "Documento informativo gerado pela plataforma Escola Sem Barreiras. Não tem assinatura nem valor jurídico e não substitui atos oficiais da escola ou da secretaria." Cada documento acrescenta as suas:
- **Declaração:** os dados do Censo Escolar são da edição indicada, e as posições foram registradas pelo diretor.
- **Plano Escolar:**
  - as ações marcadas como propostas pela IA foram revisadas e aceitas pelo diretor;
  - custos são estimativas da escola;
  - as fontes legais ainda não foram validadas por especialista (questão 11 do PRD).
- **Plano Municipal:**
  - confirmar o plano não é aprovar orçamento, financiar nem executar;
  - custos são estimativas da secretaria;
  - nada aqui altera os planos das escolas.

Todo PDF também diz que a cópia não acompanha correções nem retiradas posteriores. O topo de cada página traz a marca **"Uso interno da escola e da secretaria. Contém registros sujeitos à LGPD: não divulgue."**, exceto a Declaração publicada e não retirada, que traz "Versão publicada em X. A versão oficial para o público é a da página da escola." Antes do primeiro download da sessão, a tela avisa que o arquivo sai da plataforma.

## RN-PDF-06 — Sem dado pessoal além do que a tela já mostra

O PDF não mostra nome de pessoa da plataforma: quem decidiu o Plano Escolar e quem confirmou o Plano Municipal aparecem só como "Secretaria Municipal de Educação", enquanto o documento não tiver valor formal (decisão do responsável em 2026-11-03). Também não mostra e-mail nem identificador de conta. O nome do arquivo usa só tipo, código da escola ou do município e versão, por exemplo `declaracao-obstaculos_35012345_v3.pdf`, sem nome de pessoa nem de escola.

## RN-PDF-07 — Nenhuma IA na geração

Montar o PDF não chama nenhum provedor de IA. O conteúdo é o texto gravado e as contagens vêm da versão, sem resumo nem reescrita.

## RN-PDF-08 — Auditoria e limite

Cada pedido de PDF, entregue ou recusado, entra na auditoria com a conta, o tipo e o identificador da versão e o resultado, sem conteúdo. Cada conta pode baixar até 40 PDFs a cada 10 minutos (revisão do AgLGPD, M3).
