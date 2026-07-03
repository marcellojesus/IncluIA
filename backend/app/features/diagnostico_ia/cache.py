"""RN-05 de docs/business-rules/diagnostico-ia.md: cache 24h, chave inclui a versão do Censo
para invalidação automática quando uma nova edição for processada."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database import get_connection
from app.features.diagnostico_ia.schemas import DiagnosticoEixo
from etl.config import CENSO_VERSAO

TTL = timedelta(hours=24)


def calcular_chave(codigo_ibge: int, eixo: str) -> str:
    bruto = f"{codigo_ibge}:{eixo}:{CENSO_VERSAO}"
    return hashlib.sha256(bruto.encode()).hexdigest()


def obter_do_cache(chave: str) -> Optional[DiagnosticoEixo]:
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT diagnostico, expira_em FROM cache_diagnosticos WHERE chave = ?", (chave,)
        ).fetchone()
        if linha is None:
            return None
        expira_em = datetime.fromisoformat(linha["expira_em"])
        if expira_em < datetime.now(timezone.utc):
            return None
        return DiagnosticoEixo.model_validate_json(linha["diagnostico"])
    finally:
        conn.close()


def salvar_no_cache(chave: str, codigo_ibge: int, eixo: str, diagnostico: DiagnosticoEixo) -> None:
    agora = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache_diagnosticos "
            "(chave, codigo_ibge, eixo, modelo_usado, diagnostico, gerado_em, expira_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                chave,
                codigo_ibge,
                eixo,
                diagnostico.modelo_usado,
                diagnostico.model_dump_json(),
                agora.isoformat(),
                (agora + TTL).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
