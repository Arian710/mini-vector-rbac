"""
Einfache, assert-basierte Tests. Sie beweisen, dass die Rollen- UND
Tenant-Trennung wirklich greift - insbesondere auch dann, wenn ein sensibles
Ticket inhaltlich der beste Treffer waere (test_best_match_hidden_from_unauthorized_role)
oder ein anderer Mandant exakt dieselbe Rolle hat (test_tenant_filter_beats_matching_role).

Kein Testframework noetig: einfach `python test_rbac.py` ausfuehren.

Nutzt bewusst IMMER den HashingEmbedder statt Azure - Tests sollen offline,
kostenlos und deterministisch laufen, egal ob eine .env mit Azure-Zugangsdaten
existiert oder nicht.
"""

from data import TICKETS
from db import MiniVectorDB
from embeddings import HashingEmbedder

TENANT_A = "kanzlei-mueller"
TENANT_B = "steuerberatung-schmidt"

MANAGEMENT_ONLY_IDS_A = {8, 9, 10, 11, 19, 20}
ALL_VISIBLE_IDS_A = {1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 21, 22}


def build_database() -> MiniVectorDB:
    db = MiniVectorDB(embedder=HashingEmbedder())
    for ticket in TICKETS:
        db.add(ticket["id"], ticket["text"], ticket["allowed_roles"], ticket["tenant_id"])
    return db


def test_support_never_sees_management_tickets():
    db = build_database()
    results = db.search("Gehalt Budget Quartal Kuendigung Uebernahme", role="support",
                          tenant_id=TENANT_A, top_k=10)
    for r in results:
        assert r["id"] not in MANAGEMENT_ONLY_IDS_A, (
            f"Rolle 'support' hat sensibles Ticket {r['id']} gesehen!"
        )


def test_management_sees_sensitive_ticket():
    db = build_database()
    results = db.search("Gehaltserhoehung Budget Vertriebsteam", role="management",
                          tenant_id=TENANT_A, top_k=3)
    ids = [r["id"] for r in results]
    assert 8 in ids, "Rolle 'management' sollte das Gehalts-Ticket (8) als Treffer sehen"


def test_best_match_hidden_from_unauthorized_role():
    # Fast identischer Text wie Ticket 10 - das MUSS der Top-Treffer sein, wenn
    # der Rollenfilter nicht greifen wuerde.
    query = "Kuendigung eines Mitarbeiters in der Buchhaltung wird vorbereitet"

    db = build_database()
    unfiltered = db.search(query, role="management", tenant_id=TENANT_A, top_k=1)
    assert unfiltered[0]["id"] == 10, (
        "Testannahme verletzt: Ticket 10 muesste hier der Top-Treffer sein"
    )

    filtered = db.search(query, role="support", tenant_id=TENANT_A, top_k=1)
    assert all(r["id"] != 10 for r in filtered), (
        "Rolle 'support' hat trotz bestem inhaltlichen Match das sensible Ticket 10 gesehen!"
    )


def test_general_ticket_visible_to_all_roles():
    db = build_database()
    for role in ["support", "management"]:
        results = db.search("Drucker druckt keine Dokumente", role=role, tenant_id=TENANT_A, top_k=3)
        ids = [r["id"] for r in results]
        assert 1 in ids, f"Rolle '{role}' sollte das allgemeine Drucker-Ticket (1) sehen"


def test_unknown_role_only_sees_all_tickets():
    db = build_database()
    results = db.search("Gehalt Budget Kuendigung Uebernahme Quartal", role="praktikant",
                          tenant_id=TENANT_A, top_k=10)
    for r in results:
        assert r["id"] in ALL_VISIBLE_IDS_A, (
            f"Unbekannte Rolle 'praktikant' hat sensibles Ticket {r['id']} gesehen!"
        )


def test_tenant_filter_beats_matching_role():
    # Ticket 15 (Tenant B) ist fast wortgleich mit Ticket 8 (Tenant A) formuliert,
    # beide allowed_roles=["management"]. Das MUSS der Top-Treffer fuer Tenant B
    # sein, wenn man den Tenant-Filter ignoriert.
    query = "Gehaltserhoehung fuer das Team, mehr Budget pro Quartal"

    db = build_database()
    unfiltered = db.search(query, role="management", tenant_id=TENANT_B, top_k=1)
    assert unfiltered[0]["id"] == 15, (
        "Testannahme verletzt: Ticket 15 (Tenant B) muesste hier der Top-Treffer sein"
    )

    # Tenant A, exakt dieselbe Rolle "management" - darf Ticket 15 (Tenant B) trotzdem NIE sehen.
    results_a = db.search(query, role="management", tenant_id=TENANT_A, top_k=10)
    assert all(r["id"] != 15 for r in results_a), (
        "Tenant A (management) hat ein Ticket von Tenant B gesehen - Tenant-Filter versagt!"
    )

    # Umgekehrt: Tenant B darf Ticket 8 (Tenant A) nie sehen, obwohl die Rolle passt
    # und der Text sehr aehnlich ist.
    results_b = db.search(query, role="management", tenant_id=TENANT_B, top_k=10)
    assert all(r["id"] != 8 for r in results_b), (
        "Tenant B (management) hat ein Ticket von Tenant A gesehen - Tenant-Filter versagt!"
    )


def test_general_ticket_not_visible_across_tenants():
    # allowed_roles=["all"] bedeutet "alle Rollen DIESES Tenants", nicht "alle Tenants".
    db = build_database()
    results = db.search("Buero WLAN Mandant Frist", role="support", tenant_id=TENANT_A, top_k=10)
    ids = [r["id"] for r in results]
    assert 12 not in ids and 13 not in ids, (
        "Tenant A hat ein allgemeines Ticket (allowed_roles=['all']) von Tenant B gesehen!"
    )


TESTS = [
    test_support_never_sees_management_tickets,
    test_management_sees_sensitive_ticket,
    test_best_match_hidden_from_unauthorized_role,
    test_general_ticket_visible_to_all_roles,
    test_unknown_role_only_sees_all_tickets,
    test_tenant_filter_beats_matching_role,
    test_general_ticket_not_visible_across_tenants,
]


if __name__ == "__main__":
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
