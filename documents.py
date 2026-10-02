"""
Text-Extraktion fuer den Selfservice-Dokumenten-Upload.

Nimmt rohe Datei-Bytes + Dateiname entgegen, gibt reinen Text zurueck - was
danach mit dem Text passiert (Embedding, Rollenvorschlag, Speicherung) weiss
dieses Modul bewusst nicht, genau wie embeddings.py nichts von RBAC weiss.
"""

import io

import pypdf
import tiktoken
from docx import Document as DocxDocument

# cl100k_base ist die Tokenizer-Kodierung, die text-embedding-3-small (und die
# meisten aktuellen OpenAI/Azure-OpenAI-Modelle) tatsaechlich verwendet - exakte
# Tokenzahl statt Wort-/Zeichen-Schaetzung, die bei technischem Text (Code,
# zusammengesetzte deutsche Woerter) leicht danebenliegt.
_ENCODING = tiktoken.get_encoding("cl100k_base")


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


MAX_CHUNK_TOKENS = 500  # klein genug fuer praezise Trefferabschnitte, weit unter dem 8191-Limit


def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list:
    """
    Teilt langen Text in mehrere Abschnitte, jeder einzeln einbettbar - statt
    Inhalt wegzuschneiden (wie eine simple Kuerzung es wuerde), wird ein langes
    Expose/eBook zu MEHREREN durchsuchbaren Dokumenten, jedes mit eigenem Vektor.
    Eine Suche findet so auch Inhalte tief in einem langen Dokument, nicht nur
    im ersten Abschnitt.

    Respektiert Absatzgrenzen (trennt nicht mitten im Satz), ausser ein einzelner
    Absatz ist selbst schon zu lang - dann wird er hart nach Tokens aufgeteilt.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_paragraphs = []
    current_tokens = 0

    def flush():
        if current_paragraphs:
            chunks.append("\n".join(current_paragraphs))

    for paragraph in paragraphs:
        paragraph_tokens = len(_ENCODING.encode(paragraph))

        if paragraph_tokens > max_tokens:
            flush()
            current_paragraphs, current_tokens = [], 0
            encoded = _ENCODING.encode(paragraph)
            for i in range(0, len(encoded), max_tokens):
                chunks.append(_ENCODING.decode(encoded[i:i + max_tokens]))
            continue

        if current_tokens + paragraph_tokens > max_tokens:
            flush()
            current_paragraphs, current_tokens = [], 0

        current_paragraphs.append(paragraph)
        current_tokens += paragraph_tokens

    flush()
    return chunks


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
