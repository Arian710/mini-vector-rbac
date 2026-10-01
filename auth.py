"""
Echtes Login statt simuliertem Dictionary.

- Passwoerter werden NIE im Klartext gespeichert, sondern per bcrypt gehasht
  (Einweg-Verfahren: aus dem Hash laesst sich das Passwort nicht zurueckrechnen).
- Nach erfolgreichem Login bekommt der Client ein JWT (JSON Web Token): ein
  signiertes Paket mit Username + Rolle + Tenant. Der Server prueft bei jeder
  Anfrage nur noch die Signatur, statt das Passwort erneut zu brauchen.
  Faelscht jemand den Inhalt (z.B. Rolle oder Tenant), wird die Signatur
  ungueltig und der Server lehnt das Token ab.
- Jeder User gehoert zu genau einem Tenant (Mandant). Das steht ebenfalls im
  Token, damit api.py/db.py dem Client auch hier nicht vertrauen muessen.
"""

import datetime
import os

import bcrypt
import jwt

import storage

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60


def _secret_key() -> str:
    key = os.environ.get("JWT_SECRET_KEY")
    if not key:
        raise RuntimeError(
            "JWT_SECRET_KEY ist nicht gesetzt. Bitte in .env eintragen (siehe .env.example)."
        )
    return key


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def register_user(username: str, password: str, role: str, tenant_id: str) -> None:
    storage.save_user(username, hash_password(password), role, tenant_id)


def authenticate(username: str, password: str) -> dict:
    """Prueft Username+Passwort. Gibt {role, tenant_id} zurueck oder wirft ValueError."""
    user = storage.get_user(username)
    if user is None:
        raise ValueError("Unbekannter User oder falsches Passwort")
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise ValueError("Unbekannter User oder falsches Passwort")
    return {"role": user["role"], "tenant_id": user["tenant_id"]}


def create_access_token(username: str, role: str, tenant_id: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "tenant_id": tenant_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Prueft Signatur + Ablaufzeit. Gibt {username, role, tenant_id} zurueck oder wirft jwt.PyJWTError."""
    payload = jwt.decode(token, _secret_key(), algorithms=[JWT_ALGORITHM])
    return {
        "username": payload["sub"],
        "role": payload["role"],
        "tenant_id": payload["tenant_id"],
    }
