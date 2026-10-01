"""
Tests fuer Multi-Tenancy (Issue #4) auf echter API-Ebene.

Beweist das Kernszenario: zwei Mandanten, in jedem ein User mit der Rolle
'management', beide suchen nach fast demselben Gehalts-Thema - jeder sieht
NUR sein eigenes Ticket, nie das des anderen Mandanten, obwohl Rolle und
Textaehnlichkeit identisch waeren.

Nutzt eine eigene, temporaere SQLite-Datei statt der echten vector_rbac.db.

Kein Testframework noetig: einfach `python test_tenancy.py` ausfuehren.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")

import storage

storage.DB_PATH = "test_tenancy.db"

import auth
from data import TICKETS
from embeddings import HashingEmbedder

TENANT_A = "kanzlei-mueller"
TENANT_B = "steuerberatung-schmidt"


def setup_module():
    if os.path.exists(storage.DB_PATH):
        os.remove(storage.DB_PATH)
    storage.init_db()
    auth.register_user("anna", "demo1234", "support", TENANT_A)
    auth.register_user("bernd", "demo1234", "management", TENANT_A)
    auth.register_user("carla", "demo1234", "support", TENANT_B)
    auth.register_user("david", "demo1234", "management", TENANT_B)

    embedder = HashingEmbedder()
    for ticket in TICKETS:
        vector = embedder.embed(ticket["text"])
        storage.save_ticket(ticket["id"], ticket["text"], vector, ticket["allowed_roles"], ticket["tenant_id"])


def _login(client, username, password="demo1234"):
    resp = client.post("/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login fuer {username} fehlgeschlagen: {resp.text}"
    return resp.json()["access_token"]


def test_same_role_different_tenant_never_sees_each_others_ticket():
    from fastapi.testclient import TestClient
    import api as api_module

    client = TestClient(api_module.app)
    token_bernd = _login(client, "bernd")  # management, Tenant A
    token_david = _login(client, "david")  # management, Tenant B

    query = "Gehaltserhoehung fuer das Team, mehr Budget pro Quartal"

    results_bernd = client.post(
        "/search", json={"query": query, "top_k": 10},
        headers={"Authorization": f"Bearer {token_bernd}"},
    ).json()
    results_david = client.post(
        "/search", json={"query": query, "top_k": 10},
        headers={"Authorization": f"Bearer {token_david}"},
    ).json()

    ids_bernd = {r["id"] for r in results_bernd}
    ids_david = {r["id"] for r in results_david}

    assert 8 in ids_bernd, "bernd (Tenant A, management) sollte sein eigenes Gehalts-Ticket (8) sehen"
    assert 15 in ids_david, "david (Tenant B, management) sollte sein eigenes Gehalts-Ticket (15) sehen"

    assert 15 not in ids_bernd, "bernd hat ein Ticket von Tenant B gesehen - Mandantentrennung verletzt!"
    assert 8 not in ids_david, "david hat ein Ticket von Tenant A gesehen - Mandantentrennung verletzt!"


def test_general_ticket_not_visible_across_tenants_via_api():
    from fastapi.testclient import TestClient
    import api as api_module

    client = TestClient(api_module.app)
    token_anna = _login(client, "anna")  # support, Tenant A

    results = client.post(
        "/search", json={"query": "Buero WLAN Mandant Frist Steuererklaerung", "top_k": 10},
        headers={"Authorization": f"Bearer {token_anna}"},
    ).json()
    ids = {r["id"] for r in results}
    assert 12 not in ids and 13 not in ids, (
        "Tenant A hat ein allgemeines Ticket (allowed_roles=['all']) von Tenant B gesehen!"
    )


def test_audit_log_isolated_per_tenant():
    from fastapi.testclient import TestClient
    import api as api_module

    client = TestClient(api_module.app)
    token_carla = _login(client, "carla")   # support, Tenant B
    token_bernd = _login(client, "bernd")   # management, Tenant A
    token_david = _login(client, "david")   # management, Tenant B

    client.post("/search", json={"query": "Fristverlaengerung Steuererklaerung", "top_k": 3},
                headers={"Authorization": f"Bearer {token_carla}"})

    # bernd (Tenant A, management) darf NICHT sehen, dass carla (Tenant B) gesucht hat.
    log_a = client.get("/audit-log", headers={"Authorization": f"Bearer {token_bernd}"}).json()
    assert all(entry["username"] != "carla" for entry in log_a), (
        "Tenant A sieht einen Log-Eintrag von Tenant B - Audit-Log nicht mandantengetrennt!"
    )

    # david (Tenant B, management) sieht carlas Suche dagegen sehr wohl.
    log_b = client.get("/audit-log", headers={"Authorization": f"Bearer {token_david}"}).json()
    assert any(entry["username"] == "carla" for entry in log_b), (
        "Tenant B haette carlas Suche im eigenen Audit-Log sehen sollen"
    )


TESTS = [
    test_same_role_different_tenant_never_sees_each_others_ticket,
    test_general_ticket_not_visible_across_tenants_via_api,
    test_audit_log_isolated_per_tenant,
]


if __name__ == "__main__":
    setup_module()
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
    os.remove(storage.DB_PATH)
