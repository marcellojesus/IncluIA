"""Gera de antemão a narrativa pública dos municípios de uma UF para a edição atual do Censo.

    python -m app.features.diagnostico_ia.cli gerar RJ [--limite 50]

Municípios que já têm narrativa guardada são pulados; os que caem no texto de reserva ficam para
uma próxima rodada.
"""

import argparse
import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.database import get_connection  # noqa: E402
from app.features.diagnostico_ia import service  # noqa: E402
from app.features.diagnostico_ia.db import ensure_schema  # noqa: E402


async def _gerar(uf: str, limite: int | None) -> None:
    conn = get_connection()
    try:
        codigos = [linha[0] for linha in conn.execute("SELECT co_municipio FROM municipios WHERE sg_uf = ? ORDER BY co_municipio", (uf.upper(),))]
    finally:
        conn.close()
    pendentes = [c for c in codigos if service.guardada(c) is None][:limite]
    print(f"{uf.upper()}: {len(codigos)} municípios, {len(pendentes)} sem narrativa nesta rodada.")
    for n, codigo in enumerate(pendentes, start=1):
        resultado = await service.obter_narrativa_municipio(codigo)
        completo = resultado is not None and all(e.modelo_usado != "dados_brutos" for e in resultado.eixos)
        print(f"  [{n}/{len(pendentes)}] {codigo}: {'ok' if completo else 'sem IA, tentar de novo depois'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)
    gerar = sub.add_parser("gerar", help="gera a narrativa dos municípios de uma UF")
    gerar.add_argument("uf")
    gerar.add_argument("--limite", type=int, default=None, help="no máximo N municípios nesta rodada")
    args = parser.parse_args()
    ensure_schema()
    asyncio.run(_gerar(args.uf, args.limite))


if __name__ == "__main__":
    main()
