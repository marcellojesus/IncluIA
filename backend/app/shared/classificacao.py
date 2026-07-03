"""Colapsa a régua de 5 faixas do Score IncluIA (metodologia_score.md §5) em 3 estados de
semáforo — usado por qualquer feature que precise de status ok/warn/nok a partir de um score
0-10 (ver docs/business-rules/indicadores-municipio.md RN-01 e docs/business-rules/escolas.md RN-02)."""

from typing import Literal

StatusSemaforo = Literal["ok", "warn", "nok"]


def status_semaforo(faixa: str) -> StatusSemaforo:
    if faixa == "Crítico":
        return "nok"
    if faixa in ("Adequado", "Referência"):
        return "ok"
    return "warn"
