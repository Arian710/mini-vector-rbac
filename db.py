"""
MiniVectorDB - eine winzige Vektordatenbank mit serverseitigem Rollenfilter.

Diese Datei setzt 4 der 5 Konzepte aus unserem Dialog in Code um (das
Embedding selbst - Konzept 2 - steckt in embeddings.py und wird hier nur ueber
das Embedder-Interface benutzt, damit MiniVectorDB nicht wissen muss, ob im
Hintergrund ein Platzhalter oder Azure OpenAI laeuft):

  Konzept 3: Cosine Sim.  -> cosine_similarity() misst den Winkel zwischen zwei Vektoren
  Konzept 4: Brute-Force  -> search() vergleicht die Query stur mit JEDEM erlaubten Eintrag
  Konzept 5: RBAC         -> der Rollenfilter sitzt INNERHALB von search(), nicht
                              irgendwo "danach" beim Aufrufer
"""

import numpy as np

from embeddings import Embedder, HashingEmbedder


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine Similarity (Konzept 3): (a . b) / (|a| * |b|)

    Ergebnis liegt zwischen -1 (genau entgegengesetzte Richtung) und 1
    (exakt gleiche Richtung). Misst den Winkel zwischen zwei Vektoren,
    ignoriert dabei bewusst deren Laenge.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class MiniVectorDB:
    """Eine minimale Vektordatenbank mit eingebautem, serverseitigem Rollenfilter."""

    def __init__(self, embedder: Embedder = None):
        # Ein Embedder wird injiziert statt fest verdrahtet - so kann main.py
        # echte Azure-Embeddings nutzen, waehrend test_rbac.py bewusst den
        # kostenlosen HashingEmbedder erzwingt (offline, deterministisch).
        self._embedder = embedder or HashingEmbedder()
        self._entries = []  # jeder Eintrag: {"id", "text", "vector", "allowed_roles"}

    def add(self, ticket_id, text: str, allowed_roles: list) -> None:
        """
        Fuegt ein Dokument zur Datenbank hinzu.

        Konzept 2 (Embedding): der Text wird hier ueber den injizierten Embedder
        in einen Vektor uebersetzt und zusammen mit den erlaubten Rollen
        gespeichert. allowed_roles=["all"] bedeutet: jede Rolle darf dieses
        Dokument sehen.
        """
        vector = self._embedder.embed(text)
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
        hier drin sitzt. WICHTIG: `role` muss von einer vertrauenswuerdigen,
        serverseitigen Quelle kommen (siehe auth.py / api.py) - niemals direkt
        vom Client uebernommen werden.

        Konzept 4 (Brute-Force): auf der erlaubten Teilmenge wird wirklich JEDER
        Eintrag durchgerechnet - kein Index, keine Abkuerzung.

        Konzept 3 (Cosine Similarity): der Aehnlichkeitswert pro Eintrag.
        """
        query_vector = self._embedder.embed(query)

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
