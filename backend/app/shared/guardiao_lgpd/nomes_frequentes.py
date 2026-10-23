"""Prenomes e sobrenomes frequentes no Brasil, sem acento e em minúsculas, para a camada 2.

Pega nomes que o modelo deixa passar ("O João tem autismo", "MARIA EDUARDA", "o joaozinho"),
independentemente de caixa. Ficam de fora prenomes que também são palavras comuns (Clara, Vitória,
Rosa, Luz, Glória, Graça, Lia, Taís, Mel, Aurora, Caio, Sara, Marina): esses dependem do modelo,
que usa a maiúscula.

Lista inicial montada à mão; pode ser substituída pela lista de nomes do Censo 2010 do IBGE.
"""

PRENOMES = frozenset(
    """
    adriana agatha alana alessandra alexandre alice aline allana amanda ana anderson andre andrea andressa
    angela anthony antonella antonia antonio arthur artur ayla barbara beatriz benicio benjamin benjamim
    bernardo bianca breno bruna bruno camila camilly carla carlos carolina catarina caua cecilia
    cesar charlotte cintia claudia claudio cristiane cristiano daniel daniela danilo davi david debora
    denise derick diego douglas edson eduarda eduardo elaine elias eliane eloa emanuel emanuelly emanuele
    emilly enzo erick esther estela ezequiel fabiana fabio felipe fernanda fernando flavia francisca
    francisco gabriel gabriela gabriele gabrielly gael giovana giovanna giovanni guilherme gustavo heitor
    helena heloisa henrique hugo iago ian igor isaac isabela isabella isabelle isabelly isadora italo
    jessica joana joao joaquim jonas jorge jose josue juan julia juliana julio kaique kaua kauan kelly
    kevin lara larissa laura lavinia leandro leonardo leticia levi livia lorena lorenzo luan luana lucas
    luca lucca luciana luciano luis luisa luiz luiza manoel manuel manuela marcela marcelo marcia marcio
    marcos maria mariana mateus matheus matias maya maite melissa miguel milena mirella moises
    murilo nathalia natalia nicolas nicole otavio patricia paula paulo pedro pietra pietro priscila
    rafael rafaela raimundo raquel raul rebeca renan renata renato ricardo rita roberta roberto rodrigo
    rogerio ryan samuel sandra sarah sergio simone sofia sophia sophie stella tatiane thalita theo
    thiago tiago valentim valentina vanessa vicente vinicius vitor victor wellington wesley william
    yasmin yuri
    """.split()
)

SOBRENOMES = frozenset(
    """
    almeida alves andrade araujo barbosa batista borges brito campos cardoso carvalho castro cavalcante
    conceicao correia costa cunha dias farias fernandes ferreira freitas goncalves gomes jesus lima lopes
    machado marques martins melo mendes monteiro moreira moura nascimento nunes oliveira pereira pinto
    ramos reis ribeiro rocha rodrigues santana santos silva soares souza sousa teixeira vieira xavier
    """.split()
)

CONECTORES = frozenset({"da", "de", "do", "das", "dos"})


def prenome_base(palavra: str) -> str | None:
    """Prenome da lista, aceitando diminutivo ("joaozinho" → joao, "pedrinho" → pedro)."""
    if palavra in PRENOMES:
        return palavra
    for sufixo in ("zinho", "zinha"):
        if palavra.endswith(sufixo) and palavra[: -len(sufixo)] in PRENOMES:
            return palavra[: -len(sufixo)]
    for sufixo, final in (("inho", "o"), ("inha", "a")):
        if palavra.endswith(sufixo) and palavra[: -len(sufixo)] + final in PRENOMES:
            return palavra[: -len(sufixo)] + final
    return None
