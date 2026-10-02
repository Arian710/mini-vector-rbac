"""
MiniVectorDB - eine winzige Vektordatenbank mit serverseitigem Tenant- und
Rollenfilter.

Diese Datei setzt mehrere Konzepte aus unserem Dialog in Code um (das
Embedding selbst - Konzept 2 - steckt in embeddings.py und wird hier nur ueber
das Embedder-Interface benutzt, damit MiniVectorDB nicht wissen muss, ob im
Hintergrund ein Platzhalter oder Azure OpenAI laeuft):

  Konzept 3: Cosine Sim.   -> cosine_similarity() misst den Winkel zwischen zwei Vektoren
  Konzept 4: Brute-Force   -> search() vergleicht die Query stur mit JEDEM erlaubten Eintrag
  Konzept 5: RBAC          -> der Rollenfilter sitzt INNERHALB von search(), nicht
                               irgendwo "danach" beim Aufrufer
  Konzept 6: Multi-Tenancy -> der Tenant-Filter sitzt VOR dem Rollenfilter, als
                               zusaetzliche, haertere Schranke
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
    """Eine minimale Vektordatenbank mit eingebautem, serverseitigem Tenant- und Rollenfilter."""

    def __init__(self, embedder: Embedder = None):
        # Ein Embedder wird injiziert statt fest verdrahtet - so kann main.py
        # echte Azure-Embeddings nutzen, waehrend test_rbac.py bewusst den
        # kostenlosen HashingEmbedder erzwingt (offline, deterministisch).
        self._embedder = embedder or HashingEmbedder()
        self._entries = []  # jeder Eintrag: {"id", "text", "vector", "allowed_roles", "tenant_id"}

    def add(self, ticket_id, text: str, allowed_roles: list, tenant_id: str, customer_label: str = None,
            source_document: str = None, chunk_index: int = None, chunk_total: int = None) -> None:
        """
        Fuegt ein Dokument zur Datenbank hinzu.

        Konzept 2 (Embedding): der Text wird hier ueber den injizierten Embedder
        in einen Vektor uebersetzt und zusammen mit den erlaubten Rollen und dem
        Mandanten (tenant_id) gespeichert. allowed_roles=["all"] bedeutet: jede
        Rolle INNERHALB DESSELBEN TENANTS darf dieses Dokument sehen - niemals
        tenant-uebergreifend. customer_label ist reine Organisations-Metadaten
        (z.B. "Kunde Mueller GmbH") - NIE eine Sicherheitsgrenze, das bleibt
        allein tenant_id/allowed_roles vorbehalten. source_document/chunk_index/
        chunk_total markieren Eintraege, die aus einem langen, in mehrere
        Abschnitte aufgeteilten Upload stammen (siehe documents.chunk_text) -
        bei kurzen Dokumenten bleiben sie None.
        """
        vector = self._embedder.embed(text)
        self._entries.append({
            "id": ticket_id,
            "text": text,
            "vector": vector,
            "allowed_roles": allowed_roles,
            "tenant_id": tenant_id,
            "customer_label": customer_label,
            "source_document": source_document,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
        })

    def load_entry(self, ticket_id, text: str, vector: np.ndarray, allowed_roles: list, tenant_id: str,
                    customer_label: str = None, source_document: str = None,
                    chunk_index: int = None, chunk_total: int = None) -> None:
        """
        Fuegt einen Eintrag mit BEREITS BERECHNETEM Vektor hinzu, z.B. beim
        Start aus der persistenten Datenbank geladen - ruft den Embedder NICHT
        erneut auf. Verhindert, dass bei jedem Neustart alle Texte erneut (und
        bei Azure: erneut kostenpflichtig) embedded werden muessen.
        """
        self._entries.append({
            "id": ticket_id,
            "text": text,
            "vector": vector,
            "allowed_roles": allowed_roles,
            "tenant_id": tenant_id,
            "customer_label": customer_label,
            "source_document": source_document,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
        })

    def __len__(self) -> int:
        return len(self._entries)

    def embed(self, text: str) -> np.ndarray:
        """Oeffentlicher Durchgriff auf den injizierten Embedder - fuer Code
        ausserhalb von MiniVectorDB (z.B. role_suggestion.py), ohne dass dieser
        Code den privaten Embedder selbst kennen oder konfigurieren muss."""
        return self._embedder.embed(text)

    def entries_for_tenant(self, tenant_id: str) -> list:
        """Alle Eintraege eines Tenants, UNGEFILTERT nach Rolle - nur fuer interne
        Server-Logik (z.B. role_suggestion.py), nie direkt ueber die API ausgeben."""
        return [entry for entry in self._entries if entry["tenant_id"] == tenant_id]

    def _allowed_entries(self, role: str, tenant_id: str) -> list:
        """Tenant-Filter (haerteste Schranke) dann RBAC-Filter - siehe search()."""
        same_tenant = [entry for entry in self._entries if entry["tenant_id"] == tenant_id]
        return [
            entry for entry in same_tenant
            if "all" in entry["allowed_roles"] or role in entry["allowed_roles"]
        ]

    def search(self, query: str, role: str, tenant_id: str, top_k: int = 3) -> list:
        """
        Sucht die aehnlichsten Dokumente zu einer Anfrage - aber NUR unter den
        Dokumenten, die (a) demselben Tenant gehoeren UND (b) die uebergebene
        Rolle ueberhaupt sehen darf.

        Konzept 6 (Multi-Tenancy): der Tenant-Filter ist die HAERTESTE und
        ERSTE Schranke - noch vor der Rolle. Ein Dokument eines anderen
        Tenants taucht nie auf, selbst wenn Rolle und allowed_roles perfekt
        passen wuerden. Zwei Mandanten koennen identisch benannte Rollen
        haben ("management" bei Kanzlei A und bei Kanzlei B) - das Tenant-Feld
        verhindert, dass das zu einer Verwechslung wird.

        Konzept 5 (RBAC serverseitig): der Rollenfilter passiert als naechster
        Schritt, bevor ueberhaupt eine Aehnlichkeit berechnet wird. Ein Dokument,
        das diese Rolle nicht sehen darf, verlaesst diese Methode nie - egal wie
        gut es inhaltlich passen wuerde. WICHTIG: `role` und `tenant_id` muessen
        von einer vertrauenswuerdigen, serverseitigen Quelle kommen (siehe
        auth.py / api.py) - niemals direkt vom Client uebernommen werden.

        Konzept 4 (Brute-Force): auf der erlaubten Teilmenge wird wirklich JEDER
        Eintrag durchgerechnet - kein Index, keine Abkuerzung.

        Konzept 3 (Cosine Similarity): der Aehnlichkeitswert pro Eintrag.
        """
        query_vector = self._embedder.embed(query)
        allowed_entries = self._allowed_entries(role, tenant_id)

        scored = [
            (cosine_similarity(query_vector, entry["vector"]), entry)
            for entry in allowed_entries
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            {
                "id": entry["id"],
                "text": entry["text"],
                "score": round(score, 4),
                "source_document": entry.get("source_document"),
                "chunk_index": entry.get("chunk_index"),
                "chunk_total": entry.get("chunk_total"),
            }
            for score, entry in scored[:top_k]
        ]

    def graph_data(self, role: str, tenant_id: str, top_neighbors: int = 5, min_similarity: float = 0.35) -> dict:
        """
        Liefert Knoten+Kanten fuer eine Obsidian-artige Graph-Ansicht - nutzt
        denselben Tenant-/RBAC-Filter wie search(), damit niemand ein Dokument
        auch nur als Punkt im Graph sieht, das er nicht lesen duerfte.

        WICHTIG fuer die Skalierung (siehe Feature-Backlog): bei vielen
        Dokumenten pro Tenant waere ein VOLLSTAENDIGER Graph (jeder mit jedem)
        O(n^2) Kanten - bei 1000 Dokumenten also bis zu ~500.000. Stattdessen
        bekommt jeder Knoten nur seine `top_neighbors` aehnlichsten Nachbarn,
        das haelt den Graph unabhaengig von der Tenant-Groesse renderbar.

        min_similarity filtert zusaetzlich schwache Kanten heraus (z.B. Platz 5
        von 5 moeglichen Nachbarn, aber inhaltlich kaum verwandt) - sonst wirkt
        der Graph bei vielen Dokumenten wie ein undurchsichtiger "Haarball"
        statt klar erkennbarer Themen-Cluster.
        """
        entries = self._allowed_entries(role, tenant_id)
        nodes = [
            {
                "id": entry["id"],
                "text": entry["text"],
                "restricted": "all" not in entry["allowed_roles"],
                "customer_label": entry.get("customer_label"),
                "source_document": entry.get("source_document"),
            }
            for entry in entries
        ]

        best_weight = {}
        for entry in entries:
            similarities = [
                (cosine_similarity(entry["vector"], other["vector"]), other["id"])
                for other in entries if other["id"] != entry["id"]
            ]
            similarities.sort(key=lambda pair: pair[0], reverse=True)
            for score, other_id in similarities[:top_neighbors]:
                if score < min_similarity:
                    continue
                key = frozenset((entry["id"], other_id))
                if key not in best_weight or score > best_weight[key]:
                    best_weight[key] = score

        edges = [
            {"source": min(pair), "target": max(pair), "weight": round(weight, 4)}
            for pair, weight in best_weight.items()
        ]
        return {"nodes": nodes, "edges": edges}
