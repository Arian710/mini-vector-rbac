"""
Einfache, assert-basierte Tests. Sie beweisen, dass die Rollentrennung wirklich
greift - insbesondere auch dann, wenn ein sensibles Ticket inhaltlich der beste
Treffer waere (test_best_match_hidden_from_unauthorized_role).

Kein Testframework noetig: einfach `python test_rbac.py` ausfuehren.
"""

from data import TICKETS
from db import MiniVectorDB

MANAGEMENT_ONLY_IDS = {8, 9, 10, 11}
ALL_VISIBLE_IDS = {1, 2, 3, 4, 5, 6, 7}


def build_database() -> MiniVectorDB:
    db = MiniVectorDB()
    for ticket in TICKETS:
        db.add(ticket["id"], ticket["text"], ticket["allowed_roles"])
    return db


def test_support_never_sees_management_tickets():
    db = build_database()
    results = db.search("Gehalt Budget Quartal Kuendigung Uebernahme", role="support", top_k=10)
    for r in results:
        assert r["id"] not in MANAGEMENT_ONLY_IDS, (
            f"Rolle 'support' hat sensibles Ticket {r['id']} gesehen!"
        )


def test_management_sees_sensitive_ticket():
    db = build_database()
    results = db.search("Gehaltserhoehung Budget Vertriebsteam", role="management", top_k=3)
    ids = [r["id"] for r in results]
    assert 8 in ids, "Rolle 'management' sollte das Gehalts-Ticket (8) als Treffer sehen"


def test_best_match_hidden_from_unauthorized_role():
    # Fast identischer Text wie Ticket 10 - das MUSS der Top-Treffer sein, wenn
    # der Rollenfilter nicht greifen wuerde.
    query = "Kuendigung eines Mitarbeiters in der Buchhaltung wird vorbereitet"

    db = build_database()
    unfiltered = db.search(query, role="management", top_k=1)
    assert unfiltered[0]["id"] == 10, (
        "Testannahme verletzt: Ticket 10 muesste hier der Top-Treffer sein"
    )

    filtered = db.search(query, role="support", top_k=1)
    assert all(r["id"] != 10 for r in filtered), (
        "Rolle 'support' hat trotz bestem inhaltlichen Match das sensible Ticket 10 gesehen!"
    )


def test_general_ticket_visible_to_all_roles():
    db = build_database()
    for role in ["support", "management"]:
        results = db.search("Drucker druckt keine Dokumente", role=role, top_k=3)
        ids = [r["id"] for r in results]
        assert 1 in ids, f"Rolle '{role}' sollte das allgemeine Drucker-Ticket (1) sehen"


def test_unknown_role_only_sees_all_tickets():
    db = build_database()
    results = db.search("Gehalt Budget Kuendigung Uebernahme Quartal", role="praktikant", top_k=10)
    for r in results:
        assert r["id"] in ALL_VISIBLE_IDS, (
            f"Unbekannte Rolle 'praktikant' hat sensibles Ticket {r['id']} gesehen!"
        )


TESTS = [
    test_support_never_sees_management_tickets,
    test_management_sees_sensitive_ticket,
    test_best_match_hidden_from_unauthorized_role,
    test_general_ticket_visible_to_all_roles,
    test_unknown_role_only_sees_all_tickets,
]


if __name__ == "__main__":
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
