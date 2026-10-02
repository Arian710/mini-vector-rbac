"""
Text-Extraktion fuer den Selfservice-Dokumenten-Upload.

Nimmt rohe Datei-Bytes + Dateiname entgegen, gibt reinen Text zurueck - was
danach mit dem Text passiert (Embedding, Rollenvorschlag, Speicherung) weiss
dieses Modul bewusst nicht, genau wie embeddings.py nichts von RBAC weiss.
"""

import io
import os
import time

import pypdf
import requests
import tiktoken
from docx import Document as DocxDocument

# cl100k_base ist die Tokenizer-Kodierung, die text-embedding-3-small (und die
# meisten aktuellen OpenAI/Azure-OpenAI-Modelle) tatsaechlich verwendet - exakte
# Tokenzahl statt Wort-/Zeichen-Schaetzung, die bei technischem Text (Code,
# zusammengesetzte deutsche Woerter) leicht danebenliegt.
_ENCODING = tiktoken.get_encoding("cl100k_base")


class UnsupportedFileType(Exception):
    pass


DOCINTEL_API_VERSION = "2023-07-31"
MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER = 20  # darunter: vermutlich gescannt/bild-only, OCR versuchen


def _ocr_extract_pdf(data: bytes) -> str:
    """
    Fallback fuer PDFs ohne (ausreichende) Text-Ebene - typisch bei gescannten
    oder fotografierten Expose-Seiten. Nutzt Azure AI Document Intelligence
    (prebuilt-read-Modell) statt lokalem Tesseract, um die auf diesem Windows-
    Rechner wiederholt aufgetretenen DLL-Probleme bei lokalen OCR-Installs zu
    vermeiden (siehe Feature-Backlog).

    Gibt "" zurueck statt zu werfen, wenn OCR nicht konfiguriert ist oder
    fehlschlaegt - der Aufrufer faellt dann auf die (ggf. duerftige) pypdf-
    Extraktion zurueck, statt den ganzen Upload scheitern zu lassen.
    """
    endpoint = os.environ.get("AZURE_DOCINTEL_ENDPOINT")
    api_key = os.environ.get("AZURE_DOCINTEL_API_KEY")
    if not endpoint or not api_key:
        return ""

    try:
        submit_url = (
            f"{endpoint.rstrip('/')}/formrecognizer/documentModels/prebuilt-read:analyze"
            f"?api-version={DOCINTEL_API_VERSION}"
        )
        submit = requests.post(
            submit_url,
            headers={"Ocp-Apim-Subscription-Key": api_key, "Content-Type": "application/pdf"},
            data=data,
            timeout=30,
        )
        submit.raise_for_status()
        operation_url = submit.headers["Operation-Location"]

        # Analyse laeuft asynchron auf Azure-Seite - pollen bis "succeeded"/"failed",
        # max. ~60s (30 x 2s), laenger sollte eine einzelne PDF-Seite nicht brauchen.
        for _ in range(30):
            time.sleep(2)
            poll = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": api_key}, timeout=30)
            poll.raise_for_status()
            result = poll.json()
            if result["status"] == "succeeded":
                return result["analyzeResult"]["content"].strip()
            if result["status"] == "failed":
                return ""
        return ""
    except requests.exceptions.RequestException:
        return ""


def _extract_pdf(data: bytes) -> tuple:
    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()

    avg_chars_per_page = len(text) / max(len(pages), 1)
    if avg_chars_per_page < MIN_CHARS_PER_PAGE_FOR_TEXT_LAYER:
        ocr_text = _ocr_extract_pdf(data)
        if ocr_text:
            return ocr_text, True

    return text, False


def _extract_docx(data: bytes) -> tuple:
    doc = DocxDocument(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip(), False


def _extract_txt(data: bytes) -> tuple:
    return data.decode("utf-8", errors="replace").strip(), False


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


def extract_text(filename: str, data: bytes) -> tuple:
    """Gibt (text, ocr_used) zurueck - ocr_used ist nur bei PDFs ohne
    ausreichende Text-Ebene True, wenn Azure Document Intelligence erfolgreich
    eingesprungen ist (siehe _ocr_extract_pdf)."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    extractor = _EXTRACTORS.get(extension)
    if extractor is None:
        raise UnsupportedFileType(
            f"Dateityp '.{extension}' wird nicht unterstuetzt (erlaubt: PDF, DOCX, TXT)."
        )
    text, ocr_used = extractor(data)
    if not text:
        # ocr_used ist hier immer False: _extract_pdf liefert True nur bei
        # NICHT-leerem OCR-Ergebnis, sonst faellt es auf diesen Fehlerpfad.
        raise UnsupportedFileType(
            "Aus der Datei konnte kein Text extrahiert werden (leer, oder gescannt und OCR "
            "nicht konfiguriert/fehlgeschlagen)."
        )
    return text, ocr_used
