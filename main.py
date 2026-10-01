"""
Demo: zeigt MiniVectorDB direkt (ohne die Web-API/Login-Schicht), mit aus
SQLite geladenen, bereits embeddeten Tickets.

Zeigt gezielt Konzept 6 (Multi-Tenancy): dieselbe Anfrage, dieselbe Rolle
"management", aber zwei verschiedene Tenants - jeder sieht nur sein eigenes,
sehr aehnlich formuliertes Gehalts-Ticket, nie das des anderen Mandanten.

Vorher einmal ausfuehren:  python seed_data.py
"""

import storage
from db import MiniVectorDB
from embeddings import get_default_embedder


def build_database() -> MiniVectorDB:
    storage.init_db()
    tickets = storage.load_tickets()
    if not tickets:
        raise RuntimeError("Keine Tickets in der Datenbank. Zuerst 'python seed_data.py' ausführen.")
    # Derselbe Embedder wie beim Seeden - sonst landet die Query in einem
    # anderen Vektorraum als die gespeicherten Tickets.
    db = MiniVectorDB(embedder=get_default_embedder())
    for ticket in tickets:
        db.load_entry(ticket["id"], ticket["text"], ticket["vector"], ticket["allowed_roles"], ticket["tenant_id"])
    return db


def print_results(tenant_id: str, role: str, results: list) -> None:
    print(f"\n=== Suche als Rolle '{role}' bei Tenant '{tenant_id}' ===")
    if not results:
        print("  (keine sichtbaren Treffer)")
        return
    for r in results:
        print(f"  [{r['score']:.3f}] Ticket {r['id']}: {r['text']}")


def main() -> None:
    db = build_database()
    query = "Wie sieht es mit Gehaeltern und Budget im Unternehmen aus?"
    print(f'Suchanfrage: "{query}"')

    for tenant_id in ["kanzlei-mueller", "steuerberatung-schmidt"]:
        for role in ["support", "management"]:
            results = db.search(query, role=role, tenant_id=tenant_id, top_k=3)
            print_results(tenant_id, role, results)


if __name__ == "__main__":
    main()
