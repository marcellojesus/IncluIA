"""Documentos em PDF (RF-31). Spec: docs/sdd/fase-2/requirements/documentos-pdf.md (RN-PDF-01 a 07).

Cada feature monta um `Documento` a partir da versão congelada; aqui ficam o layout comum (cabeçalho,
rodapé, ressalvas, fonte), o código de conferência e a nova passada pelo Guardião LGPD. Nenhuma IA
é chamada e o arquivo não é guardado no servidor. A entrega (limite, auditoria e resposta HTTP) fica
em `app/features/acesso/entrega_pdf.py`.
"""

from app.shared.pdf.documento import (
    Bloco,
    Campo,
    Documento,
    DocumentoInseguro,
    Secao,
    USO_INTERNO,
    codigo_conferencia,
    conferir,
    data_hora,
    gerar,
)

__all__ = [
    "Bloco",
    "Campo",
    "Documento",
    "DocumentoInseguro",
    "Secao",
    "USO_INTERNO",
    "codigo_conferencia",
    "conferir",
    "data_hora",
    "gerar",
]
