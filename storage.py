"""
Persistenz-Schicht (SQLite).

Trennt "wie Daten dauerhaft gespeichert werden" von "wie gesucht wird" (db.py).
MiniVectorDB bleibt eine reine In-Memory-Suchmaschine - storage.py laedt beim
Start die zuvor gespeicherten Tickets samt bereits berechnetem Vektor (damit
beim Neustart nicht erneut - und bei Azure: erneut kostenpflichtig - embedded
werden muss) und speichert User samt Passwort-Hash.

WICHTIG: Pfad-Parameter duerfen NICHT als `path: str = DB_PATH` definiert
werden - Python wertet einen Default-Wert einmalig beim Laden des Moduls aus,
nicht bei jedem Aufruf. Wuerde jemand spaeter `storage.DB_PATH` umsetzen (z.B.
fuer Tests mit einer eigenen Datenbankdatei), wuerden die Funktionen trotzdem
weiter den alten, eingefrorenen Pfad benutzen. Deshalb hier `path: str = None`
und der echte, aktuelle Wert wird erst INNERHALB der Funktion nachgeschlagen.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np

DB_PATH = "vector_rbac.db"


@contextmanager
def _connect(path: str = None):
    conn = sqlite3.connect(path or DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str = None) -> None:
    with _connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                vector TEXT NOT NULL,
                allowed_roles TEXT NOT NULL,
                tenant_id TEXT NOT NULL
            )
        """)
        # Migrationen fuer Datenbanken, die vor den jeweiligen Features angelegt
        # wurden - ALTER TABLE ADD COLUMN kennt kein "IF NOT EXISTS", daher try/except.
        for migration in (
            "ALTER TABLE tickets ADD COLUMN customer_label TEXT",
            "ALTER TABLE tickets ADD COLUMN source_document TEXT",
            "ALTER TABLE tickets ADD COLUMN chunk_index INTEGER",
            "ALTER TABLE tickets ADD COLUMN chunk_total INTEGER",
        ):
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                tenant_id TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                query TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                vector TEXT,
                is_system INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(tenant_id, name)
            )
        """)
    _backfill_default_roles(path)


# "all" und "management" sind strukturell verankert (db.py prueft "all" als
# Sonderfall, api.py require_management() prueft "management" als Rollenname)
# und duerfen deshalb nie umbenannt/geloescht werden - "support" ist dagegen
# nur ein normaler, voll editierbarer Vorschlagswert.
SYSTEM_ROLE_NAMES = {"all", "management"}
DEFAULT_ROLE_NAMES = {"all", "support", "management"}


def _backfill_default_roles(path: str = None) -> None:
    """
    Expand->Backfill->Contract-Migration: traegt fuer jeden bereits bekannten
    Tenant (aus users/tickets ermittelt) die Standard-Rollen nach, falls er
    noch keine eigenen Rollen hat. Macht bestehende Installationen nach diesem
    Feature nicht "kaputt" (siehe WorkOS-Empfehlung zu Multi-Tenant-Migrationen).
    """
    with _connect(path) as conn:
        tenant_ids = set()
        for row in conn.execute("SELECT DISTINCT tenant_id FROM users"):
            tenant_ids.add(row[0])
        for row in conn.execute("SELECT DISTINCT tenant_id FROM tickets"):
            tenant_ids.add(row[0])

        for tenant_id in tenant_ids:
            existing = {
                row[0] for row in
                conn.execute("SELECT name FROM roles WHERE tenant_id = ?", (tenant_id,))
            }
            for name in DEFAULT_ROLE_NAMES - existing:
                conn.execute(
                    "INSERT INTO roles (tenant_id, name, description, vector, is_system, created_at) "
                    "VALUES (?, ?, NULL, NULL, ?, ?)",
                    (tenant_id, name, 1 if name in SYSTEM_ROLE_NAMES else 0,
                     datetime.now(timezone.utc).isoformat()),
                )


def save_ticket(ticket_id, text: str, vector: np.ndarray, allowed_roles: list,
                 tenant_id: str, customer_label: str = None, source_document: str = None,
                 chunk_index: int = None, chunk_total: int = None, path: str = None) -> None:
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tickets "
            "(id, text, vector, allowed_roles, tenant_id, customer_label, source_document, chunk_index, chunk_total) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, text, json.dumps(vector.tolist()), json.dumps(allowed_roles), tenant_id,
             customer_label, source_document, chunk_index, chunk_total),
        )


def next_ticket_id(path: str = None) -> int:
    """Naechste freie ID - Tickets/Dokumente teilen sich einen globalen ID-Raum,
    tenant-uebergreifend (siehe data.py: IDs 1-22 sind bereits vergeben)."""
    with _connect(path) as conn:
        row = conn.execute("SELECT MAX(id) FROM tickets").fetchone()
    return (row[0] or 0) + 1


def load_tickets(path: str = None) -> list:
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, text, vector, allowed_roles, tenant_id, customer_label, "
            "source_document, chunk_index, chunk_total FROM tickets"
        ).fetchall()
    return [
        {
            "id": row[0],
            "text": row[1],
            "vector": np.array(json.loads(row[2])),
            "allowed_roles": json.loads(row[3]),
            "tenant_id": row[4],
            "customer_label": row[5],
            "source_document": row[6],
            "chunk_index": row[7],
            "chunk_total": row[8],
        }
        for row in rows
    ]


def save_user(username: str, password_hash: str, role: str, tenant_id: str, path: str = None) -> None:
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (username, password_hash, role, tenant_id) "
            "VALUES (?, ?, ?, ?)",
            (username, password_hash, role, tenant_id),
        )


def get_user(username: str, path: str = None):
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT username, password_hash, role, tenant_id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return {"username": row[0], "password_hash": row[1], "role": row[2], "tenant_id": row[3]}


def log_search(username: str, tenant_id: str, query: str, result_count: int, path: str = None) -> None:
    """Protokolliert eine Suche. Wird von api.py aufgerufen, NICHT von db.py -
    die Suchmaschine selbst kennt gar keinen Username, nur Rolle und Tenant."""
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO search_log (username, tenant_id, query, result_count, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, tenant_id, query, result_count, datetime.now(timezone.utc).isoformat()),
        )


class DuplicateRoleName(Exception):
    pass


class RoleInUse(Exception):
    pass


def list_roles(tenant_id: str, path: str = None) -> list:
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT id, name, description, vector, is_system, created_at FROM roles "
            "WHERE tenant_id = ? ORDER BY is_system DESC, name ASC",
            (tenant_id,),
        ).fetchall()
    return [
        {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "vector": np.array(json.loads(row[3])) if row[3] else None,
            "is_system": bool(row[4]),
            "created_at": row[5],
        }
        for row in rows
    ]


def create_role(tenant_id: str, name: str, description: str = None,
                 vector: np.ndarray = None, path: str = None) -> int:
    vector_json = json.dumps(vector.tolist()) if vector is not None else None
    try:
        with _connect(path) as conn:
            cursor = conn.execute(
                "INSERT INTO roles (tenant_id, name, description, vector, is_system, created_at) "
                "VALUES (?, ?, ?, ?, 0, ?)",
                (tenant_id, name, description, vector_json, datetime.now(timezone.utc).isoformat()),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise DuplicateRoleName(f"Rolle '{name}' existiert in diesem Tenant bereits.")


def update_role(role_id: int, tenant_id: str, name: str = None, description: str = None,
                 vector: np.ndarray = None, path: str = None) -> None:
    """Tenant-scoped: aktualisiert nur, wenn die Rolle WIRKLICH zu tenant_id gehoert -
    verhindert, dass ein management-User versehentlich/absichtlich eine ID aus
    einem anderen Tenant editiert."""
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT name, description, is_system FROM roles WHERE id = ? AND tenant_id = ?",
            (role_id, tenant_id),
        ).fetchone()
        if row is None:
            raise LookupError("Rolle nicht gefunden.")
        if row[2] and name is not None and name != row[0]:
            raise PermissionError(f"Systemrolle '{row[0]}' kann nicht umbenannt werden.")

        new_name = name if name is not None else row[0]
        new_description = description if description is not None else row[1]
        vector_json = json.dumps(vector.tolist()) if vector is not None else None

        try:
            if vector is not None:
                conn.execute(
                    "UPDATE roles SET name = ?, description = ?, vector = ? WHERE id = ? AND tenant_id = ?",
                    (new_name, new_description, vector_json, role_id, tenant_id),
                )
            else:
                conn.execute(
                    "UPDATE roles SET name = ?, description = ? WHERE id = ? AND tenant_id = ?",
                    (new_name, new_description, role_id, tenant_id),
                )
        except sqlite3.IntegrityError:
            raise DuplicateRoleName(f"Rolle '{new_name}' existiert in diesem Tenant bereits.")


def delete_role(role_id: int, tenant_id: str, path: str = None) -> None:
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT name, is_system FROM roles WHERE id = ? AND tenant_id = ?",
            (role_id, tenant_id),
        ).fetchone()
        if row is None:
            raise LookupError("Rolle nicht gefunden.")
        name, is_system = row
        if is_system:
            raise PermissionError(f"Systemrolle '{name}' kann nicht geloescht werden.")

        user_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE tenant_id = ? AND role = ?", (tenant_id, name)
        ).fetchone()[0]
        ticket_rows = conn.execute(
            "SELECT allowed_roles FROM tickets WHERE tenant_id = ?", (tenant_id,)
        ).fetchall()
        doc_count = sum(1 for (allowed_json,) in ticket_rows if name in json.loads(allowed_json))

        if user_count or doc_count:
            raise RoleInUse(
                f"Rolle '{name}' wird noch von {user_count} User(n) und {doc_count} Dokument(en) "
                "verwendet - erst umbenennen oder neu zuweisen, bevor sie geloescht werden kann."
            )
        conn.execute("DELETE FROM roles WHERE id = ? AND tenant_id = ?", (role_id, tenant_id))


def load_search_log(tenant_id: str, limit: int = 100, path: str = None) -> list:
    """Gibt NUR das Protokoll des eigenen Tenants zurueck - ein management-User
    sieht sonst auch, wonach ein anderer Mandant gesucht hat."""
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT username, query, result_count, created_at FROM search_log "
            "WHERE tenant_id = ? ORDER BY id DESC LIMIT ?",
            (tenant_id, limit),
        ).fetchall()
    return [
        {"username": r[0], "query": r[1], "result_count": r[2], "created_at": r[3]}
        for r in rows
    ]
