"""Prompt do chat de ajuste por eixo — RN-09 de docs/business-rules/diagnostico-ia.md.

Os trechos legais abaixo são citações literais curadas de base/legislacao/ (não lidas em tempo de
execução — RNF-02 pede contexto enxuto, e o texto legal por eixo não muda entre chamadas). Cada
trecho tem a fonte exata em comentário, espelhando docs/legislacao.md — nunca adicionar uma citação
aqui sem primeiro registrá-la lá.

Nota técnica: isto NÃO é RAG (Retrieval-Augmented Generation). Não há embeddings, índice vetorial
nem busca por similaridade — o trecho por eixo é fixo, escolhido manualmente em tempo de escrita
do código (ver arquitetura.md "Grounding legal — não é RAG" para a justificativa). Só migrar para
RAG de verdade se o corpus legal crescer a ponto de um trecho fixo por eixo não ser mais suficiente.
"""

from typing import Literal

from app.shared.guardiao_lgpd import TextoProtegido

EixoRomano = Literal["I", "II", "III", "IV"]

# Fonte: base/legislacao/decreto_12686_2025_pneei.md, Art. 5º a 10.
_BASE_LEGAL_EIXO_I = """Decreto 12.686/2025 (PNEEI), Art. 5º a 10 — organização do AEE:
- Art. 5º: "O Atendimento Educacional Especializado - AEE é atividade pedagógica de caráter \
complementar à escolarização de pessoas com deficiência e transtorno do espectro autista, e \
suplementar à escolarização de pessoas com altas habilidades ou superdotação."
- Art. 8º: "A matrícula no AEE não poderá ser substitutiva à matrícula e à frequência na classe \
comum.\""""

# Fonte: base/legislacao/lei_13146_2015_lbi_art27_a_30.md, Art. 28, II e XVI.
_BASE_LEGAL_EIXO_II = """Lei 13.146/2015 (LBI), Art. 28, incisos II e XVI:
- II: "aprimoramento dos sistemas educacionais, visando a garantir condições de acesso, \
permanência, participação e aprendizagem, por meio da oferta de serviços e de recursos de \
acessibilidade que eliminem as barreiras e promovam a inclusão plena."
- XVI: "acessibilidade para todos os estudantes, trabalhadores da educação e demais integrantes \
da comunidade escolar às edificações, aos ambientes e às atividades concernentes a todas as \
modalidades, etapas e níveis de ensino.\""""

# Fonte: base/legislacao/lei_13146_2015_lbi_art27_a_30.md, Art. 28, XI, XII e § 2º.
_BASE_LEGAL_EIXO_III = """Lei 13.146/2015 (LBI), Art. 28, incisos XI e XII, e § 2º:
- XI: "formação e disponibilização de professores para o atendimento educacional especializado, \
de tradutores e intérpretes da Libras, de guias intérpretes e de profissionais de apoio."
- XII: "oferta de ensino da Libras, do Sistema Braille e de uso de recursos de tecnologia \
assistiva, de forma a ampliar habilidades funcionais dos estudantes."
- § 2º, I: "os tradutores e intérpretes da Libras atuantes na educação básica devem, no mínimo, \
possuir ensino médio completo e certificado de proficiência na Libras.\""""

# Fonte: base/legislacao/decreto_12686_2025_pneei.md, Art. 1º § 3º e Art. 8º.
_BASE_LEGAL_EIXO_IV = """Decreto 12.686/2025 (PNEEI), Art. 1º § 3º e Art. 8º:
- Art. 1º, § 3º: "A garantia do sistema educacional inclusivo ocorre por meio da organização do \
sistema educacional geral, de forma a assegurar que os estudantes que são o público da educação \
especial estejam incluídos em classes e escolas comuns, com o apoio necessário à sua \
participação, permanência e aprendizagem."
- Art. 8º: "A matrícula no AEE não poderá ser substitutiva à matrícula e à frequência na classe \
comum.\""""

_BASE_LEGAL_POR_EIXO: dict[EixoRomano, str] = {
    "I": _BASE_LEGAL_EIXO_I,
    "II": _BASE_LEGAL_EIXO_II,
    "III": _BASE_LEGAL_EIXO_III,
    "IV": _BASE_LEGAL_EIXO_IV,
}

_FORMATO_SAIDA_CHAT = """Responda em JSON com exatamente esta estrutura:
{
  "resposta": "sua resposta em texto corrido para a mensagem do gestor",
  "recomendacoesAtualizadas": [
    {"acao": "...", "custoEstimado": "R$ ...", "prazo": "... meses", "impactoAlunos": <inteiro>, "fundamentacao": "..."}
  ] ou null se o gestor não pediu (ou você não está propondo) uma revisão da recomendação
}"""


def montar_system_prompt_chat(eixo_romano: EixoRomano, contexto_diagnostico: dict) -> str:
    base_legal = _BASE_LEGAL_POR_EIXO[eixo_romano]
    return f"""Você é um especialista em educação especial e política pública brasileira, \
conversando com um gestor de secretaria municipal ou estadual de educação sobre o diagnóstico \
de um eixo específico do Score Escola Sem Barreiras.

Contexto do diagnóstico atual (não reavalie, apenas use como referência):
- Município: {contexto_diagnostico['nome_municipio']} — {contexto_diagnostico['uf']}
- Eixo: {contexto_diagnostico['eixo_label']}
- Status já calculado: {contexto_diagnostico['status']}
- Valor do indicador: {contexto_diagnostico['valor']} ({contexto_diagnostico['subtexto']})
- Análise gerada anteriormente: {contexto_diagnostico['analise']}
- Recomendações atuais: {contexto_diagnostico['recomendacoes']}

Base legal que você PODE citar para este eixo — nunca cite artigo ou lei fora desta lista:
{base_legal}

Regras estritas:
- Nunca invente dados nem cite artigo/lei fora da base legal acima.
- Nunca decida ou sugira mudar o status (✅/⚠️/❌) ou o score do eixo — isso é calculado \
deterministicamente e está fora do escopo desta conversa; se perguntado, explique que você só \
pode discutir a análise e as recomendações, não o veredito.
- Se o gestor pedir um ajuste na recomendação (custo, prazo, ação, prioridade), responda com uma \
lista completa e atualizada em "recomendacoesAtualizadas" — cada item continua exigindo custo \
estimado e prazo, nunca deixe em branco. Se for só uma pergunta, deixe esse campo null.
- Ao discutir conformidade legal, reforce que a análise é uma aproximação metodológica do \
produto, sem substituir validação jurídica formal.
- Responda em português do Brasil, tom profissional e direto.
- Responda APENAS com um JSON válido no formato pedido, sem markdown, sem texto fora do JSON.

{_FORMATO_SAIDA_CHAT}"""


def montar_mensagens_chat(historico: list[dict], nova_mensagem: TextoProtegido) -> list[dict]:
    return [*historico, {"role": "user", "content": nova_mensagem}]


INSTRUCAO_REPROCESSAMENTO = (
    "Considerando toda a conversa acima com o gestor, gere a versão final e "
    "atualizada deste diagnóstico, incorporando os ajustes pedidos e os "
    "esclarecimentos discutidos. Responda no mesmo formato JSON pedido no início "
    "desta conversa (situacao, analise, alertaLegal, recomendacoes, "
    "referenciaMunicipio)."
)


def montar_mensagens_reprocessamento(
    prompt_inicial: TextoProtegido, historico: list[dict], instrucao: TextoProtegido
) -> list[dict]:
    """RN-10: reprocessamento explícito (botão) — o mesmo prompt inicial do diagnóstico automático
    (montar_prompt_usuario, de prompts.py) seguido de toda a conversa do chat e da instrução
    INSTRUCAO_REPROCESSAMENTO, pedindo uma versão final que incorpore os ajustes discutidos. Usa o
    SYSTEM_PROMPT normal do diagnóstico (não o de chat) porque a saída esperada é o RespostaIA
    completo (situação/análise/alerta/recomendações), não o RespostaChatIA. Todas as partes chegam
    já protegidas (AD-05)."""
    return [
        {"role": "user", "content": prompt_inicial},
        *historico,
        {"role": "user", "content": instrucao},
    ]
