"""
Einfache, assert-basierte Tests für auth.py: Passwort-Hashing und JWT.

Nutzt ein eigenes Postgres-Schema statt der echten vector_rbac-Daten,
damit Testläufe die echten Demo-Daten nicht überschreiben.

Kein Testframework nötig: einfach `python test_auth.py` ausführen.
"""

import os

from dotenv import load_dotenv
load_dotenv()  # Postgres-Zugangsdaten (AZURE_POSTGRES_*) kommen aus .env

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")

import storage

storage.PG_SCHEMA = "test_auth"

import auth


def setup_module():
    storage.drop_schema(storage.PG_SCHEMA)
    storage.init_db()


def test_password_hash_is_not_plaintext():
    hashed = auth.hash_password("geheim123")
    assert hashed != "geheim123", "Passwort wurde nicht gehasht, sondern im Klartext gespeichert!"


def test_authenticate_accepts_correct_password():
    auth.register_user("testuser", "richtig123", "support", "kanzlei-mueller")
    identity = auth.authenticate("testuser", "richtig123")
    assert identity["role"] == "support"
    assert identity["tenant_id"] == "kanzlei-mueller"


def test_authenticate_rejects_wrong_password():
    auth.register_user("testuser2", "richtig123", "support", "kanzlei-mueller")
    try:
        auth.authenticate("testuser2", "falsches_passwort")
        assert False, "Falsches Passwort hätte abgelehnt werden müssen"
    except ValueError:
        pass


def test_token_roundtrip_contains_correct_role_and_tenant():
    token = auth.create_access_token("anna", "support", "kanzlei-mueller")
    payload = auth.decode_access_token(token)
    assert payload["username"] == "anna"
    assert payload["role"] == "support"
    assert payload["tenant_id"] == "kanzlei-mueller"


def test_tampered_token_is_rejected():
    import jwt as pyjwt

    token = auth.create_access_token("anna", "support", "kanzlei-mueller")
    try:
        pyjwt.decode(token + "tampered", auth._secret_key(), algorithms=["HS256"])
        assert False, "Manipuliertes Token hätte abgelehnt werden müssen"
    except pyjwt.PyJWTError:
        pass


TESTS = [
    test_password_hash_is_not_plaintext,
    test_authenticate_accepts_correct_password,
    test_authenticate_rejects_wrong_password,
    test_token_roundtrip_contains_correct_role_and_tenant,
    test_tampered_token_is_rejected,
]


if __name__ == "__main__":
    setup_module()
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
    storage.drop_schema(storage.PG_SCHEMA)
