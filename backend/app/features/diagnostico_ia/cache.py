"""Narrativa pública guardada por edição do Censo (decisão de 2026-10-18, impacto-fase-1.md opção 2).

Gerada uma vez por município, eixo e edição; não expira. Uma nova edição muda a chave e a narrativa
é escrita de novo. O texto de reserva sem IA (RN-02) não é guardado, para a IA ser tentada de novo.
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from app.database import get_connection
from app.features.diagnostico_ia.schemas import NarrativaEixo
from etl.config import CENSO_VERSAO

_VERSAO_DO_TEXTO = "publica-v2"
"""Muda quando o formato da narrativa muda; as linhas antigas da tabela deixam de ser lidas."""


def calcular_chave(codigo_ibge: int, eixo: str) -> str:
    bruto = f"{_VERSAO_DO_TEXTO}:{codigo_ibge}:{eixo}:{CENSO_VERSAO}"
    return hashlib.sha256(bruto.encode()).hexdigest()


def obter_do_cache(chave: str) -> Optional[NarrativaEixo]:
    conn = get_connection()
    try:
        linha = conn.execute("SELECT diagnostico FROM cache_diagnosticos WHERE chave = ?", (chave,)).fetchone()
    finally:
        conn.close()
    return NarrativaEixo.model_validate_json(linha["diagnostico"]) if linha else None


def salvar_no_cache(chave: str, codigo_ibge: int, narrativa: NarrativaEixo) -> None:
    agora = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache_diagnosticos "
            "(chave, codigo_ibge, eixo, modelo_usado, diagnostico, gerado_em, expira_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            # expira_em é coluna legada do cache de 24 h; a narrativa vale para a edição inteira.
            (chave, codigo_ibge, narrativa.eixo, narrativa.modelo_usado, narrativa.model_dump_json(), agora, "edicao:" + CENSO_VERSAO),
        )
        conn.commit()
    finally:
        conn.close()
