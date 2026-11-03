"""Entrega dos documentos em PDF (RF-31; RN-PDF-01 a 07): limite por conta, auditoria e resposta HTTP.

A montagem e a conferência pelo Guardião ficam em `app/shared/pdf`. Aqui:
- versão retirada por dado pessoal ou pedido de titular não sai em PDF (revisão do AgLGPD, A1): a tela
  continua mostrando aos mesmos usuários (AD-03), mas não sai cópia portátil do que se decidiu bloquear;
- cada download, entregue ou recusado, entra na auditoria, sem conteúdo (M3).
"""

import logging

from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from app.features.acesso.dependencias import SessaoGestao
from app.features.acesso.modelos import EventoAuditoria
from app.features.acesso.protecao import limitar_pdf
from app.shared.guardiao_lgpd import GuardiaoIndisponivel
from app.shared.pdf import Documento, DocumentoInseguro, gerar

logger = logging.getLogger(__name__)

MOTIVOS_LGPD = ("dado_pessoal", "pedido_de_titular")


def _auditar(sessao: Session, sessao_gestao: SessaoGestao, documento: Documento, resultado: str, detalhe: str) -> None:
    alvo_tipo, alvo_id = documento.alvo
    sessao.add(EventoAuditoria(
        ator_id=sessao_gestao.conta.id, acao="pdf_baixado", alvo_tipo=alvo_tipo, alvo_id=alvo_id, resultado=resultado,
        detalhe=f"{detalhe}; v{documento.versao}",
    ))
    sessao.commit()


def entregar(sessao: Session, sessao_gestao: SessaoGestao, documento: Documento, retirada_motivo: str | None = None) -> Response:
    limitar_pdf.contar(sessao_gestao.conta.id)
    if retirada_motivo in MOTIVOS_LGPD:
        _auditar(sessao, sessao_gestao, documento, "recusado", f"retirada por {retirada_motivo}")
        raise HTTPException(
            409, "Esta versão foi retirada da página pública por proteção de dados pessoais e não pode ser baixada. Consulte-a na plataforma.",
        )
    try:
        conteudo = gerar(documento)
    except DocumentoInseguro as erro:
        logger.warning("PDF bloqueado pelo Guardião (%s, versão %s): %s", documento.alvo[0], documento.versao, erro.tipos)
        _auditar(sessao, sessao_gestao, documento, "recusado", "guardiao")
        raise HTTPException(
            409, "Esta versão tem trecho que parece dado pessoal e o PDF não foi gerado. Fale com a administração da plataforma.",
        ) from None
    except GuardiaoIndisponivel:
        raise HTTPException(503, "O filtro de dados pessoais está indisponível. Tente de novo em instantes.") from None
    _auditar(sessao, sessao_gestao, documento, "ok", "entregue")
    return Response(
        content=conteudo, media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{documento.nome_arquivo}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
