"""
Demo: zeigt MiniVectorDB direkt (ohne die Web-API/Login-Schicht), mit aus
SQLite geladenen, bereits embeddeten Tickets.

Vorher einmal ausfuehren:  python seed_data.py
"""

import storage
from db import MiniVectorDB


def build_database() -> MiniVectorDB:
    storage.init_db()
    tickets = storage.load_tickets()
    if not tickets:
        raise RuntimeError("Keine Tickets in der Datenbank. Zuerst 'python seed_data.py' ausführen.")
    db = MiniVectorDB()
    for ticket in tickets:
        db.load_entry(ticket["id"], ticket["text"], ticket["vector"], ticket["allowed_roles"])
    return db


def print_results(role: str, results: list) -> None:
    print(f"\n=== Suche als Rolle '{role}' ===")
    if not results:
        print("  (keine sichtbaren Treffer)")
        return
    for r in results:
        print(f"  [{r['score']:.3f}] Ticket {r['id']}: {r['text']}")


def main() -> None:
    db = build_database()
    query = "Wie sieht es mit Gehaeltern und Budget im Unternehmen aus?"
    print(f'Suchanfrage: "{query}"')

    for role in ["support", "management"]:
        results = db.search(query, role=role, top_k=3)
        print_results(role, results)


if __name__ == "__main__":
    main()
