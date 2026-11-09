# Documento de Requisitos do Produto (PRD) — Escola Sem Barreiras | Fase 2: Gestão Ativa

**Status:** Em implementação — piloto com a rede municipal; protótipo v2 aprovado em 2026-10-23  
**Versão:** 0.3  
**Data:** 2026-10-27 (versão 0.2 de 2026-10-18; 0.1 de 2026-10-11)  
**Fontes primárias:** `../../../FASE2/EscolaSemBarreiras_Fase2_NarrativaV6_revisão_cassiano.pdf` e `../../../FASE2/GestaoAtiva_Perfis_Diretor_Secretario.pdf`

## Resumo

A Fase 2 propõe transformar indicadores da Fase 1, organizados pelos eixos da Política Nacional de Educação Especial Inclusiva (PNEEI), instituída pelo Decreto nº 12.686/2025, em instrumentos de gestão. O módulo **Gestão Ativa** atende diretores, que contextualizam obstáculos da escola e propõem ações, e secretários municipais, que analisam a rede, definem prioridades e estruturam um plano municipal.

Este PRD preserva a proposta das fontes, mas registra como pendentes as decisões de produto, segurança, privacidade, regras legais e cálculo.

**Decisões de produto de 2026-10-18 (validação do protótipo):** a Declaração de Obstáculos é **emitida** antes do Plano de Ação e serve de base de contexto para a IA do plano; **emitir** e **publicar** são etapas separadas; toda barreira precisa de uma **posição** antes da emissão; e passa a existir a posição **divergência com o dado do Censo**. Essas decisões estão detalhadas nas seções 1B, 2 e "Publicação da Declaração de Obstáculos". O protótipo em Linguagem de Marcação de Hipertexto (HTML, do inglês HyperText Markup Language) v2 (`FASE2/prototipo_gestao_ativa_v2.html`) foi aprovado em 2026-10-23, e a implementação começou em seguida.

**Decisões de 2026-10-23 a 2026-10-27 (implementação):** o piloto atende só escolas da **rede municipal**, e o secretário do município aprova os diretores; a entrada é **sem senha**, por código enviado ao e-mail; o rascunho da Declaração é salvo e retomado; o Plano de Ação aceito pode ser **publicado** pelo diretor, só junto com a Declaração publicada; o Plano Estratégico Municipal parte **só dos planos aceitos**; o Dashboard Municipal ordena as escolas pelo **peso no score da rede** e o Analítico ordena as barreiras pelos **alunos atingidos**; e a Fase 1 foi integrada (seção "Integração com a Fase 1"). Os detalhes ficam nas notas de implementação de cada requisito.

## Estado da implementação (2026-10-27)

| Feature | Situação | Requisitos atendidos | Especificação |
|---|---|---|---|
| Acesso à Gestão Ativa | Implementado no piloto | RF-01 a RF-06, RF-12 (só e-mail; sem suspensão de secretário) | [acesso](requirements/acesso-gestao-ativa.md) |
| Dashboard da Escola | Implementado | RF-33, RF-35, RF-38 | [dashboard da escola](requirements/diretor/dashboard-situacao-escola.md) |
| Declaração de Obstáculos | Implementada, com publicação e retirada | RF-07 a RF-11, RF-32, RF-39 a RF-42 | [declaração](requirements/diretor/declaracao-obstaculos.md) |
| Plano de Ação Escolar | Implementado, com publicação do plano aceito | RF-12 a RF-17 (contexto da IA só com a base normativa e a Declaração; sem orçamento e histórico da escola) | [plano escolar](requirements/diretor/plano-acao-escolar.md) |
| Dashboard Municipal | Implementado | RF-18, RF-34, RF-36 a RF-38 | [dashboard municipal](requirements/secretario/dashboard-municipal.md) |
| Fila e Revisão | Implementada, com apontamentos por barreira e ação | RF-19 a RF-22 | [fila](requirements/secretario/fila-revisao-planos.md) |
| Plano Estratégico Municipal | Implementado, com narrativa executiva sem fonte de custo | RF-26 a RF-30 (no RF-30, custos só como estimativa da secretaria até as decisões 12 e 13) | [plano municipal](requirements/secretario/plano-estrategico-municipal.md) |
| Analítico de Barreiras | Implementado em 2026-10-27 | RF-23 a RF-25 | [analítico](requirements/secretario/analitico-barreiras.md) |
| Documentos em PDF | Implementado em 2026-11-03 | RF-31 (Declaração, Plano Escolar e Plano Municipal; sem narrativa executiva e sem PDF público) | [documentos em PDF](requirements/documentos-pdf.md) |

A arquitetura (banco próprio, Guardião LGPD, IA em camadas e validação de citações) está em [arquitetura.md](arquitetura.md).

## Problema e objetivos

Os indicadores tornam lacunas visíveis, mas não oferecem aos diretores um fluxo formal para explicar obstáculos nem aos secretários uma base comparável para consolidar necessidades e planejar intervenções.

- Registrar obstáculos relatados por diretores, vinculados às barreiras encontradas nos dados do Censo.
- Transformar relatos confirmados em planos escolares revisáveis.
- Consolidar padrões e prioridades para a rede municipal.
- Produzir um plano estratégico com ações individuais e sistêmicas, organizadas pela Lei Orçamentária Anual (LOA) e pelo Plano Plurianual (PPA).
- Preservar autoria, versões, fontes e revisão humana dos artefatos gerados com apoio de inteligência artificial (IA).

## Perfis

- **Diretor de escola:** após validação institucional, acessa e gerencia exclusivamente a escola vinculada ao seu perfil.
- **Secretário municipal de educação:** após provisionamento e validação institucional, consulta exclusivamente a rede municipal autorizada, analisa necessidades e gerencia o plano estratégico municipal.
- **Público:** consulta a versão publicada da Declaração de Obstáculos de cada escola, depois da checagem de dados pessoais e da aprovação do diretor, e o Plano de Ação aceito que o diretor publicar. Não acessa a Gestão Ativa.
- **Administrador do produto** (acrescentado na implementação): provisiona secretários e pode retirar publicações a pedido de titular. É criado só pela linha de comando do servidor.

O módulo Gestão Ativa será restrito a diretores e secretários aprovados. As páginas públicas da Fase 1 permanecem públicas. Não haverá integração com gov.br no MVP. O fluxo deve verificar separadamente a identidade/canal da pessoa e sua autorização para exercer o papel na escola ou rede.

## Escopo proposto do produto mínimo viável (MVP, do inglês Minimum Viable Product)

### 0. Cadastro, validação de vínculo e acesso

O diretor solicita acesso informando seus dados de contato e o código INEP da própria escola. A solicitação começa pendente e não libera o módulo. Uma autoridade educacional ou mantenedora autorizada confirma o vínculo consultando seus registros funcionais e, quando necessário, um ato oficial vigente. O e-mail ou telefone institucional é confirmado por código de uso único; essa confirmação prova controle do canal, mas não substitui a validação do vínculo.

Contas de secretário municipal são provisionadas inicialmente por um administrador autorizado do produto, que confirma a função por canal institucional oficial. Após aprovação, a autorização é aplicada no servidor: diretor acessa somente a escola vinculada e secretário somente a rede municipal habilitada. Aprovação, rejeição, alteração de vínculo e revogação devem ser registradas. Não se exige cópia de documento pessoal por padrão.

O Censo Escolar 2025 não fornece a identidade individual necessária para aprovar o cadastro: a tabela pública de gestor escolar contém contagens por escola, incluindo a quantidade declarada de diretores, mas não nome ou contato pessoal. Por isso, o sistema não deve aprovar automaticamente uma solicitação com base apenas no código INEP, autodeclaração ou acesso a e-mail.

### 1. Visão do diretor e registro de obstáculos

**1A. Dashboard da Situação Atual da Escola:** após autenticação e validação de vínculo, a primeira tela do diretor apresenta uma visão ampliada da escola: score e faixa, resultados e indicadores dos quatro eixos da PNEEI, barreiras identificadas nos dados, posições já registradas, estado da Declaração (rascunho, emitida, publicada), pendências, planos de ação e decisões da secretaria. A partir da análise dos eixos e barreiras, o diretor pode iniciar a Declaração de Obstáculos. O dashboard é privado ao diretor e à escola vinculada, não substitui nem altera a página pública da escola.

**1B. Declaração de Obstáculos:** é a justificativa formal da escola diante das barreiras apontadas pelo Censo, dirigida ao secretário e ao público. Para cada barreira, o diretor registra uma **posição**:

- **Obstáculo relatado:** uma conversa com IA coleta o obstáculo, faz perguntas de aprofundamento e apresenta o texto formal para revisão explícita do diretor.
- **Divergência com o dado do Censo:** o diretor informa que o dado não reflete a realidade da escola (por exemplo, a sala existe, mas não foi declarada). A divergência fica registrada e não altera o dado, o score nem a faixa.
- **Sem relato nesta versão:** escolha explícita do diretor, exibida como tal, nunca como barreira inexistente ou esquecida.

A Declaração só pode ser **emitida** quando todas as barreiras têm posição. Emitir congela uma versão com autoria e data, torna-a visível ao secretário da rede e a disponibiliza como contexto para a IA do Plano de Ação. Mudanças posteriores geram nova versão (retificação), sem apagar as anteriores. A IA redige em tom factual e neutro, sem atribuir culpa a pessoas ou órgãos. A declaração não altera os dados nem o score do Censo.

### 2. Plano de Ação da escola

O Plano de Ação só pode ser iniciado depois que a escola tem uma Declaração de Obstáculos **emitida**. A IA conversacional usa a versão emitida como contexto: cruza cada barreira com a posição registrada e propõe uma ou mais ações pertinentes, citando o obstáculo ou a divergência em que cada proposta se baseia. O plano fica vinculado à versão da declaração usada; se uma nova versão for emitida depois, o plano é sinalizado como baseado na versão anterior. O diretor conversa com a IA para avaliar a pertinência de cada proposta, pedir esclarecimentos e ajustar a ação; o modelo deve usar apenas contexto autorizado e disponível para aquela escola, como normas e documentos institucionais, orçamento e histórico de ações, identificando fontes e lacunas. A IA sugere; o diretor decide quais ações integrar ao plano. A proposta organizada por ações da LOA (exercício corrente) e do PPA (horizonte de quatro anos, conforme a fonte) é editável, mantém histórico de versões e só é enviada à secretaria após confirmação explícita do diretor. O envio cria uma versão submetida, pendente de decisão do secretário municipal. As fontes propõem exportar o Plano de Ação e uma Declaração de Não-Conformidade Justificada em Formato de Documento Portátil (PDF); o formato e o status jurídico desses documentos ainda precisam de validação.

### 3. Revisão municipal dos Planos de Ação escolares

**3A. Dashboard Municipal do Secretário:** após autenticação e validação de vínculo, a tela inicial do secretário apresenta uma visão privada do município, distinta da área pública: score municipal e contexto, eixos ordenados da pior para a melhor situação, escolas prioritárias que mais contribuem para o score baixo segundo critérios reproduzíveis, e uma fila/indicador de escolas com Planos de Ação submetidos para análise. A lista da fila permite abrir a feature de revisão. A ordenação e os critérios de prioridade devem ser explicáveis; a IA não inventa pontuações nem substitui o cálculo determinístico.

**3B. Fila e Revisão dos Planos de Ação escolares:** o secretário vê a lista de escolas da sua rede que submeteram pelo menos uma proposta, com estado de revisão e data da última submissão. Pode abrir cada proposta, junto com a versão da Declaração de Obstáculos em que ela se baseia, e decidir sobre a versão submetida: **aceitar** sem recomendação adicional, **solicitar ajustes** com comentário obrigatório ou **reprovar** com justificativa obrigatória. A escola recebe a decisão e, se ajustes forem solicitados, pode editar a proposta e submetê-la novamente como nova versão. A aceitação valida a proposta como base de planejamento municipal; não significa que as ações foram financiadas ou executadas. Reprovação não apaga histórico nem registros de obstáculos.

### 4. Painel do secretário e analítico de barreiras

Apresentar score municipal, situação por eixo, escolas prioritárias, estado de registro de obstáculos e estado de revisão dos Planos de Ação. O secretário consulta as Declarações emitidas pelas escolas da rede, inclusive de escolas que ainda não submeteram plano, e pode solicitar uma varredura assistida por IA das declarações emitidas e dos planos submetidos, cruzando barreiras, obstáculos e ações para identificar padrões recorrentes, severidade e escolas com maiores dificuldades. Contagens, critérios de ordenação e indicadores devem ser computados por lógica determinística e rastreável; as interpretações da IA são sinalizadas como análise assistida, não como veredito.

### 5. Plano Estratégico Municipal

Com base na análise e nas propostas escolares, o secretário pode selecionar ações ou partes de ações para compor um plano municipal organizado pela LOA e pelo PPA. Uma ação municipal pode atender uma barreira comum a várias escolas ou cobrir apenas uma parte do Plano de Ação de uma escola; a composição municipal não aceita, substitui ou conclui automaticamente o restante do plano escolar. O plano municipal deve indicar quais escolas e ações são contempladas, estimativas e premissas, impacto projetado e narrativa executiva. A IA pode apoiar a identificação e redação de oportunidades, mas o secretário seleciona, edita e confirma o plano. Depois de confirmado, o sistema registra a versão como proposta/meta municipal e mostra às escolas apenas as ações que as envolvem; não as marca como executadas sem registro próprio.

### Publicação da Declaração de Obstáculos

Publicar é uma etapa separada de emitir. A partir de uma versão emitida, o sistema gera uma versão pública em linguagem acessível. Antes de publicar, uma checagem assistida por IA aponta possíveis dados pessoais e riscos de identificação indireta de estudantes ou profissionais (por exemplo, "o único estudante surdo do 5º ano"), e o diretor revisa e aprova explicitamente. A versão publicada aparece na página pública da escola com data e número de versão, sem alterar o score nem os dados do Censo. Retirada da publicação, moderação e eventual resposta da secretaria permanecem como decisões pendentes.

### Integração com a Fase 1

A área pública da Fase 1 continua aberta, sem login. A integração, decidida rota por rota em [impacto-fase-1.md](impacto-fase-1.md) e concluída em 2026-10-27, fez o seguinte:
- **login da Fase 1:** saiu do ar, com o autocadastro; o único login do produto é o da Gestão Ativa;
- **entrada da Gestão Ativa:** o cabeçalho, a Início, o rodapé e a página Sobre levam a `/participar`;
- **fichas das escolas:** mostram as barreiras do Censo e o que a escola publicou;
- **Início do município:** conta as publicações das escolas;
- **Diagnóstico IA:** virou uma leitura pública do município, sem chat e sem recomendações.

## Não objetivos

- Enviar ou alterar respostas dentro do Educacenso; a fonte informa não haver interface de programação de aplicações (API) pública para integração.
- Garantir orçamento, execução de intervenção ou conformidade legal por meio de documentos gerados.
- Alterar score, dados observados do Censo ou status por decisão da IA.
- Incluir no MVP o Assistente de Preenchimento do Censo ou a Série Histórica; a Narrativa V6 os lista como extensões futuras.

## Requisitos funcionais (RF) propostos

### Acesso e experiência por perfil

- **RF-01:** restringir o módulo Gestão Ativa a diretores e secretários com vínculo aprovado, aplicando autorização no servidor por escola ou rede municipal; as páginas públicas da Fase 1 permanecem públicas.
- **RF-02:** apresentar experiências de entrada e navegação distintas para diretor e secretário.
- **RF-03:** permitir que o diretor solicite acesso associando-se a uma escola identificada pelo código INEP; manter a solicitação pendente até aprovação institucional.
- **RF-04:** habilitar secretários municipais por provisionamento aprovado por administrador autorizado, associado a um município.
- **RF-05:** confirmar controle do e-mail ou telefone por código de uso único, sem tratar isso como prova suficiente de cargo/vínculo. *(Implementado só por e-mail.)*
- **RF-06:** registrar aprovador, data, método e resultado da verificação, alterações e revogações, minimizando dados pessoais.
- **RF-33:** após autenticação, abrir o diretor no Dashboard da Situação Atual da Escola vinculada.
- **RF-34:** após autenticação, abrir o secretário no Dashboard Municipal da rede autorizada.
- **RF-35:** disponibilizar no Dashboard da Escola o contexto ampliado dos eixos/barreiras e um ponto de entrada explícito para iniciar a Declaração de Obstáculos.
- **RF-36:** disponibilizar no Dashboard Municipal os eixos ordenados por situação e uma lista explicável de escolas prioritárias que contribuem para o score baixo.
- **RF-37:** mostrar no Dashboard Municipal a quantidade/lista de Planos de Ação submetidos e pendentes de análise, com acesso à fila correspondente.
- **RF-38:** manter dashboards da Gestão Ativa privados e separados das páginas públicas da Fase 1, aplicando autorização no servidor.

### Diretor | Declaração de Obstáculos

- **RF-07:** listar barreiras do Censo por eixo, separando dados observados de obstáculos relatados.
- **RF-08:** conduzir conversa contextualizada por barreira, aprofundar o relato e permitir revisão explícita do diretor.
- **RF-09:** consolidar a Declaração de Obstáculos com a posição de cada barreira (obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão), sem alterar dados ou score do Censo.
- **RF-10:** manter autoria, data, histórico e versões da declaração e das conversas.
- **RF-11:** mostrar estado do registro por barreira e permitir ao diretor acompanhar o progresso.
- **RF-39:** permitir registrar, para cada barreira, a posição "divergência com o dado do Censo", com descrição da realidade informada, sem alterar o dado.
- **RF-40:** permitir emitir a Declaração somente quando todas as barreiras tiverem posição; a emissão congela a versão e a torna visível ao secretário da rede.
- **RF-41:** permitir retificar uma declaração emitida por meio de nova versão, preservando as anteriores e sinalizando planos baseados em versão antiga.
- **RF-42:** permitir publicar uma versão emitida após checagem assistida de dados pessoais e aprovação explícita do diretor.

### Diretor | Plano de Ação Escolar

- **RF-12:** exigir Declaração emitida para iniciar o plano e usar a versão emitida como contexto da IA, que cruza cada barreira com a posição registrada e propõe ações.
- **RF-13:** permitir ao diretor avaliar pertinência, conversar sobre sugestões e selecionar, editar ou descartar ações explicitamente.
- **RF-14:** limitar o contexto da IA a documentos, normas, orçamento e histórico da própria escola que estejam disponíveis e autorizados, identificando fontes e lacunas.
- **RF-15:** permitir editar ações, responsáveis, prazos, observações e horizonte LOA/PPA, preservando sugestões de IA e decisões humanas.
- **RF-16:** permitir ao diretor submeter uma versão confirmada; a versão enviada fica congelada e pendente de análise municipal.
- **RF-17:** disponibilizar ao diretor estado, comentários e decisão da secretaria e permitir nova versão após pedido de ajustes sem apagar versões anteriores.

### Secretário | Entrada, fila e revisão

- **RF-18:** apresentar painel de entrada do secretário com visão municipal e fila própria de revisão, distinta da experiência do diretor.
- **RF-19:** listar escolas da rede com ao menos um Plano de Ação submetido, estado e data da submissão.
- **RF-20:** permitir abrir a versão submetida e os registros associados dentro do escopo autorizado.
- **RF-21:** permitir aceitar a versão como base, solicitar ajustes com comentário obrigatório ou reprovar com justificativa obrigatória.
- **RF-22:** registrar decisão, responsável, data e versão avaliada; disponibilizar a decisão ao diretor da escola correspondente.

### Secretário | Analítico de Barreiras

- **RF-23:** produzir análise assistida por IA que cruze barreiras, obstáculos e ações para identificar recorrências, severidade e padrões entre escolas.
- **RF-24:** apresentar evidências, cobertura e limitações; contagens, métricas, filtros e ordenação devem ser reproduzíveis e não determinados por texto livre da IA.
- **RF-25:** não interpretar falta de submissão como ausência de barreira ou dificuldade.

### Secretário | Plano Estratégico Municipal

- **RF-26:** permitir compor o plano municipal com ações sistêmicas e ações ou partes identificadas de Planos de Ação escolares.
- **RF-27:** registrar escolas, barreiras e itens escolares atendidos por cada ação municipal; a cobertura parcial não aceita, substitui ou encerra o restante do plano escolar.
- **RF-28:** permitir editar, priorizar, confirmar e versionar o plano municipal com premissas, fontes, orçamento estimado e horizonte LOA/PPA.
- **RF-29:** distribuir ações municipais somente às escolas relacionadas, sem marcar automaticamente financiamento ou execução.
- **RF-30:** incluir narrativa executiva e fontes identificáveis para custos e projeções.

### Documentos e publicação

- **RF-31:** gerar documentos em Formato de Documento Portátil (PDF) com versão, data, conteúdo confirmado e ressalvas, sujeito a validação jurídica.
- **RF-32:** exibir na página pública da escola a versão publicada da Declaração de Obstáculos, com data e versão, conforme RF-42.

Os critérios de aceite detalhados e as notas de implementação de cada requisito estão nos documentos de requisitos por feature (ver "Estado da implementação").

## Requisitos transversais

- Aplicar autorização no servidor e proteger conversas e registros escolares.
- Não enviar dados pessoais a provedores de IA sem avaliação e controles aprovados; reduzir e filtrar dados antes do processamento.
- Distinguir dados observados, relatos, inferências de IA, estimativas, edições humanas e decisões confirmadas.
- Não permitir que texto livre de IA determine números oficiais, score ou conformidade; cálculos devem ser determinísticos e verificáveis.
- Preservar registros confirmados diante de indisponibilidade de IA e permitir retomar operações interrompidas.
- Projetar para acessibilidade, incluindo teclado, leitor de tela e estados que não dependam apenas de cor.
- Redigir textos gerados pela IA para a Declaração em tom factual e neutro, sem atribuir culpa a pessoas ou órgãos.
- Não apresentar estimativa como orçamento aprovado nem documento gerado como parecer jurídico ou certificação.

## Decisões pendentes

1. **Parcialmente resolvida em 2026-10-23:** no piloto, o secretário do município aprova os diretores da rede municipal, e o administrador do produto provisiona o secretário. Continuam pendentes os substitutos autorizados e a autoridade para outras redes.
2. **Resolvida em 2026-10-18:** a Declaração é fechada na **emissão**, que exige posição para todas as barreiras; retificação gera nova versão, e o plano baseado em versão anterior é sinalizado. Continua pendente se a retificação deve ser bloqueada enquanto um plano está em análise.
3. **Resolvida em 2026-10-23:** o rascunho da Declaração (posições e conversa em andamento) fica salvo e é retomado de onde parou; conversas paradas há mais de 30 dias são apagadas.
4. Definir os critérios pelos quais o diretor marca uma ação sugerida pela IA como pertinente, ajustável ou não pertinente, e como tratar ações não pertinentes.
5. Definir quais normas, documentos institucionais, orçamento e histórico estarão disponíveis para contexto da IA, quem os fornece, níveis de acesso, atualização e retenção.
6. Definir prazo de análise da secretaria, responsáveis substitutos e se aceitação pode incluir recomendação opcional. Hoje a escola pode enviar nova versão depois de qualquer decisão, inclusive reprovação; a política definitiva segue pendente.
7. **Parcialmente resolvida em 2026-10-26:** a decisão vale para a versão inteira; ao pedir ajustes ou reprovar, a secretaria pode apontar barreiras e ações específicas, com nota. Aceite parcial de um plano não existe.
8. **Parcialmente resolvida em 2026-10-26:** cada ação municipal aponta as escolas e os itens dos planos aceitos que atende, com cobertura total ou parcial. Continua pendente quem mantém o andamento (execução).
9. **Parcialmente resolvida em 2026-10-18 e 2026-10-24:** a Declaração é publicada em etapa separada da emissão, após checagem de dados pessoais e aprovação do diretor; a retirada existe (pelo diretor e pela administração, com motivo e auditoria). Continuam pendentes: moderação, canal público para pedir revisão, prazo de exibição de versões antigas e se a publicação pode ser obrigatória.
10. Dados permitidos nos prompts, provedores de IA, retenção e prevenção de dados pessoais. **Parcialmente resolvida em 2026-10-18:** provedores em plano gratuito, com Guardião LGPD local que mascara ou bloqueia dados pessoais antes de qualquer envio à IA (ver `arquitetura.md`, AD-05). Continuam pendentes a retenção e a validação da taxa de detecção.
11. Validação por especialista do mapeamento legal e dos artigos citados nos documentos.
12. Método determinístico para estimar impacto no score; a fonte atribui o cálculo ao modelo de linguagem de grande escala (LLM, do inglês Large Language Model), enquanto a arquitetura atual proíbe IA de decidir números/status.
13. Fontes concretas, cobertura e atualização de estimativas do Fundo Nacional de Desenvolvimento da Educação (FNDE) e do Sistema de Informações sobre Orçamentos Públicos em Educação (SIOPE).
14. Ano da LOA, horizonte do PPA e critérios de classificação orçamentária.
15. Edição de Censo usada para comparação de evolução do score.
16. **Parcialmente resolvida em 2026-11-03:** no piloto o PDF é informativo, sem assinatura, com versão, datas, quem confirmou, código de conferência e ressalvas ([documentos em PDF](requirements/documentos-pdf.md)). Continuam pendentes a assinatura, a identidade visual e o valor formal depois da validação jurídica.
17. Vocabulário e relação entre “barreira” identificada nos dados e “obstáculo” relatado pelo diretor. Em 2026-10-18 foi adotado “posição” como termo para o que o diretor registra sobre cada barreira (obstáculo relatado, divergência com o dado do Censo ou sem relato nesta versão).
18. Cronograma de dois meses indicado na Narrativa V6, escopo incluído e disponibilidade para validação.
19. **Resolvida em 2026-10-23:** o piloto atende só escolas da rede municipal. **Complemento de 2026-11-09:** no Distrito Federal, que não tem rede municipal, o piloto atende a rede distrital (escolas “Estadual” do Censo em Brasília, 5300108).
20. Definir se o secretário pode registrar resposta ou manifestação, pública ou privada, a uma Declaração que atribua obstáculos à rede.
21. Definir o encaminhamento das divergências com o dado do Censo: se geram orientação para correção no próximo Educacenso (ligada à futura extensão Assistente de Preenchimento) e se aparecem para o secretário como indicador próprio.
22. Definir se "sem relato nesta versão" exige justificativa curta e se aparece na versão publicada.

## Fora do cronograma de MVP

A Narrativa V6 lista como extensões: Assistente de Preenchimento do Censo (sem integração com Educacenso) e Série Histórica com bases de 2023, 2024 e 2025.

## Etapas seguintes

Requisitos de acesso: [Acesso à Gestão Ativa](requirements/acesso-gestao-ativa.md). O [índice das features de requisitos](requirements/planos-de-acao.md) aponta para Declaração de Obstáculos, Plano de Ação Escolar, Fila e Revisão do Secretário, Analítico de Barreiras e Plano Estratégico Municipal. As regras seguem a mesma separação no [índice de regras de negócio](business-rules/planos-de-acao.md). Próxima entrega: documentos em PDF (RF-31). A narrativa executiva (RF-30) foi entregue em 2026-10-27 sem fonte de custo. Antes de produção: provedor de e-mail real, validação jurídica dos prazos de retenção definidos em 2026-11-03 e agendamento diário da rotina ([retencao.md](business-rules/retencao.md); AD-07 em [arquitetura.md](arquitetura.md)) e o destino das contas da Fase 1 ([impacto-fase-1.md](impacto-fase-1.md)).
