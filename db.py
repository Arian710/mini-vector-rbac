"""
MiniVectorDB - eine winzige Vektordatenbank mit serverseitigem Rollenfilter.

Diese Datei setzt die 5 Konzepte aus unserem Dialog in Code um:
  Konzept 1: Vektor       -> Zahlenlisten (numpy-Arrays), die Punkte im Raum sind
  Konzept 2: Embedding    -> text_to_vector() uebersetzt Text in so einen Punkt
  Konzept 3: Cosine Sim.  -> cosine_similarity() misst den Winkel zwischen zwei Vektoren
  Konzept 4: Brute-Force  -> search() vergleicht die Query stur mit JEDEM Eintrag
  Konzept 5: RBAC         -> der Rollenfilter sitzt INNERHALB von search(), nicht
                              irgendwo "danach" beim Aufrufer
"""

import hashlib
import re

import numpy as np

VECTOR_DIM = 64

# Sehr haeufige deutsche Woerter, die in praktisch jedem Satz vorkommen und daher
# keine thematische Unterscheidungskraft haben - wir ignorieren sie, damit die
# inhaltlich wichtigen Woerter (z.B. "Gehalt", "Drucker") staerker ins Gewicht fallen.
STOPWORDS = {
    "der", "die", "das", "und", "ist", "im", "in", "zu", "auf", "fuer",
    "mit", "von", "wird", "wurde", "ein", "eine", "einen", "einem",
    "nicht", "mehr", "noch", "sich", "bei", "um", "als", "an", "aus",
    "dem", "des", "den", "sind", "hat", "haben", "werden", "ueber",
    "seit", "heute",
}

_WORD_RE = re.compile(r"[a-zäöüß]+")


def _tokenize(text: str) -> list:
    words = _WORD_RE.findall(text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _hash_index(word: str, dim: int) -> int:
    # md5 statt Pythons eingebautem hash(), weil hash() fuer Strings pro Prozess
    # randomisiert ist - wir brauchen aber ein Ergebnis, das bei jedem Lauf gleich
    # ist, sonst waeren unsere Vektoren nicht reproduzierbar.
    digest = hashlib.md5(word.encode("utf-8")).hexdigest()
    return int(digest, 16) % dim


def text_to_vector(text: str, dim: int = VECTOR_DIM) -> np.ndarray:
    """
    Vereinfachtes Platzhalter-Embedding (Konzept 2).

    WICHTIG: Das hier ist bewusst KEIN trainiertes Modell, sondern ein simpler
    "Hashing-Trick": jedes Wort wird per Hash-Funktion einer festen Position im
    Vektor zugeordnet, und wir zaehlen, wie oft jedes Wort vorkommt. Das erkennt
    also nur Wortueberlappung, keine Synonyme oder echte Bedeutung (anders als ein
    echtes Embedding-Modell aus Konzept 2).

    Fuer eine echte Anwendung wuerde man diese Funktion durch einen API-Aufruf an
    ein trainiertes Embedding-Modell ersetzen - der Rest der Datenbank (Cosine
    Similarity, Suche, Rollenfilter) bliebe dabei komplett unveraendert.
    """
    vector = np.zeros(dim)
    for word in _tokenize(text):
        vector[_hash_index(word, dim)] += 1.0
    return vector


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine Similarity (Konzept 3): (a . b) / (|a| * |b|)

    Ergebnis liegt zwischen -1 (genau entgegengesetzte Richtung) und 1
    (exakt gleiche Richtung). Miss den Winkel zwischen zwei Vektoren,
    ignoriert dabei bewusst deren Laenge.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class MiniVectorDB:
    """Eine minimale Vektordatenbank mit eingebautem, serverseitigem Rollenfilter."""

    def __init__(self):
        self._entries = []  # jeder Eintrag: {"id", "text", "vector", "allowed_roles"}

    def add(self, ticket_id, text: str, allowed_roles: list) -> None:
        """
        Fuegt ein Dokument zur Datenbank hinzu.

        Konzept 2 (Embedding): der Text wird hier in einen Vektor uebersetzt und
        zusammen mit den erlaubten Rollen gespeichert. allowed_roles=["all"]
        bedeutet: jede Rolle darf dieses Dokument sehen.
        """
        vector = text_to_vector(text)
        self._entries.append({
            "id": ticket_id,
            "text": text,
            "vector": vector,
            "allowed_roles": allowed_roles,
        })

    def search(self, query: str, role: str, top_k: int = 3) -> list:
        """
        Sucht die aehnlichsten Dokumente zu einer Anfrage - aber NUR unter den
        Dokumenten, die die uebergebene Rolle ueberhaupt sehen darf.

        Konzept 5 (RBAC serverseitig): der Rollenfilter passiert als ALLERERSTER
        Schritt, bevor ueberhaupt eine Aehnlichkeit berechnet wird. Ein Dokument,
        das diese Rolle nicht sehen darf, verlaesst diese Methode nie - egal wie
        gut es inhaltlich passen wuerde. Es gibt keinen Aufrufer-Code, der diesen
        Filter vergessen oder umgehen koennte, weil er nicht "aussen", sondern
        hier drin sitzt.

        Konzept 4 (Brute-Force): auf der erlaubten Teilmenge wird wirklich JEDER
        Eintrag durchgerechnet - kein Index, keine Abkuerzung.

        Konzept 3 (Cosine Similarity): der Aehnlichkeitswert pro Eintrag.
        """
        query_vector = text_to_vector(query)

        # RBAC-Filter zuerst - nicht als nachtraeglicher Schritt.
        allowed_entries = [
            entry for entry in self._entries
            if "all" in entry["allowed_roles"] or role in entry["allowed_roles"]
        ]

        scored = [
            (cosine_similarity(query_vector, entry["vector"]), entry)
            for entry in allowed_entries
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            {"id": entry["id"], "text": entry["text"], "score": round(score, 4)}
            for score, entry in scored[:top_k]
        ]
