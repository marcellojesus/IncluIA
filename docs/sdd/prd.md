# Documento de Requisitos do Produto (PRD) — Escola Sem Barreiras

**Status:** Visão do produto atualizada por engenharia reversa do código local; backlog da Fase 2 proposto, sujeito a entendimento e aprovação  
**Versão:** 0.2  
**Data:** 2026-10-11  
**Base observada:** checkout local do frontend Next.js e backend FastAPI em 2026-10-11

## Visão do produto

A Escola Sem Barreiras é uma plataforma pública de transparência e controle social da educação especial inclusiva. Apresenta indicadores derivados dos microdados do Censo Escolar do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP), organizados por município, escola e eixos da Política Nacional de Educação Especial Inclusiva (PNEEI), para que sociedade e gestores possam explorar e comparar a situação apresentada.

O produto inclui uma experiência de diagnóstico narrativo assistido por inteligência artificial (IA), protegida por autenticação. O diagnóstico explica indicadores já calculados e permite conversa por eixo para esclarecer ou ajustar recomendações; não substitui os dados do Censo, validação jurídica ou decisão orçamentária.

## Problema e públicos

Informações sobre inclusão escolar exigem processamento e contexto para serem compreensíveis e comparáveis. A plataforma busca tornar esses indicadores acessíveis ao público e oferecer aos usuários autenticados uma explicação contextualizada por IA.

- **Público geral:** famílias, sociedade civil, imprensa, pesquisadores e demais visitantes que consultam os dados abertos.
- **Usuários autenticados:** qualquer pessoa com conta criada ou credenciais válidas pode acessar o Diagnóstico IA. O perfil informado na conta não limita o município consultado.

O software atual não implementa áreas privadas específicas para diretores ou secretários, nem autorização por escola, município ou unidade da Federação (UF).

## Objetivos do produto

- Tornar indicadores derivados do Censo Escolar exploráveis em linguagem acessível.
- Permitir navegar entre municípios por região, unidade da Federação (UF) e município e comparar seus resultados.
- Exibir resultados por escola e por eixo, com rastreabilidade à metodologia e às fontes públicas.
- Oferecer diagnóstico textual assistido por IA, com controles de acesso, alternativas automáticas em caso de falha (fallback) e persistência de conversas.
- Evoluir para apoiar ações de gestão sem confundir dado observado, métrica, relato, recomendação ou decisão pública.

## Princípios

1. Dados do Censo e métricas calculadas devem permanecer distinguíveis de análise e recomendação geradas por IA.
2. A IA explica indicadores pré-calculados; score e status de eixo são derivados por regras determinísticas.
3. Referências legais devem obedecer ao mapeamento documentado, e os indicadores não constituem certificação de conformidade.
4. Funcionalidades visíveis mas não implementadas devem ser identificadas como futuras e não podem sugerir que um registro ou encaminhamento foi realizado.
5. Cada fase tem seu próprio PRD; backlog futuro não é compromisso de entrega até aprovação.

## Produto atual — Fase 1

O sistema observado oferece:

- **Início municipal:** rota `/` encaminha ao painel (dashboard) de Brasília, no Distrito Federal (DF), como município inicial. O painel exibe score e faixa, semáforos dos quatro eixos da PNEEI, scores por eixo, dados gerais da rede, ações de navegação e comparação estadual.
- **Navegação geográfica:** seletor persistente em cascata Região → UF → Município. A página dedicada de mapa coroplético não é a navegação principal atual.
- **Escolas do município:** lista pública com filtros de situação crítica e sem Atendimento Educacional Especializado (AEE), ficha/modal de escola e estados de carregamento/erro. Exportação está desabilitada e sinalizada como futura.
- **Comparação:** tela pública com rankings de estados e municípios por UF.
- **Diagnóstico IA:** tela por município, autenticada, com análise, alerta, recomendações e referência comparativa por eixo; permite regenerar, conversar por eixo, persistir histórico e solicitar reprocessamento do diagnóstico. Usa Gemini → Groq → Mistral; quando todos falham durante a geração inicial, o backend pode apresentar dados sem narrativa de IA.
- **Transparência e informação:** páginas Sobre, Dados Abertos e Metodologia apresentam créditos e avisos acadêmicos, link para microdados do INEP, documentação da interface de programação de aplicações (API) e metodologia. Dados Abertos não oferece exportação própria de conjuntos de dados (datasets).
- **Acessibilidade de interface:** barra compartilhada oferece controles de alto contraste e tamanho de fonte.
- **Área de participação:** rota existe, mas mostra página em construção. Os botões “Registrar uma barreira” apenas informam que a funcionalidade estará disponível em fase futura; não salvam nem encaminham registros.

O detalhamento verificado, rotas e limites estão em [PRD da Fase 1](fase-1/prd.md). Requisitos e regras detalhados antigos continuam em seus caminhos atuais e podem documentar etapas anteriores do produto.

## Backlog proposto — Fase 2: Gestão Ativa

Este backlog consolida o escopo apresentado na Narrativa V6 e em “Gestão Ativa — Fluxo por perfil de usuário”. É uma proposta para entendimento, prototipação e validação; **não está aprovado para implementação**. A próxima atividade será entender os fluxos e testar a experiência em protótipo HTML.

### Acesso aos perfis de Gestão Ativa

- **B2-13 — Cadastro e validação de vínculo:** permitir acesso somente a diretores e secretários autorizados, sem integração com gov.br no MVP. O diretor solicita vínculo com uma escola pelo código INEP; a solicitação fica pendente até validação pela autoridade educacional ou mantenedora responsável. O secretário é habilitado por provisionamento inicial de um administrador autorizado, com confirmação por canal oficial. A verificação do e-mail/telefone confirma controle do canal, não o cargo. Após aprovação, aplicar escopo por escola para diretor e por rede municipal para secretário. Requisitos e regras detalhados: [Requisitos de acesso à Gestão Ativa](fase-2/requirements/acesso-gestao-ativa.md) e [Regras de acesso à Gestão Ativa](fase-2/business-rules/acesso-gestao-ativa.md).

### Perfil Diretor de Escola

- **B2-01 — Dashboard da Situação Atual da Escola:** tela inicial privada do diretor, com score, faixa, análise ampliada dos quatro eixos, barreiras, obstáculos já registrados, pendências e acesso à Declaração de Obstáculos.
- **B2-02 — Registro de posições por barreira:** mostrar barreiras extraídas dos dados do Censo, agrupadas por eixo; para cada uma, o diretor registra obstáculo relatado (com conversa de IA e revisão do texto formal), divergência com o dado do Censo ou sem relato nesta versão.
- **B2-03 — Emissão, publicação e histórico da Declaração:** emitir a declaração somente quando todas as barreiras tiverem posição; a versão emitida fica visível ao secretário e serve de contexto ao Plano de Ação. Publicar para o público é etapa separada, com checagem de dados pessoais e aprovação do diretor. Retificar gera nova versão; preservar autoria, data, versões e histórico conversacional sem alterar o dado do Censo.
- **B2-04 — Plano de Ação conversacional da escola:** iniciado somente após a Declaração emitida, que é o contexto da IA; cruzar cada barreira com a posição registrada e propor ações com apoio de IA conversacional. O diretor avalia a pertinência, pede ajustes ou descarta uma sugestão; escolhe as ações que entram no plano, organizado por LOA/PPA e com responsáveis, prazos e estimativas identificadas.
- **B2-05 — Submissão do plano à secretaria:** salvar o Plano de Ação no perfil da escola e permitir que o diretor submeta uma versão para análise municipal; a submissão fica pendente de decisão e mantém as versões anteriores.
- **B2-06 — Documentos da escola:** gerar Declaração de Obstáculos e Plano de Ação em PDF quando aprovados no escopo documental, com versões e ressalvas jurídicas adequadas.

### Perfil Secretário Municipal de Educação

- **B2-07 — Dashboard Municipal:** tela inicial privada do secretário, com eixos ordenados pela pior situação, escolas que mais contribuem para score baixo segundo critério explicável e fila de escolas com Planos de Ação submetidos.
- **B2-08 — Fila e decisão sobre planos escolares:** abrir a lista de submissões e permitir aceitar uma versão como base, solicitar ajustes com comentário ou reprovar com justificativa; comunicar a decisão e preservar o histórico.
- **B2-09 — Analítico assistido por IA:** varrer declarações e planos submetidos, cruzando barreiras, obstáculos e ações para apontar recorrência, severidade e escolas com maiores dificuldades. A IA explica padrões; métricas e critérios numéricos permanecem reproduzíveis.
- **B2-10 — Plano Estratégico Municipal parcial:** permitir selecionar ações ou partes de planos escolares para compor respostas municipais sistêmicas ou compartilhadas, indicando as escolas e barreiras atendidas. A inclusão de parte de um plano não aceita, substitui nem encerra o restante do plano da escola.
- **B2-11 — Confirmação e distribuição municipal:** permitir revisar e confirmar o Plano Estratégico Municipal organizado por LOA/PPA; registrar a versão aprovada como proposta/meta e mostrar a cada diretor somente as ações que envolvem sua escola, sem indicar execução automática.

### Extensões citadas como trabalho futuro

- **B2-12 — Assistente de preenchimento do Censo:** checklist editável de apoio ao Educacenso, sem envio direto ao INEP.
- **B2-14 — Série histórica:** comparar evolução de escolas e municípios quando as bases históricas e regras de comparabilidade estiverem disponíveis.

### Condições antes de qualquer implementação

Definir autenticação e associação diretor/escola e secretário/rede; autoridades para aprovar, ajustar ou reprovar planos; prazos de análise e reenvio; pausa e retomada dos chats; critérios de pertinência das sugestões; documentos, orçamento e histórico que podem compor o contexto de IA; governança de publicação pública; privacidade, minimização e retenção; validação jurídica; cálculo determinístico de impacto no score; fontes de custo do Fundo Nacional de Desenvolvimento da Educação (FNDE) e do Sistema de Informações sobre Orçamentos Públicos em Educação (SIOPE); horizonte e ano da Lei Orçamentária Anual (LOA) e do Plano Plurianual (PPA); campos e valor formal dos PDFs. A especificação completa e as decisões em aberto estão no [PRD da Fase 2](fase-2/prd.md).

## Fora do escopo atual

- Gestão Ativa e os itens do backlog acima ainda não estão implementados no software observado.
- O Educacenso não é integrado para leitura/escrita operacional; a futura extensão é um guia/checklist.
- A área pública não recebe obstáculos de diretores atualmente.
- Página de participação, exportação das escolas e exportação do diagnóstico são ausentes, placeholders ou controles desabilitados.
- O score não é uma certificação oficial de conformidade jurídica.

## Critério de verdade e manutenção

Este PRD registra comportamento do código local observado em 2026-10-11; ele não certifica deploy de produção, qualidade dos dados, aderência de todos os requisitos antigos nem aprovação da proposta da Fase 2. Mudanças no produto devem atualizar o PRD da fase correspondente e manter rastreabilidade com requisitos e regras de negócio. O protótipo HTML da Fase 2 começa somente após a etapa de entendimento e validação do backlog.

## PRDs por fase

- [Fase 1 — produto implementado observado](fase-1/prd.md)
- [Fase 2 — Gestão Ativa proposta](fase-2/prd.md)
