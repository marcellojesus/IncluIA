# Arquitetura da Fase 2 — Gestão Ativa

**Status:** Proposta para revisão · 2026-10-18  
**Base:** [arquitetura.md](../../../arquitetura.md) (Fase 1), [docs/deploy.md](../../deploy.md), [PRD da Fase 2](prd.md) e [impacto sobre a Fase 1](impacto-fase-1.md)  
**Restrições definidas pelo responsável em 2026-10-18:** infraestrutura somente em planos gratuitos, inclusive para a IA; nenhum dado pessoal pode ser enviado à IA, garantido por um Guardião LGPD local (AD-05).

## 1. Contexto

A Fase 1 é um produto de **leitura**: o ETL processa o Censo em lote, grava `data/incluia.db` (SQLite) e esse arquivo é versionado no Git e servido pelo backend sem escrita relevante. A Fase 2 é um produto de **escrita**: declarações, planos, decisões, versões e auditoria, com usuários autenticados e permissão por escola ou rede.

O ponto que impede reaproveitar a persistência atual está em `docs/deploy.md`: no Render gratuito, o disco é efêmero e "qualquer escrita em runtime é perdida quando o serviço reinicia/reimplanta". Uma Declaração emitida não pode desaparecer no próximo deploy.

## 2. O que permanece da Fase 1

- Frontend Next.js (App Router, TypeScript, Tailwind) na Vercel.
- Backend FastAPI no Render.
- ETL em Pandas, executado manualmente por edição do Censo, com o resultado como artefato somente leitura.
- Cadeia de provedores de IA com fallback e saída estruturada validada por Pydantic.
- Princípios: IA não decide números nem status; base legal só a pré-validada; cálculos determinísticos.

## 3. Decisões propostas

### AD-01 — Dois armazenamentos: Censo (leitura) e Gestão Ativa (escrita)

- **Dados do Censo** (escolas, municípios, UF, barreiras, narrativas públicas): continuam como artefato do ETL em SQLite, versionado e somente leitura.
- **Dados da Gestão Ativa** (usuários, vínculos, posições, declarações, planos, decisões, auditoria): banco **PostgreSQL gerenciado em plano gratuito**.
- **Ligação entre os dois:** pelo código INEP da escola (`CO_ENTIDADE`) e pelo código IBGE do município, mais a edição do Censo e a versão da metodologia de barreiras.
- **Alternativas consideradas:** (a) SQLite com disco persistente — exige plano pago no Render; (b) SQLite remoto (libSQL/Turso) — mantém o dialeto atual, mas é menos comum para dados transacionais com auditoria; (c) tudo em PostgreSQL — possível no futuro, mas obriga a mudar o ETL e o deploy da Fase 1 agora sem necessidade.
- **A verificar antes de escolher o provedor** (Neon, Supabase, Render Postgres ou outro): limite de armazenamento, política de pausa por inatividade, expiração do banco gratuito e disponibilidade de backup. Esses limites mudam com frequência e devem ser conferidos na data da escolha.
- **Backup:** como planos gratuitos costumam ter backup limitado, prever exportação periódica (por exemplo, `pg_dump` agendado) para armazenamento privado.

### AD-02 — Autenticação e autorização próprias no backend

- Evoluir a autenticação JWT atual do FastAPI para: papéis (diretor, secretário, administrador), tabela de vínculos (usuário × escola ou rede, com estado pendente, aprovado, revogado) e código de uso único por e-mail.
- **Autorização sempre no servidor:** toda rota da Gestão Ativa filtra pelo vínculo aprovado; mudar código na URL ou na requisição não amplia o escopo (RN-DMS-06).
- **Envio de e-mail:** provedor transacional com plano gratuito, a escolher (verificar cota diária e exigência de domínio próprio para remetente).
- **Tela de administração mínima:** aprovar, rejeitar e revogar vínculos, com registro de quem aprovou, quando e como (RF-06).
- **Alternativa considerada:** usar o serviço de autenticação do provedor de banco (por exemplo, Supabase Auth). Reduz trabalho com código e e-mail, mas a regra de vínculo continua sendo própria e o produto fica mais acoplado ao provedor. Pode ser reavaliado se AD-01 escolher esse provedor.
- **Autocadastro aberto da Fase 1:** desativado (ver AD-07).

### AD-03 — Versões imutáveis e trilha de auditoria

- Declarações, planos, decisões do secretário e planos municipais são gravados como **versões imutáveis**: uma nova versão é uma nova linha; versões emitidas, submetidas ou decididas nunca são atualizadas.
- Rascunhos são a única parte editável.
- Tabela de auditoria com quem, o quê, quando e sobre qual versão, para ações de emissão, publicação, submissão, decisão, aprovação de vínculo e revogação.
- Mensagens das conversas com IA são guardadas apenas o necessário para reproduzir o texto proposto e a revisão do usuário (minimização; retenção a definir).

### AD-04 — Barreiras e narrativa pública geradas pelo ETL

- Nova etapa do ETL gera a tabela de barreiras por escola, conforme a [metodologia de barreiras](../../../metodologia_barreiras.md), com edição do Censo e versão da metodologia.
- A narrativa municipal pública (opção 2 do Diagnóstico IA) é gerada **em lote**, uma vez por edição do Censo, e gravada no artefato somente leitura. Visitantes nunca disparam chamadas de IA.
- Consequência: a área pública continua funcionando mesmo se o banco da Gestão Ativa ou os provedores de IA estiverem indisponíveis.

### AD-05 — IA gratuita protegida por um Guardião LGPD local

**Decisão de 2026-10-18:** manter os provedores de IA em planos gratuitos. Como esses planos podem usar os dados enviados, a proteção fica do nosso lado: **nenhum dado pessoal sai do backend**, garantido por um Guardião LGPD.

- **Reaproveitar** a cadeia de provedores e a saída estruturada da Fase 1.
- **Guardião LGPD — componente local, sem chamadas externas.** Uma verificação feita por IA em nuvem enviaria o dado justamente para onde ele não pode ir; por isso o guardião roda no próprio backend, em três camadas:
  1. **Regras determinísticas:** CPF, RG, telefone, e-mail, datas de nascimento, números de matrícula e similares.
  2. **Reconhecimento de nomes de pessoas** com modelo local de linguagem natural em português, de pequeno porte, compatível com a memória do servidor gratuito.
  3. **Regras do contexto escolar:** combinações que identificam estudantes sem citar nome (por exemplo, "único aluno", estudante com deficiência associado a turma ou ano, menção a laudo).
- **Comportamento:**
  - **Mascarar e avisar** (padrão): o trecho é substituído por um marcador (por exemplo, `[NOME]`, `[ESTUDANTE]`) e o usuário vê o que foi mascarado antes do envio.
  - **Bloquear** em risco alto (documentos de identificação, dados de saúde como laudo): o envio não acontece até o usuário reescrever o trecho.
  - **Registrar** a ocorrência (tipo e quantidade de mascaramentos) sem guardar o dado original no registro.
- **Obrigatório por construção:** a única função do backend que chama provedores de IA recebe o texto já processado pelo guardião; não existe caminho alternativo. Testes automatizados com exemplos de dados pessoais verificam que nada passa sem mascaramento.
- **Mesmo componente na publicação:** a checagem antes de publicar a Declaração (RF-42) usa o guardião.
- **Aviso ao usuário** antes de cada conversa: não incluir nomes ou dados de estudantes; o texto passa por um filtro antes de ir para a IA, e o provedor é gratuito.
- **Escopo do contexto:** a IA recebe apenas dados da escola ou rede autorizada (RN-PAE-03, RN-SAB-01).
- **Sem IA disponível:** os registros já confirmados permanecem e o usuário segue sem a sugestão (requisito transversal do PRD).
- **Risco residual aceito:** nenhum filtro detecta 100% dos casos. O risco é reduzido pelas três camadas, pelo aviso e pela revisão humana do texto antes do envio, e deve ser reavaliado se o produto sair do piloto.
- **Implementação (2026-10-23):** `backend/app/shared/guardiao_lgpd/`. Camada 2 com spaCy `pt_core_news_sm` (cerca de 80 MB a mais de memória), lista local de prenomes e sobrenomes frequentes e exceções para nomes públicos (municípios do artefato do Censo, escolas, leis). Revisado duas vezes pelo AgLGPD; os casos da revisão estão em `backend/tests/test_guardiao_lgpd_regressao.py`, que é o conjunto de regressão da taxa de detecção. Riscos residuais conhecidos: endereço só é mascarado em frase com "mora", "reside", "endereço" ou "CEP"; nome com maiúscula no início da frase que também é palavra comum depende do modelo. Integração com a chamada aos provedores pendente.

### AD-06 — Hospedagem gratuita com mitigação de inatividade

- Manter Vercel e Render em planos gratuitos.
- O backend gratuito "dorme" após 15 minutos e leva de 30 a 60 segundos para responder na primeira chamada. Mitigação na interface: estado claro de "conectando ao servidor" e salvamento local do rascunho em andamento no navegador até a confirmação do servidor.
- Manter o serviço acordado com chamadas periódicas é tecnicamente possível, mas depende da política de uso do provedor e da cota mensal; verificar antes de adotar.

### AD-07 — Contas e conversas da Fase 1

- O autocadastro aberto e o chat público do Diagnóstico IA são encerrados.
- Contas existentes: aviso aos usuários e exclusão ou anonimização após prazo definido; conversas armazenadas seguem a mesma regra. Observação: no ambiente atual de produção, o banco é recriado a cada deploy, o que limita o volume real de contas e conversas persistidas — confirmar antes de definir o procedimento.

### AD-08 — Recuperação de contexto para a IA (RAG em camadas)

**Proposta de 2026-10-23.** Com IA gratuita não há treinamento nem ajuste fino; a precisão vem do contexto entregue em cada chamada. Cada tipo de conhecimento é recuperado pela técnica que lhe dá mais exatidão — busca por similaridade só onde a pergunta é imprevisível. Diagrama: [diagrama_ia_rag.html](diagrama_ia_rag.html).

**Camadas de contexto:**

| Camada | Conteúdo | Recuperação |
|---|---|---|
| C1 — Fatos da escola | Score, faixa, indicadores e barreiras da escola ou rede autorizada | Consulta SQL ao artefato do Censo (`incluia.db`). Nunca por busca vetorial: o dado precisa ser exato e a IA não decide números. |
| C2 — Metodologia | `metodologia_score.md` e `metodologia_barreiras.md`, na versão usada pelo ETL | Injeção por chave: cada barreira ou eixo traz a sua seção. |
| C3 — Corpus normativo | Base legal validada (`base/legislacao/`, [legislacao.md](../../legislacao.md)) e, depois, documentos de políticas públicas de educação | (a) **Mapa curado** barreira/eixo → dispositivos, ampliando o mapeamento eixo → base legal já existente; (b) **busca híbrida** para perguntas livres. |
| C4 — Contexto privado | Declaração emitida, posições, plano em edição, decisões | Injeção direta, filtrada pelo vínculo aprovado (AD-02, RN-PAE-03, RN-SAB-01). |

**Base de conhecimento como artefato do ETL** (mesmo padrão do AD-04):

- Um script offline lê o corpus, divide por **estrutura legal** (artigo, parágrafo, inciso; seção nos documentos não normativos), gera embeddings e grava tudo num arquivo somente leitura e versionado. O backend em execução só lê.
- Metadados por trecho: documento, dispositivo, data, vigência (vigente, alterado, revogado), URL oficial, data de consulta e versão da base.
- Busca por palavra-chave com SQLite FTS5 (embutido, sem custo de memória nem chamada externa); busca vetorial por força bruta em numpy, suficiente para alguns milhares de trechos; resultados combinados por classificação recíproca (RRF, do inglês Reciprocal Rank Fusion).
- **Fallback:** sem a API de embeddings (falha ou cota), a busca segue só por palavra-chave.
- Inclusão de documento no corpus exige registro em [legislacao.md](../../legislacao.md) ou em lista equivalente de fontes validadas — a regra "nunca citar o que não está validado" continua valendo.

**Montagem e validação da chamada:**

1. O texto do usuário passa pelo Guardião LGPD (AD-05) **antes** de qualquer chamada externa — inclusive a de embeddings, que também envia texto ao provedor.
2. O montador de contexto junta C1, C2, C3 e C4 e corta pelo **orçamento de tokens do provedor mais restrito da cadeia**, para que o fallback não falhe por tamanho (referência inicial: 4 a 6 trechos normativos).
3. A saída estruturada (Pydantic) exige, em cada afirmação normativa, os identificadores dos trechos usados. O backend **rejeita** citação de identificador que não foi entregue no contexto e aciona nova tentativa ou o próximo provedor.
4. Sem trecho de suporte, a resposta deve declarar a lacuna ("não encontrei base normativa"), rotulada como tal (RN-SAB-03).
5. Evitar técnicas que gastam chamadas extras (reescrita de pergunta, reordenação por LLM) enquanto a IA for gratuita.

**Geração em lote:** textos que não dependem da conversa (explicação de cada barreira e sua base legal, narrativa municipal) são gerados uma vez por edição do Censo ou da base, revisados e gravados no artefato (AD-04). Chamadas ao vivo ficam para o chat do Plano de Ação e o Analítico.

**Conteúdo privado não vai para embedding externo:** declarações e planos usados no Analítico do secretário são buscados apenas por FTS5 local; um modelo local de embeddings só será adotado se couber na memória do servidor junto com o modelo de nomes do Guardião.

**Avaliação:** conjunto de 30 a 50 perguntas reais de diretores e secretários, cada uma com a fonte esperada, para medir se a busca traz o trecho certo (revocação nos primeiros resultados) e se as citações da resposta são válidas. Reexecutado a cada nova versão da base ou mudança de provedor.

## 4. Riscos do plano gratuito

| Risco | Efeito | Mitigação |
|---|---|---|
| Pausa ou expiração do banco gratuito | Gestão Ativa indisponível ou perda de dados | Conferir a política na escolha (AD-01); backup periódico |
| Cotas de IA gratuitas | Sugestões indisponíveis em picos | Fallback entre provedores; fluxo continua sem IA |
| Cota de e-mail | Códigos de acesso não enviados | Cota dimensionada ao número de diretores do piloto |
| Backend que dorme | Primeira resposta lenta | AD-06 |
| Limites mudam sem aviso | Quebra de funcionamento | Revisar limites a cada etapa; documentar provedores e cotas em `docs/deploy.md` |
| Cota ou indisponibilidade da API de embeddings | Busca normativa menos precisa | Fallback para FTS5 (AD-08) |
| Contexto maior que o limite de um provedor gratuito | Fallback falha por tamanho | Orçamento de tokens pelo provedor mais restrito (AD-08) |
| Modelo descontinuado no plano gratuito | Cadeia de IA quebra | Conferir modelos e cotas na escolha; hoje o código fixa `gemini-2.0-flash` |

## 5. Decisões pendentes

1. Escolher o modelo local de reconhecimento de nomes e validar a taxa de detecção do Guardião LGPD com exemplos reais de relatos (AD-05).
2. Escolher o provedor de PostgreSQL após verificar os limites (AD-01).
3. Escolher o provedor de e-mail e o remetente (AD-02).
4. Prazo de retenção de conversas com IA e de rascunhos (AD-03).
5. Procedimento para contas e conversas da Fase 1 (AD-07).
6. Escala do piloto (quantas escolas e redes), que define se as cotas gratuitas bastam.
7. Provedor e modelo de embeddings (multilíngue, com plano gratuito), e se haverá modelo local (AD-08).
8. Lista inicial do corpus de políticas públicas, com fonte oficial e vigência de cada documento (AD-08).
9. Ampliar o mapeamento eixo → base legal para barreira → dispositivos, com validação jurídica (AD-08).
10. Conjunto de perguntas de avaliação e meta mínima de acerto antes do piloto (AD-08).
11. Vulnerabilidade social de um estudante identificável ("o pai está preso", "vive em abrigo", "sofre bullying"): bloquear como situação sensível ou só mascarar. Hoje passa sem tratamento, exceto Conselho Tutelar, medida protetiva e acolhimento institucional, que bloqueiam (AD-05).
