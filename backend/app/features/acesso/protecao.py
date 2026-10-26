"""Proteções transversais das rotas da Gestão Ativa (revisões do AgLGPD de 2026-10-23 e 24).

- `exigir_configuracao`: fora de `AMBIENTE=dev`, sem segredos ou sem provedor de e-mail, a Gestão
  Ativa responde 503 em vez de rodar com padrões inseguros; o site público segue no ar.
- `Limitador`: poucas requisições por IP numa janela. Em memória, por processo: suficiente para o
  piloto num único servidor; com mais instâncias, trocar por armazenamento compartilhado.
  - `limitar_por_ip`: rotas anônimas do acesso (força bruta do código espalhada por várias contas);
  - `limitar_rota_publica`: Declaração publicada (raspagem e esgotamento da cota do banco gratuito).
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.shared.ambiente import problemas_da_gestao


def exigir_configuracao() -> None:
    if problemas_da_gestao():
        # Os detalhes ficam no log de subida (main.py); a resposta não descreve a configuração.
        raise HTTPException(503, "A Gestão Ativa está indisponível neste servidor.")


class Limitador:
    def __init__(self, limite: int, janela_segundos: int):
        self.limite = limite
        self.janela = janela_segundos
        self._acessos: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "desconhecido"
        agora = time.monotonic()
        with self._trava:
            fila = self._acessos[ip]
            while fila and fila[0] < agora - self.janela:
                fila.popleft()
            if len(fila) >= self.limite:
                raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos e tente de novo.")
            fila.append(agora)

    def zerar(self) -> None:
        with self._trava:
            self._acessos.clear()


limitar_por_ip = Limitador(limite=30, janela_segundos=600)
limitar_rota_publica = Limitador(limite=120, janela_segundos=600)

# Compatibilidade com quem importa as constantes antigas.
LIMITE_POR_IP = limitar_por_ip.limite
JANELA_SEGUNDOS = limitar_por_ip.janela


def zerar_limites() -> None:
    """Para os testes."""
    limitar_por_ip.zerar()
    limitar_rota_publica.zerar()
