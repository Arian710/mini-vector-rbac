"""
Tests fuer das Audit-Log (Issue #3).

Teil 1 prueft storage.py direkt (log_search/load_search_log).
Teil 2 prueft die echte API-Autorisierung ueber FastAPI's TestClient:
  - ein eingeloggter 'support'-User (authentifiziert!) bekommt trotzdem 403
    auf /audit-log (nicht autorisiert)
  - 'management' bekommt 200 und sieht den Log-Eintrag der zuvor von
    'support' ausgefuehrten Suche

Nutzt ein eigenes Postgres-Schema statt der echten vector_rbac-Daten.

Kein Testframework noetig: einfach `python test_audit.py` ausfuehren.
"""

import os

from dotenv import load_dotenv
load_dotenv()  # Postgres-Zugangsdaten (AZURE_POSTGRES_*) kommen aus .env

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")
os.environ["DISABLE_RATE_LIMIT"] = "1"  # dieser Test loggt bewusst oft hintereinander ein

# Erzwingt den HashingEmbedder-Fallback in api.py, unabhaengig von einer
# evtl. vorhandenen .env mit echten Azure-Zugangsdaten - siehe test_tenancy.py
# fuer die ausfuehrliche Begruendung (Shape-Mismatch 1536 vs. 64 sonst).
for _azure_var in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"):
    os.environ[_azure_var] = ""

import storage

storage.PG_SCHEMA = "test_audit"

import auth
from data import TICKETS
from embeddings import HashingEmbedder


TENANT = "kanzlei-mueller"


def setup_module():
    storage.drop_schema(storage.PG_SCHEMA)
    storage.init_db()
    auth.register_user("anna", "demo1234", "support", TENANT)
    auth.register_user("bernd", "demo1234", "management", TENANT)
    embedder = HashingEmbedder()
    for ticket in TICKETS:
        vector = embedder.embed(ticket["text"])
        storage.save_ticket(ticket["id"], ticket["text"], vector, ticket["allowed_roles"], ticket["tenant_id"])


# ---------------------------------------------------------- Teil 1: storage.py ---

def test_log_search_roundtrip():
    storage.log_search("anna", TENANT, "Drucker kaputt", 2)
    entries = storage.load_search_log(tenant_id=TENANT)
    assert entries[0]["username"] == "anna"
    assert entries[0]["query"] == "Drucker kaputt"
    assert entries[0]["result_count"] == 2


def test_log_search_newest_first():
    storage.log_search("bernd", TENANT, "erste anfrage", 1)
    storage.log_search("bernd", TENANT, "zweite anfrage", 3)
    entries = storage.load_search_log(tenant_id=TENANT)
    assert entries[0]["query"] == "zweite anfrage", "Neuester Eintrag muss zuerst kommen"


# ---------------------------------------------------------- Teil 2: API-Autorisierung ---

def test_support_cannot_see_audit_log_but_management_can():
    from fastapi.testclient import TestClient
    import api as api_module

    client = TestClient(api_module.app)

    login_support = client.post("/login", json={"username": "anna", "password": "demo1234"})
    token_support = login_support.json()["access_token"]

    login_mgmt = client.post("/login", json={"username": "bernd", "password": "demo1234"})
    token_mgmt = login_mgmt.json()["access_token"]

    # anna (support) fuehrt eine Suche aus - das MUSS protokolliert werden
    search_resp = client.post(
        "/search",
        json={"query": "Gehalt Budget", "top_k": 3},
        headers={"Authorization": f"Bearer {token_support}"},
    )
    assert search_resp.status_code == 200

    # anna (support) ist authentifiziert, aber NICHT autorisiert fuer /audit-log
    denied = client.get("/audit-log", headers={"Authorization": f"Bearer {token_support}"})
    assert denied.status_code == 403, "Rolle 'support' haette 403 bekommen muessen"

    # bernd (management) ist autorisiert und sieht annas protokollierte Suche
    allowed = client.get("/audit-log", headers={"Authorization": f"Bearer {token_mgmt}"})
    assert allowed.status_code == 200
    usernames = [entry["username"] for entry in allowed.json()]
    assert "anna" in usernames, "annas Suche haette im Log auftauchen muessen"


TESTS = [
    test_log_search_roundtrip,
    test_log_search_newest_first,
    test_support_cannot_see_audit_log_but_management_can,
]


if __name__ == "__main__":
    setup_module()
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
    storage.drop_schema(storage.PG_SCHEMA)
