# Requisitos — Documentos em PDF

**Status:** Implementado em 2026-11-03  
**PRD:** RF-31 · **Regras:** [documentos-pdf](../business-rules/documentos-pdf.md)

## Objetivo

Permitir que diretor e secretário baixem, em Formato de Documento Portátil (PDF), uma versão já congelada da Declaração de Obstáculos, do Plano de Ação Escolar ou do Plano Estratégico Municipal. O documento serve para levar a reuniões, anexar a processos internos e arquivar. No piloto ele é **informativo**: não tem assinatura nem valor jurídico.

## Decisões tomadas (2026-11-03)

- **Documentos desta entrega:** Declaração de Obstáculos (versão emitida), Plano de Ação Escolar (versão enviada) e Plano Estratégico Municipal (versão confirmada).
- **Fora desta entrega:**
  - o PDF na página pública;
  - o PDF das ações municipais na visão do diretor.
- **Valor formal (questão 16 do PRD, parcialmente resolvida):** documento informativo com ressalvas. Traz versão, datas, quem confirmou e um código de conferência, mas não tem assinatura. A assinatura digital (ICP-Brasil ou gov.br) fica para depois da validação jurídica.
- **Geração:** no backend, a partir da versão gravada. Nunca a partir da tela nem de rascunho.
- **Narrativa executiva (RF-30), decidida depois da pendência 16 da arquitetura:** PDF próprio, feito para quem decide o orçamento e com marca própria; a edição do secretário com número ou nome da rede não é salva (RN-PDF-09).

## Requisitos funcionais

- **PDF-RF-01:** gerar o PDF de uma versão emitida da Declaração de Obstáculos, para o diretor da escola e para o secretário do município da escola.
  - **Aceite:**
    - traz, por barreira, o eixo, a barreira, o dado do Censo, os pontos, a posição (obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão) e o texto confirmado;
    - traz as edições do Censo e da metodologia da versão;
    - informa a situação da publicação: não publicada, publicada em data X ou publicação retirada em data X. O motivo da retirada não aparece.
- **PDF-RF-02:** gerar o PDF de uma versão enviada do Plano de Ação Escolar, para o diretor da escola e para o secretário do município da escola.
  - **Aceite:**
    - traz as ações por barreira, com relação ao obstáculo, responsável, prazo, horizonte LOA/PPA, custo estimado, premissas e fontes legíveis (ex.: "Lei 13.146/2015 (LBI), Art. 28, XII");
    - marca a origem de cada ação: proposta pela IA, proposta pela IA e editada, ou escrita pelo diretor;
    - traz a versão da Declaração usada como base e avisa se já existe Declaração emitida mais nova;
    - traz a situação da análise (aguardando análise, aceito, ajustes solicitados ou reprovado), com data, comentário e apontamentos da secretaria, quando houver.
- **PDF-RF-03:** gerar o PDF de uma versão confirmada do Plano Estratégico Municipal, só para o secretário do município.
  - **Aceite:**
    - traz as ações da rede com barreiras, prioridade, responsável, prazo, horizonte, custo estimado, premissas, fontes, origem e as escolas atendidas com cobertura total ou parcial;
    - traz os planos escolares usados como base (escola e versão);
    - diz que confirmar o plano não é aprovar orçamento, financiar nem executar (SPM-RF-08).
- **PDF-RF-07:** gerar o PDF da narrativa executiva de uma versão confirmada do Plano Estratégico Municipal, só para o secretário do município.
  - **Aceite:**
    - traz os números calculados pelo sistema, resumo, situação da rede, estratégia por frente, fundamentação legal com as fontes, próximos passos e incertezas;
    - diz se o texto foi revisado pela secretaria ou é do assistente sem revisão;
    - as ações citadas aparecem só pela linha estruturada, sem texto livre, valor de custo nem escolas;
    - é recusado quando o texto gravado tem número ou nome da rede (RN-PDF-09).
- **PDF-RF-04:** todo PDF traz:
  - um cabeçalho com o tipo de documento, a escola ou o município, a versão e a data da versão;
  - a data da decisão ou da confirmação, com o papel (Secretaria Municipal de Educação), sem nome de pessoa (RN-PDF-06);
  - a marca de uso interno, ou de versão publicada, no topo de cada página (RN-PDF-05);
  - a data e a hora em que o arquivo foi gerado;
  - o código de conferência;
  - um rodapé com "página X de Y" e as ressalvas da RN-PDF-05.
- **PDF-RF-05:** a tela de cada versão (diretor e secretário) mostra o botão "Baixar PDF". O botão só aparece quando a versão permite gerar o arquivo.
- **PDF-RF-06:** o PDF é acessível ao leitor de tela:
  - texto real, nunca imagem de texto;
  - idioma pt-BR e título nos metadados;
  - ordem de leitura igual à visual;
  - contraste mínimo de 4,5:1;
  - posição e situação escritas por extenso, não só por cor.

## Requisitos não funcionais

- **PDF-RNF-01:** gerar o PDF sem chamar a IA e sem acesso à internet.
- **PDF-RNF-02:** biblioteca Python pura (`fpdf2`), sem dependências do sistema, para rodar igual no Windows e no deploy. A fonte TrueType vai junto no repositório, com licença livre (Noto Sans, licença OFL), para cobrir os acentos e a pontuação do português.
- **PDF-RNF-03:** gerar um plano municipal de 50 ações em menos de 3 segundos.
- **PDF-RNF-04:** o arquivo é gerado sob demanda e não é guardado no servidor. A resposta sai com `Cache-Control: no-store`.

## Rotas previstas

| Documento | Diretor | Secretário |
|---|---|---|
| Declaração | `GET /gestao/diretor/declaracao/versoes/{n}/pdf` | `GET /gestao/secretario/declaracoes/{co_entidade}/versoes/{n}/pdf` |
| Plano Escolar | `GET /gestao/diretor/plano/versoes/{n}/pdf` | `GET /gestao/secretario/planos/{co_entidade}/versoes/{n}/pdf` |
| Plano Municipal | — | `GET /gestao/secretario/plano-municipal/versoes/{n}/pdf` |
| Narrativa executiva | — | `GET /gestao/secretario/plano-municipal/versoes/{n}/narrativa/pdf` |

Cada rota usa a mesma dependência de acesso da rota que já mostra a versão em tela (`exigir_diretor` ou `exigir_secretario`, mais o filtro pela escola ou pela rede do vínculo).

**Organização do código proposta:**
- `app/shared/pdf/` guarda o layout comum: cabeçalho, rodapé, ressalvas, fonte, código de conferência e a checagem pelo Guardião;
- cada feature ganha um `documento.py`, que monta o conteúdo da sua versão;
- os testes ficam em `backend/tests/test_documentos_pdf.py`.

## Notas de implementação (2026-11-03)

- **Código:**
  - layout comum, código de conferência e checagem pelo Guardião em `backend/app/shared/pdf/`, com as fontes Noto Sans e a licença OFL em `fontes/`;
  - um `documento.py` em `declaracao/`, `plano/` e `plano_municipal/`;
  - as cinco rotas da tabela acima;
  - o botão `BotaoPdf.tsx` na emissão da Declaração, nas versões enviadas do plano, nas Declarações da rede, na revisão do plano e nas versões do plano municipal;
  - o CORS expõe `Content-Disposition` para o navegador usar o nome dado pelo servidor;
  - testes em `backend/tests/test_documentos_pdf.py`, que leem o PDF com `pypdf` (dependência só de desenvolvimento).
- **Layout:**
  - A4, com o título da versão, a identificação, "Sobre este documento" (ressalvas e explicação do código) e as seções do documento;
  - cada barreira ou ação fica inteira na mesma página quando cabe;
  - o sumário dos metadados lista as seções.
- **Quem aparece:** nenhum nome de pessoa. A decisão e a confirmação aparecem como "Secretaria Municipal de Educação".
- **Datas:** no horário de Brasília (UTC−3).
- **Revisão do AgLGPD (2026-11-03), aplicada:**
  - bloqueio da versão retirada por dado pessoal ou pedido de titular (A1);
  - camada de nomes na geração, com máscara só no arquivo (M1);
  - marca de uso interno, ressalva de cópia e aviso antes do primeiro download (M2);
  - auditoria de cada pedido e limite por conta em `acesso/entrega_pdf.py` (M3);
  - testes de outra rede, de log e resposta sem o dado, do que não aparece e dos metadados (M4);
  - só o papel no lugar do nome (B1), logs do `fpdf2` e do `fontTools` em ERROR (B3), conferência dentro de `gerar` (B4) e `X-Content-Type-Options: nosniff` (B5).

## Decisões pendentes

- Assinatura digital e valor formal, depois da validação jurídica (questão 16 do PRD).
- Identidade visual definitiva (logotipo e cores do programa e do município).
- PDF da versão publicada na página pública, só com o texto público aprovado.
- PDF em formato PDF/UA (marcado para acessibilidade), que a `fpdf2` não gera por completo.
- Uma página pública para conferir o código não pode revelar conteúdo nem a existência de versão não publicada. Ela deve exigir entrada na plataforma ou responder só sobre versões publicadas, sempre com limite de frequência.

## Notas de implementação da narrativa executiva (2026-11-03)

- `plano_municipal/documento.py::documento_narrativa`, rota em `plano_municipal/router.py` e botão na tela `NarrativaExecutiva.tsx`, com aviso próprio antes do download (`BotaoPdf` com `externo`).
- A checagem de número e nome da rede é a `narrativa.problema`, usada na resposta da IA, na edição e no PDF.
- Recusa antes de montar o documento conta no limite e entra na auditoria (`entrega_pdf.recusar`).
- Campo sem rótulo vira texto corrido no layout comum.
- Testes em `backend/tests/test_narrativa_municipal.py`.
