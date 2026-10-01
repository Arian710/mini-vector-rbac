"""
Einfache, assert-basierte Tests für auth.py: Passwort-Hashing und JWT.

Nutzt eine eigene, temporäre SQLite-Datei statt der echten vector_rbac.db,
damit Testläufe die echten Demo-Daten nicht überschreiben.

Kein Testframework nötig: einfach `python test_auth.py` ausführen.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")

import storage

storage.DB_PATH = "test_auth.db"

import auth


def setup_module():
    if os.path.exists(storage.DB_PATH):
        os.remove(storage.DB_PATH)
    storage.init_db()


def test_password_hash_is_not_plaintext():
    hashed = auth.hash_password("geheim123")
    assert hashed != "geheim123", "Passwort wurde nicht gehasht, sondern im Klartext gespeichert!"


def test_authenticate_accepts_correct_password():
    auth.register_user("testuser", "richtig123", "support")
    role = auth.authenticate("testuser", "richtig123")
    assert role == "support"


def test_authenticate_rejects_wrong_password():
    auth.register_user("testuser2", "richtig123", "support")
    try:
        auth.authenticate("testuser2", "falsches_passwort")
        assert False, "Falsches Passwort hätte abgelehnt werden müssen"
    except ValueError:
        pass


def test_token_roundtrip_contains_correct_role():
    token = auth.create_access_token("anna", "support")
    payload = auth.decode_access_token(token)
    assert payload["username"] == "anna"
    assert payload["role"] == "support"


def test_tampered_token_is_rejected():
    import jwt as pyjwt

    token = auth.create_access_token("anna", "support")
    try:
        pyjwt.decode(token + "tampered", auth._secret_key(), algorithms=["HS256"])
        assert False, "Manipuliertes Token hätte abgelehnt werden müssen"
    except pyjwt.PyJWTError:
        pass


TESTS = [
    test_password_hash_is_not_plaintext,
    test_authenticate_accepts_correct_password,
    test_authenticate_rejects_wrong_password,
    test_token_roundtrip_contains_correct_role,
    test_tampered_token_is_rejected,
]


if __name__ == "__main__":
    setup_module()
    for test in TESTS:
        test()
        print(f"OK: {test.__name__}")
    print(f"\nAlle {len(TESTS)} Tests bestanden.")
    os.remove(storage.DB_PATH)
