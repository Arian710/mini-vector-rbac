"""
Demo: dieselbe Suchanfrage, gestellt von zwei Usern mit unterschiedlichen Rollen.
Zeigt, dass der Rollenfilter in db.py wirklich unterschiedliche Ergebnisse liefert -
nicht nur unterschiedlich angezeigte, sondern unterschiedlich ZURUECKGEGEBENE Daten.

Nutzt automatisch echte Azure-Embeddings, falls in .env konfiguriert, sonst den
kostenlosen Platzhalter-Embedder (siehe embeddings.py).
"""

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from data import TICKETS
from db import MiniVectorDB
from auth import get_role
from embeddings import get_default_embedder


def build_database() -> MiniVectorDB:
    embedder = get_default_embedder()
    print(f"Verwende Embedder: {type(embedder).__name__}")
    db = MiniVectorDB(embedder=embedder)
    for ticket in TICKETS:
        db.add(ticket["id"], ticket["text"], ticket["allowed_roles"])
    return db


def print_results(username: str, results: list) -> None:
    role = get_role(username)
    print(f"\n=== Suche als '{username}' (Rolle: {role}) ===")
    if not results:
        print("  (keine sichtbaren Treffer)")
        return
    for r in results:
        print(f"  [{r['score']:.3f}] Ticket {r['id']}: {r['text']}")


def main() -> None:
    db = build_database()
    query = "Wie sieht es mit Gehaeltern und Budget im Unternehmen aus?"
    print(f'Suchanfrage: "{query}"')

    for username in ["anna", "bernd"]:
        role = get_role(username)
        results = db.search(query, role=role, top_k=3)
        print_results(username, results)


if __name__ == "__main__":
    main()
