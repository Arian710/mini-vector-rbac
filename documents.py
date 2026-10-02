"""
Text-Extraktion fuer den Selfservice-Dokumenten-Upload.

Nimmt rohe Datei-Bytes + Dateiname entgegen, gibt reinen Text zurueck - was
danach mit dem Text passiert (Embedding, Rollenvorschlag, Speicherung) weiss
dieses Modul bewusst nicht, genau wie embeddings.py nichts von RBAC weiss.
"""

import io

import pypdf
from docx import Document as DocxDocument


class UnsupportedFileType(Exception):
    pass


def _extract_pdf(data: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def _extract_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()


_EXTRACTORS = {
    "pdf": _extract_pdf,
    "docx": _extract_docx,
    "txt": _extract_txt,
}


def extract_text(filename: str, data: bytes) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    extractor = _EXTRACTORS.get(extension)
    if extractor is None:
        raise UnsupportedFileType(
            f"Dateityp '.{extension}' wird nicht unterstuetzt (erlaubt: PDF, DOCX, TXT)."
        )
    text = extractor(data)
    if not text:
        raise UnsupportedFileType("Aus der Datei konnte kein Text extrahiert werden (leer oder gescannt?).")
    return text
