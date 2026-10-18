# Regras de Negócio — Acesso à Gestão Ativa

**Status:** Proposta para validação  
**Rastreabilidade:** Documento de Requisitos do Produto (PRD) geral B2-13; PRD da Fase 2 RF-01 e RF-03 a RF-06; requisitos de acesso à Gestão Ativa

Neste documento, RN significa regra de negócio e RF significa requisito funcional.

## RN-01 — Gestão Ativa é exclusiva a dois perfis aprovados

Somente Diretor de escola e Secretário municipal de educação com vínculo ativo podem acessar as funcionalidades da Gestão Ativa. A exclusividade não transforma em privadas as páginas públicas já existentes na Fase 1. Contas públicas ou outros perfis da Fase 1 não herdam acesso ao módulo.

## RN-02 — Autodeclaração inicia pedido, não concede papel

Informar nome, contato, perfil de diretor e código do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP) da escola cria apenas uma solicitação pendente. A autodeclaração, o código da escola, os dados agregados do Censo ou a criação de uma conta comum nunca ativam privilégios por si sós.

## RN-03 — Identidade, controle do canal e vínculo funcional são verificações distintas

A confirmação por código de uso único comprova que a pessoa controla o e-mail ou telefone de destino naquele momento. Não comprova identidade civil nem nomeação/vínculo como diretor. A autoridade institucional responsável precisa confirmar o vínculo atual usando registros ou fonte oficial independente do candidato.

## RN-04 — Aprovação deve vir de autoridade independente

O candidato não aprova a própria solicitação. A aprovação do diretor cabe a autoridade educacional ou mantenedora autorizada responsável pela escola, conforme sua dependência administrativa. Contas de secretário municipal são provisionadas inicialmente por administrador autorizado do produto após confirmação da função em canal institucional oficial.

## RN-05 — O vínculo de diretor é com a escola específica

Cada diretor ativo fica associado somente à escola aprovada pelo código INEP. Alteração de escola ou novo vínculo exige nova validação. A associação a uma escola não concede acesso às demais unidades da rede.

## RN-06 — O vínculo de secretário é com uma rede municipal

Cada secretário aprovado fica associado ao município/rede municipal autorizado. O papel não concede acesso a outros municípios. A autorização para atribuir ou substituir secretário deve ser mantida por administrador com autoridade documentada.

## RN-07 — A autorização é aplicada no servidor

Toda operação de Gestão Ativa valida estado da conta, papel e vínculo no servidor. Ocultar uma tela, alterar um identificador enviado pelo navegador ou conhecer uma URL não substitui a autorização. Solicitações pendentes, rejeitadas, suspensas ou revogadas não acessam o módulo.

## RN-08 — Não há integração gov.br no produto mínimo viável (MVP)

O fluxo não depende do gov.br e não pode sugerir que a conta foi verificada por esse serviço. Uma eventual integração futura exige decisão de produto e atualização destas regras.

## RN-09 — O Censo não é cadastro nominal de diretores

A tabela pública de gestores do Censo Escolar disponibiliza contagens e características agregadas por escola, incluindo quantidade declarada de diretores; não identifica nominalmente o profissional nem fornece contato individual. O sistema não consulta essa tabela para autenticar, aprovar ou rejeitar pessoas.

## RN-10 — Contato institucional deve ser obtido ou confirmado independentemente

Quando e-mail ou telefone institucional for usado no convite, a origem do canal de aprovação deve ser uma fonte institucional independente do pedido de cadastro. Um contato fornecido somente pelo candidato não é prova suficiente de que ele ocupa o cargo.

## RN-11 — Coletar e reter apenas o necessário

Não exigir nem guardar cópia de documento pessoal por padrão. Registrar o resultado, responsável, data e método de validação, além da referência institucional mínima necessária para auditoria. Exceções dependem de avaliação de privacidade/jurídica, finalidade, acesso restrito e prazo de retenção.

## RN-12 — Acesso pode ser suspenso ou revogado

A autoridade responsável pode suspender ou revogar o vínculo quando houver desligamento, mudança de escola/rede, perda de autorização ou suspeita de uso indevido. A revogação bloqueia imediatamente novas operações; a troca de vínculo segue novamente o processo de validação.

## RN-13 — Aprovações e mudanças são auditáveis

Registrar solicitações, aprovações, rejeições, mudanças de vínculo, suspensões e revogações com autor, data/hora, resultado e método/justificativa. Não registrar senhas, tokens ou códigos de uso único nos eventos de auditoria.

## RN-14 — Escopo inicial das redes depende de decisão explícita

Até que o PRD decida se o MVP atende escolas municipais, estaduais, federais e privadas, a regra de aprovação permanece parametrizada pela autoridade educacional/mantenedora competente. Não presumir que um secretário municipal tenha competência para aprovar diretor de escola de outra dependência.
