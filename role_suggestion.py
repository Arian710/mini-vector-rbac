"""
Automatischer Rollenvorschlag fuer neu hochgeladene Dokumente (Hybrid-Logik).

Generalisiert auf beliebige, vom Management selbst angelegte Rollen (siehe
storage.py: roles-Tabelle) - statt wie fruehert nur zwischen "all" und
"management" zu unterscheiden. Pro Rolle zaehlen zwei unabhaengige Signale:

1. Keyword-Heuristik: die ROLLE liefert ihre eigenen Stichworte ueber ihr
   description-Feld (z.B. Rolle "Buchhaltung" mit Beschreibung "Rechnungen,
   Mahnwesen, Kontoauszuege") - sofort verfuegbar, auch beim allerersten
   Dokument eines Tenants, aber leicht zu umgehen (Synonyme).
2. Embedding-Aehnlichkeit, zwei Varianten, der bessere Wert zaehlt:
   a) Vergleich mit dem Anker-Vektor der Rollenbeschreibung selbst (verfuegbar
      ab dem Moment, in dem die Rolle angelegt wird - loest das klassische
      Kaltstart-Problem, kein einziges Referenzdokument noetig).
   b) Vergleich mit dem Centroid bereits so eingestufter Dokumente - lernt mit
      wachsendem Datensatz dazu, braucht aber mindestens MIN_REFERENCE_DOCS.

Sicherheits-Bias bleibt bestehen: der Mensch bestaetigt oder uebersteuert den
Vorschlag immer manuell (siehe api.py) - hier wird nichts automatisch gespeichert.
"""

from __future__ import annotations

from db import cosine_similarity

MIN_REFERENCE_DOCS = 3
SIMILARITY_THRESHOLD = 0.35
KEYWORD_SCORE_BONUS = 0.5  # addiert auf den Embedding-Score, wenn ein Keyword trifft


def _keyword_hit(text: str, description: str) -> str | None:
    if not description:
        return None
    lowered = text.lower()
    for phrase in description.split(","):
        phrase = phrase.strip().lower()
        if phrase and phrase in lowered:
            return phrase
    return None


def _embedding_score(vector, role: dict, tenant_entries: list) -> tuple:
    """Gibt (bester Score, Erklaerungstext) zurueck, oder (None, None)."""
    best_score = None
    best_reason = None

    if role.get("vector") is not None:
        sim = cosine_similarity(vector, role["vector"])
        best_score, best_reason = sim, f"aehnlich zur Rollenbeschreibung '{role['name']}' ({sim:.2f})"

    same_role_vectors = [
        e["vector"] for e in tenant_entries if role["name"] in e["allowed_roles"]
    ]
    if len(same_role_vectors) >= MIN_REFERENCE_DOCS:
        centroid = sum(same_role_vectors) / len(same_role_vectors)
        sim = cosine_similarity(vector, centroid)
        if best_score is None or sim > best_score:
            best_score = sim
            best_reason = f"aehnlich zu bestehenden '{role['name']}'-Dokumenten ({sim:.2f})"

    return best_score, best_reason


def suggest_role(text: str, vector, tenant_entries: list, tenant_roles: list) -> dict:
    """
    tenant_entries: bereits gespeicherte Dokumente DESSELBEN Tenants (Format
    von MiniVectorDB._entries: dict mit "vector" + "allowed_roles").
    tenant_roles: Ergebnis von storage.list_roles(tenant_id) - die tatsaechlich
    fuer diesen Tenant definierten Rollen.

    Rueckgabe: {"suggested_role": str, "reasons": [str, ...]}. "all" ist der
    Fallback, wenn keine speziellere Rolle ausreichend Signal liefert - sie
    wird selbst nie aktiv vorgeschlagen (sie ist "nichts Besonderes erkannt",
    kein inhaltliches Thema).
    """
    candidates = []  # (score, role_name, reasons)

    for role in tenant_roles:
        if role["name"] == "all":
            continue

        reasons = []
        score = 0.0

        keyword = _keyword_hit(text, role.get("description"))
        if keyword:
            reasons.append(f"Begriff '{keyword}' (aus Rollenbeschreibung '{role['name']}') im Text gefunden")
            score += KEYWORD_SCORE_BONUS

        embedding_score, embedding_reason = _embedding_score(vector, role, tenant_entries)
        if embedding_score is not None and embedding_score >= SIMILARITY_THRESHOLD:
            reasons.append(embedding_reason)
            score += embedding_score

        if reasons:
            candidates.append((score, role["name"], reasons))

    if not candidates:
        return {
            "suggested_role": "all",
            "reasons": ["keine passende Rolle erkannt (keine Keywords/Aehnlichkeit ueber dem Schwellenwert)"],
        }

    candidates.sort(key=lambda c: c[0], reverse=True)
    _, best_role, best_reasons = candidates[0]
    return {"suggested_role": best_role, "reasons": best_reasons}
