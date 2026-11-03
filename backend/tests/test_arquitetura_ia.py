"""Spec: docs/sdd/fase-2/arquitetura.md AD-05 — "obrigatório por construção".

Garante que não existe caminho de texto até um provedor de IA sem passar pelo Guardião LGPD:
só `ai_client.py` acessa a rede, nenhum SDK de provedor é usado, só o guardião cria
`TextoProtegido`, `liberar_dados_publicos` só recebe argumentos conhecidos, e `gerar_resposta`
recusa qualquer outra coisa — no system prompt e nas mensagens.
"""

import ast
import re
import asyncio
from pathlib import Path

import pytest

from app.shared import ai_client
from app.features.diagnostico_ia.schemas import RespostaIA
from app.shared.guardiao_lgpd import GuardiaoIndisponivel, TextoBloqueado, liberar_dados_publicos, proteger

APP = Path(__file__).resolve().parents[1] / "app"
AI_CLIENT = APP / "shared" / "ai_client.py"
GUARDIAO = APP / "shared" / "guardiao_lgpd"

# Bibliotecas de rede: só o ai_client.py pode importar. Um módulo novo que precise de rede (por
# exemplo, envio de e-mail, AD-02) entra aqui depois de revisão do AgLGPD.
_REDE = {"httpx", "requests", "aiohttp", "urllib", "urllib3", "http", "socket"}
_PODEM_USAR_REDE = {AI_CLIENT}

# SDKs de provedores de IA: proibidos em todo o app (contornariam o ai_client.py).
_SDKS_DE_IA = {
    "google.generativeai", "google.genai", "vertexai", "groq", "mistralai", "openai", "anthropic",
    "cohere", "huggingface_hub", "together", "litellm", "langchain",
}

# Únicos argumentos aceitos por liberar_dados_publicos fora do guardião: modelos fixos e prompts
# montados só com dados agregados públicos. Acrescentar um exige revisão do AgLGPD.
_ARGUMENTOS_LIBERADOS = {
    "montar_prompt_usuario(contexto)",
    "SYSTEM_PROMPT",
    # contexto_ia/montador.py: fatos do Censo, metodologia, cabeçalho fixo e texto legal do corpus
    "_renderizar_fatos(escola, barreiras, foco, base)",
    "_CABECALHO_PRIVADO",
    "_renderizar_normas(trechos)",
    "INSTRUCOES_CITACAO",
    # declaracao/conversa.py: instruções fixas do assistente de registro
    "INSTRUCOES_REGISTRO",
    "INSTRUCAO_FORMALIZAR",
    "_FALA_REMOVIDA",
    "pergunta_inicial(codigo)",
    # plano/sugestoes.py: instruções fixas e pedido com o código da barreira
    "INSTRUCOES_PLANO",
    "pedido_de_sugestoes(codigo)",
    "INSTRUCAO_AJUSTE",
    "pedido_de_ajuste(sugestao.codigo)",
    "FORMATO_RESPOSTA_FUNDAMENTADA",
    # plano_municipal/sugestoes.py: instruções fixas e pedido com o código da barreira (validado na base da rede)
    "INSTRUCOES_MUNICIPAL",
    "pedido_municipal(codigo)",
    # contexto_ia/montador.py, rede: só contagens calculadas e a regra da metodologia (sem município nem escola) e cabeçalho fixo
    "_renderizar_fatos_rede(codigo, fatos, base.metodologia[codigo])",
    "_CABECALHO_ACOES_ESCOLAS",
    # analitico/sintese.py: instruções fixas e números da rede, sem município nem escolas
    "INSTRUCOES_ANALITICO",
    "renderizar_rede(rede)",
    "_CABECALHO_RELATOS",
    "PEDIDO_ANALITICO",
    # plano_municipal/narrativa.py (revisão do AgLGPD de 2026-10-27): instruções fixas, pedido fixo e a situação
    # da rede do Analítico em faixas; as ações vão por proteger(), sem nomes da rede. Cabeçalho fixo no montador.
    "INSTRUCOES_NARRATIVA",
    "PEDIDO_NARRATIVA",
    "sem_percentuais(sintese_analitica.renderizar_rede(rede))",
    "_CABECALHO_PLANO",
}


def _arquivos_do_app():
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


def _modulos_importados(arvore: ast.AST) -> set[str]:
    modulos = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            modulos |= {a.name for a in no.names}
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos.add(no.module)
    return modulos


def _comeca_com(modulo: str, raizes: set[str]) -> bool:
    return any(modulo == r or modulo.startswith(r + ".") for r in raizes)


def test_so_ai_client_acessa_a_rede_e_nenhum_sdk_de_ia_e_usado():
    for arquivo in _arquivos_do_app():
        modulos = _modulos_importados(ast.parse(arquivo.read_text(encoding="utf-8")))
        for modulo in modulos:
            assert not _comeca_com(modulo, _SDKS_DE_IA), f"{arquivo} importa o SDK {modulo}"
            if arquivo not in _PODEM_USAR_REDE:
                assert not _comeca_com(modulo, _REDE), f"{arquivo} importa {modulo} fora do ai_client.py"


def test_app_so_importa_do_etl_modulos_sem_rede():
    """O ETL chama a API de embeddings direto (só corpus público, offline). Se o app importasse esse
    código, texto de usuário poderia chegar ao provedor sem o guardião."""
    backend = APP.parent
    for arquivo in _arquivos_do_app():
        for modulo in _modulos_importados(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if not _comeca_com(modulo, {"etl"}):
                continue
            caminho = backend.joinpath(*modulo.split("."))
            fonte = caminho.with_suffix(".py") if caminho.with_suffix(".py").exists() else caminho / "__init__.py"
            importados = _modulos_importados(ast.parse(fonte.read_text(encoding="utf-8")))
            rede = [m for m in importados if _comeca_com(m, _REDE) or _comeca_com(m, {"etl.base_normativa"})]
            assert not rede, f"{arquivo} importa {modulo}, que usa {rede}"


def test_embeddings_do_etl_so_sao_usados_pelo_construtor_da_base():
    backend = APP.parent
    permitido = backend / "etl" / "base_normativa" / "construir.py"
    for arquivo in backend.rglob("*.py"):
        if ".venv" in arquivo.parts or "__pycache__" in arquivo.parts or arquivo == permitido:
            continue
        texto = arquivo.read_text(encoding="utf-8")
        modulos = _modulos_importados(ast.parse(texto))
        assert "etl.base_normativa.embeddings" not in modulos, f"{arquivo} importa os embeddings do ETL"
        assert not ("etl.base_normativa" in modulos and "import embeddings" in texto), f"{arquivo} importa os embeddings do ETL"


def test_chamadas_de_rede_do_ai_client_sao_privadas():
    """Toda função que faz requisição é privada e só é alcançada por `gerar_resposta`."""
    arvore = ast.parse(AI_CLIENT.read_text(encoding="utf-8"))
    for funcao in ast.walk(arvore):
        if not isinstance(funcao, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        faz_requisicao = any(
            isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute) and no.func.attr in {"post", "get", "send", "request", "stream"}
            for no in ast.walk(funcao)
        )
        if faz_requisicao:
            assert funcao.name.startswith("_"), f"ai_client.{funcao.name} faz requisição e é pública"
    for arquivo in _arquivos_do_app():
        if arquivo != AI_CLIENT:
            assert "ai_client._" not in arquivo.read_text(encoding="utf-8"), f"{arquivo} usa função privada do ai_client"


def test_so_o_guardiao_cria_texto_protegido():
    for arquivo in _arquivos_do_app():
        if GUARDIAO in arquivo.parents:
            continue
        conteudo = arquivo.read_text(encoding="utf-8")
        assert not re.search(r"\b_CHAVE\b", conteudo), f"{arquivo} usa a chave interna do guardião"
        assert "TextoProtegido(" not in conteudo, f"{arquivo} cria TextoProtegido diretamente"


def test_liberar_dados_publicos_so_com_argumentos_conhecidos():
    for arquivo in _arquivos_do_app():
        if GUARDIAO in arquivo.parents:
            continue
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Call) and getattr(no.func, "id", getattr(no.func, "attr", None)) == "liberar_dados_publicos":
                argumento = ast.unparse(no.args[0]) if no.args else ""
                assert argumento in _ARGUMENTOS_LIBERADOS, (
                    f"{arquivo}:{no.lineno} libera '{argumento}' sem o reconhecimento de nomes; "
                    "use proteger() ou revise com o AgLGPD"
                )


def test_liberar_dados_publicos_ainda_bloqueia_documento_e_saude():
    with pytest.raises(TextoBloqueado):
        liberar_dados_publicos("CPF 529.982.247-25")
    with pytest.raises(TextoBloqueado):
        liberar_dados_publicos("O aluno toma Ritalina.")


def test_juntar_protegidos_nao_aceita_texto_cru():
    from app.shared.guardiao_lgpd import juntar_protegidos

    protegido = proteger("Pergunta").texto_protegido
    with pytest.raises(TypeError):
        juntar_protegidos([protegido, "O Pedro é cego"])
    with pytest.raises(ValueError):
        juntar_protegidos([protegido, protegido], separador=" O Pedro é cego ")


def test_juntar_protegidos_revisa_dado_partido_entre_partes():
    from app.shared.guardiao_lgpd import juntar_protegidos

    inicio = proteger("Contato da família: CPF 529.982").texto_protegido
    fim = proteger(".247-25 conforme ficha").texto_protegido
    with pytest.raises(TextoBloqueado):
        juntar_protegidos([inicio, fim], separador="")


def _provedor_que_nao_pode_ser_chamado(*_args, **_kwargs):
    raise AssertionError("provedor chamado com texto não protegido")


def _sistema():
    return proteger("Você é um assistente.").texto_protegido


def test_gerar_resposta_recusa_texto_cru_nas_mensagens(monkeypatch):
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor_que_nao_pode_ser_chamado)])
    with pytest.raises(TypeError):
        asyncio.run(
            ai_client.gerar_resposta(_sistema(), [{"role": "user", "content": "O Pedro é cego"}], RespostaIA)
        )


def test_gerar_resposta_recusa_system_prompt_cru(monkeypatch):
    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", _provedor_que_nao_pode_ser_chamado)])
    mensagem = proteger("Pergunta").texto_protegido
    with pytest.raises(TypeError):
        asyncio.run(
            ai_client.gerar_resposta("O Pedro é cego", [{"role": "user", "content": mensagem}], RespostaIA)
        )


def test_gerar_resposta_envia_so_o_texto_mascarado(monkeypatch):
    recebido = {}

    async def provedor(system_prompt, mensagens):
        recebido["mensagens"] = mensagens
        return {"situacao": "ok", "analise": "ok"}

    monkeypatch.setattr(ai_client, "_PROVEDORES", [("teste", provedor)])
    protegido = proteger("O Pedro, do 3º ano, é cego.").texto_protegido
    asyncio.run(ai_client.gerar_resposta(_sistema(), [{"role": "user", "content": protegido}], RespostaIA))

    enviado = recebido["mensagens"][0]["content"]
    assert isinstance(enviado, str)
    assert "Pedro" not in enviado and "3º ano" not in enviado


def test_log_de_falha_nao_carrega_url_nem_resposta():
    import httpx
    from pydantic import BaseModel

    requisicao = httpx.Request("POST", "https://exemplo.invalid/v1?key=SEGREDO")
    erro_http = httpx.HTTPStatusError("erro", request=requisicao, response=httpx.Response(429, request=requisicao))
    assert "SEGREDO" not in ai_client.descrever_falha(erro_http)

    class Modelo(BaseModel):
        campo: int

    try:
        Modelo.model_validate({"campo": "O Pedro é cego"})
    except Exception as erro_validacao:  # noqa: BLE001
        assert "Pedro" not in ai_client.descrever_falha(erro_validacao)


# Funções que passam texto pelo Guardião só para gravar ou mostrar a resposta da IA, sem enviá-lo.
_PROTEGER_FORA_DO_ENVIO = {"_mascarado", "__call__", "responsavel"}


def test_texto_que_vai_a_ia_passa_pela_camada_de_locais():
    """Revisão do AgLGPD de 2026-11-03, M4: nos módulos que chamam a IA, todo texto de usuário passa por
    `proteger_para_ia`, que exige os locais da rede; `proteger` sem locais só onde nada vai à IA."""
    for arquivo in _arquivos_do_app():
        if GUARDIAO in arquivo.parents or arquivo.parent.name in ("contexto_ia", "diagnostico_ia") or arquivo.name == "ai_client.py":
            continue
        fonte = arquivo.read_text(encoding="utf-8")
        if "gerar_resposta" not in fonte:
            continue
        arvore = ast.parse(fonte)
        for funcao in [n for n in ast.walk(arvore) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if funcao.name in _PROTEGER_FORA_DO_ENVIO:
                continue
            for no in ast.walk(funcao):
                if isinstance(no, ast.Call) and getattr(no.func, "id", getattr(no.func, "attr", None)) in ("proteger", "proteger_ou_falhar"):
                    raise AssertionError(f"{arquivo}:{no.lineno} protege texto sem a camada de locais; use proteger_para_ia")


def test_proteger_para_ia_exige_os_locais():
    from app.shared.guardiao_lgpd import SEM_LOCAIS, proteger_para_ia

    with pytest.raises(TypeError):
        proteger_para_ia("Texto", ())
    # Sem nomes da rede (escola fora do Censo), o código de 8 dígitos ainda sai.
    assert "33055238" not in proteger_para_ia("Escola 33055238", SEM_LOCAIS).texto_mascarado
