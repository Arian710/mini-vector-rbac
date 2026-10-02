"""
Tests fuer Login-Haertung (Issue: sichere Authentifizierung).

Teil 1: Passwort-Staerke-Regeln (auth.validate_password_strength).
Teil 2: Rate-Limiting auf /login - bewusst NICHT deaktiviert (anders als die
anderen API-Tests), weil genau das hier getestet werden soll.

Nutzt ein eigenes Postgres-Schema statt der echten vector_rbac-Daten.

Kein Testframework noetig: einfach `python test_security.py` ausfuehren.
"""

import os

from dotenv import load_dotenv
load_dotenv()  # Postgres-Zugangsdaten (AZURE_POSTGRES_*) kommen aus .env

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")

for _azure_var in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"):
    os.environ[_azure_var] = ""

import storage

storage.PG_SCHEMA = "test_security"

import auth


def setup_module():
    storage.drop_schema(storage.PG_SCHEMA)
    storage.init_db()
    auth.register_user("secuser", "demo1234", "support", "firma-security-test")


def test_password_too_short_rejected():
    try:
        auth.validate_password_strength("abc123")
        assert False, "zu kurzes Passwort haette abgelehnt werden muessen"
    except ValueError:
        pass


def test_password_without_digit_rejected():
    try:
        auth.validate_password_strength("nurbuchstaben")
        assert False, "Passwort ohne Ziffer haette abgelehnt werden muessen"
    except ValueError:
        pass


def test_password_without_letter_rejected():
    try:
        auth.validate_password_strength("12345678")
        assert False, "Passwort ohne Buchstaben haette abgelehnt werden muessen"
    except ValueError:
        pass


def test_valid_password_accepted():
    auth.validate_password_strength("demo1234")  # wirft nicht


def test_register_user_enforces_password_strength():
    try:
        auth.register_user("schwacher_user", "123", "support", "firma-security-test")
        assert False, "register_user haette das schwache Passwort ablehnen muessen"
    except ValueError:
        pass
    assert storage.get_user("schwacher_user") is None, "User haette trotz Fehler nicht gespeichert werden duerfen"


def test_login_rate_limit_blocks_after_five_attempts():
    from fastapi.testclient import TestClient
    import api as api_module

    client = TestClient(api_module.app)

    statuses = []
    for _ in range(6):
        resp = client.post("/login", json={"username": "secuser", "password": "falsches-passwort"})
        statuses.append(resp.status_code)

    assert statuses[:5] == [401] * 5, f"Erste 5 Versuche sollten 401 sein, waren: {statuses[:5]}"
    assert statuses[5] == 429, f"6. Versuch haette vom Rate-Limit blockiert werden sollen (429), war: {statuses[5]}"


TESTS = [
    test_password_too_short_rejected,
    test_password_without_digit_rejected,
    test_password_without_letter_rejected,
    test_valid_password_accepted,
    test_register_user_enforces_password_strength,
    test_login_rate_limit_blocks_after_five_attempts,
]


if __name__ == "__main__":
    setup_module()
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
    storage.drop_schema(storage.PG_SCHEMA)
