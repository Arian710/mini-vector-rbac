"""
Automatischer Rollenvorschlag fuer neu hochgeladene Dokumente (Hybrid-Logik).

Zwei unabhaengige Signale, beide koennen fuer "management" stimmen:

1. Keyword-Heuristik: sofort verfuegbar, funktioniert auch beim allerersten
   Dokument eines Tenants (kein Kaltstart-Problem), aber leicht zu umgehen
   (Synonyme, untypische Formulierung).
2. Embedding-Aehnlichkeit: vergleicht das neue Dokument per Cosine Similarity
   mit dem Durchschnittsvektor (Centroid) bereits eingestufter Dokumente
   desselben Tenants - lernt mit wachsendem Datensatz dazu, braucht aber
   mindestens MIN_REFERENCE_DOCS pro Kategorie, sonst wird sie uebersprungen.

Sicherheits-Bias: spricht AUCH NUR EINE der beiden Methoden fuer "management",
wird "management" vorgeschlagen - nie automatisch gespeichert, der Mensch
bestaetigt oder uebersteuert den Vorschlag immer manuell (siehe api.py).
"""

from __future__ import annotations

from db import cosine_similarity

MIN_REFERENCE_DOCS = 3

SENSITIVE_KEYWORDS = [
    "gehalt", "gehaltserhoehung", "bonuszahlung", "bonus", "kuendigung",
    "entlassung", "abfindung", "uebernahme", "uebernahmeangebot", "investor",
    "grossinvestor", "due diligence", "jahresabschluss", "quartalsergebnis",
    "umsatzrueckgang", "geschaeftsgeheimnis", "vertraulich", "streng vertraulich",
    "fusion", "m&a", "personalabbau", "restrukturierung",
]


def _keyword_hit(text: str) -> str | None:
    lowered = text.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword in lowered:
            return keyword
    return None


def _embedding_hit(vector, entries: list) -> str | None:
    management_vectors = [e["vector"] for e in entries if "all" not in e["allowed_roles"]]
    all_vectors = [e["vector"] for e in entries if "all" in e["allowed_roles"]]

    if len(management_vectors) < MIN_REFERENCE_DOCS or len(all_vectors) < MIN_REFERENCE_DOCS:
        return None

    mgmt_centroid = sum(management_vectors) / len(management_vectors)
    all_centroid = sum(all_vectors) / len(all_vectors)

    sim_to_mgmt = cosine_similarity(vector, mgmt_centroid)
    sim_to_all = cosine_similarity(vector, all_centroid)

    if sim_to_mgmt > sim_to_all:
        return f"aehnlicher zu bestehenden management-Dokumenten ({sim_to_mgmt:.2f} vs. {sim_to_all:.2f})"
    return None


def suggest_role(text: str, vector, tenant_entries: list) -> dict:
    """
    tenant_entries: bereits gespeicherte Dokumente DESSELBEN Tenants, im
    Format von MiniVectorDB._entries (dict mit "vector" + "allowed_roles").

    Rueckgabe: {"suggested_role": "management"|"all", "reasons": [str, ...]}
    """
    reasons = []

    keyword = _keyword_hit(text)
    if keyword:
        reasons.append(f"Begriff '{keyword}' im Text gefunden")

    embedding_reason = _embedding_hit(vector, tenant_entries)
    if embedding_reason:
        reasons.append(embedding_reason)

    suggested_role = "management" if reasons else "all"
    if not reasons:
        reasons.append("keine sensiblen Begriffe gefunden, keine aehnlichen management-Dokumente vorhanden")

    return {"suggested_role": suggested_role, "reasons": reasons}
