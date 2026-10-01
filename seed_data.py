"""
Beispiel-Datensatz zum einmaligen Befuellen der persistenten SQLite-Datenbank.

Einmal ausfuehren:  python seed_data.py

Danach laden main.py und api.py die Tickets direkt aus der Datenbank, ohne
erneut zu embedden.

ACHTUNG: Die Demo-Passwoerter hier sind nur fuer lokales Ausprobieren gedacht -
so niemals in einer echten Anwendung verwenden.
"""

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import auth
import storage
from data import TICKETS
from embeddings import get_default_embedder

DEMO_USERS = [
    {"username": "anna", "password": "demo1234", "role": "support"},
    {"username": "bernd", "password": "demo1234", "role": "management"},
    {"username": "carla", "password": "demo1234", "role": "support"},
    {"username": "david", "password": "demo1234", "role": "management"},
]


def seed() -> None:
    storage.init_db()

    embedder = get_default_embedder()
    print(f"Verwende Embedder: {type(embedder).__name__}")

    for ticket in TICKETS:
        vector = embedder.embed(ticket["text"])
        storage.save_ticket(ticket["id"], ticket["text"], vector, ticket["allowed_roles"])
    print(f"{len(TICKETS)} Tickets gespeichert.")

    for user in DEMO_USERS:
        auth.register_user(user["username"], user["password"], user["role"])
    print(f"{len(DEMO_USERS)} Demo-User angelegt (Passwort für alle: 'demo1234').")


if __name__ == "__main__":
    seed()
