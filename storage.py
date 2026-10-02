"""
Persistenz-Schicht (Azure Database for PostgreSQL).

Trennt "wie Daten dauerhaft gespeichert werden" von "wie gesucht wird" (db.py).
MiniVectorDB bleibt eine reine In-Memory-Suchmaschine - storage.py laedt beim
Start die zuvor gespeicherten Tickets samt bereits berechnetem Vektor (damit
beim Neustart nicht erneut - und bei Azure: erneut kostenpflichtig - embedded
werden muss) und speichert User samt Passwort-Hash.

War urspruenglich SQLite (eine lokale Datei) - umgestellt auf Azure Postgres,
weil Azure App Service (geplanter Hosting-Ort) keinen garantiert persistenten
lokalen Dateispeicher ueber Neustarts/Skalierung hinweg bietet. Tests nutzen
statt eigener SQLite-Dateien jetzt eigene Postgres-SCHEMAS auf demselben
Server (siehe PG_SCHEMA) - selbe Datenbank-Engine wie in Produktion, kein
Abweichen zwischen Test- und Echt-Umgebung.
"""

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np
import psycopg2
import psycopg2.errors
import psycopg2.pool

PG_SCHEMA = "public"  # Tests ueberschreiben das auf ein eigenes Schema zur Isolation

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10,
            host=os.environ["AZURE_POSTGRES_HOST"],
            dbname=os.environ["AZURE_POSTGRES_DB"],
            user=os.environ["AZURE_POSTGRES_USER"],
            password=os.environ["AZURE_POSTGRES_PASSWORD"],
            sslmode="require",
        )
    return _pool


def _safe_schema(schema: str) -> str:
    schema = schema or PG_SCHEMA
    if not schema.replace("_", "").isalnum():
        raise ValueError(f"Ungueltiger Schema-Name: {schema!r}")
    return schema


@contextmanager
def _connect(schema: str = None):
    schema = _safe_schema(schema)
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}"')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def drop_schema(schema: str) -> None:
    """Nur fuer Tests: raeumt ein komplettes Test-Schema samt aller Tabellen
    weg - das Postgres-Aequivalent zu 'os.remove(test_x.db)' von frueher."""
    schema = _safe_schema(schema)
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        conn.commit()
    finally:
        pool.putconn(conn)


def init_db(schema: str = None) -> None:
    schema = _safe_schema(schema)
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            cur.execute(f'SET search_path TO "{schema}"')
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY,
                    text TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    allowed_roles TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    customer_label TEXT,
                    source_document TEXT,
                    chunk_index INTEGER,
                    chunk_total INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    tenant_id TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS search_log (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    result_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    vector TEXT,
                    is_system BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    UNIQUE(tenant_id, name)
                )
            """)
        conn.commit()
    finally:
        pool.putconn(conn)
    _backfill_default_roles(schema)


# "all" und "management" sind strukturell verankert (db.py prueft "all" als
# Sonderfall, api.py require_management() prueft "management" als Rollenname)
# und duerfen deshalb nie umbenannt/geloescht werden - "support" ist dagegen
# nur ein normaler, voll editierbarer Vorschlagswert.
SYSTEM_ROLE_NAMES = {"all", "management"}
DEFAULT_ROLE_NAMES = {"all", "support", "management"}


def _backfill_default_roles(schema: str = None) -> None:
    """
    Expand->Backfill->Contract-Migration: traegt fuer jeden bereits bekannten
    Tenant (aus users/tickets ermittelt) die Standard-Rollen nach, falls er
    noch keine eigenen Rollen hat. Macht bestehende Installationen nach diesem
    Feature nicht "kaputt" (siehe WorkOS-Empfehlung zu Multi-Tenant-Migrationen).
    """
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            tenant_ids = set()
            cur.execute("SELECT DISTINCT tenant_id FROM users")
            for row in cur.fetchall():
                tenant_ids.add(row[0])
            cur.execute("SELECT DISTINCT tenant_id FROM tickets")
            for row in cur.fetchall():
                tenant_ids.add(row[0])

            for tenant_id in tenant_ids:
                cur.execute("SELECT name FROM roles WHERE tenant_id = %s", (tenant_id,))
                existing = {row[0] for row in cur.fetchall()}
                for name in DEFAULT_ROLE_NAMES - existing:
                    cur.execute(
                        "INSERT INTO roles (tenant_id, name, description, vector, is_system, created_at) "
                        "VALUES (%s, %s, NULL, NULL, %s, %s)",
                        (tenant_id, name, name in SYSTEM_ROLE_NAMES,
                         datetime.now(timezone.utc).isoformat()),
                    )


def save_ticket(ticket_id, text: str, vector: np.ndarray, allowed_roles: list,
                 tenant_id: str, customer_label: str = None, source_document: str = None,
                 chunk_index: int = None, chunk_total: int = None, schema: str = None) -> None:
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets
                    (id, text, vector, allowed_roles, tenant_id, customer_label, source_document, chunk_index, chunk_total)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text, vector = EXCLUDED.vector, allowed_roles = EXCLUDED.allowed_roles,
                    tenant_id = EXCLUDED.tenant_id, customer_label = EXCLUDED.customer_label,
                    source_document = EXCLUDED.source_document, chunk_index = EXCLUDED.chunk_index,
                    chunk_total = EXCLUDED.chunk_total
                """,
                (ticket_id, text, json.dumps(vector.tolist()), json.dumps(allowed_roles), tenant_id,
                 customer_label, source_document, chunk_index, chunk_total),
            )


def next_ticket_id(schema: str = None) -> int:
    """Naechste freie ID - Tickets/Dokumente teilen sich einen globalen ID-Raum,
    tenant-uebergreifend (siehe data.py: IDs 1-22 sind bereits vergeben)."""
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(id) FROM tickets")
            row = cur.fetchone()
    return (row[0] or 0) + 1


def load_tickets(schema: str = None) -> list:
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, text, vector, allowed_roles, tenant_id, customer_label, "
                "source_document, chunk_index, chunk_total FROM tickets"
            )
            rows = cur.fetchall()
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


def save_user(username: str, password_hash: str, role: str, tenant_id: str, schema: str = None) -> None:
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role, tenant_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash, role = EXCLUDED.role, tenant_id = EXCLUDED.tenant_id
                """,
                (username, password_hash, role, tenant_id),
            )


def get_user(username: str, schema: str = None):
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, password_hash, role, tenant_id FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return {"username": row[0], "password_hash": row[1], "role": row[2], "tenant_id": row[3]}


class DuplicateRoleName(Exception):
    pass


class RoleInUse(Exception):
    pass


def list_roles(tenant_id: str, schema: str = None) -> list:
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, vector, is_system, created_at FROM roles "
                "WHERE tenant_id = %s ORDER BY is_system DESC, name ASC",
                (tenant_id,),
            )
            rows = cur.fetchall()
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
                 vector: np.ndarray = None, schema: str = None) -> int:
    vector_json = json.dumps(vector.tolist()) if vector is not None else None
    try:
        with _connect(schema) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO roles (tenant_id, name, description, vector, is_system, created_at) "
                    "VALUES (%s, %s, %s, %s, FALSE, %s) RETURNING id",
                    (tenant_id, name, description, vector_json, datetime.now(timezone.utc).isoformat()),
                )
                return cur.fetchone()[0]
    except psycopg2.errors.UniqueViolation:
        raise DuplicateRoleName(f"Rolle '{name}' existiert in diesem Tenant bereits.")


def update_role(role_id: int, tenant_id: str, name: str = None, description: str = None,
                 vector: np.ndarray = None, schema: str = None) -> None:
    """Tenant-scoped: aktualisiert nur, wenn die Rolle WIRKLICH zu tenant_id gehoert -
    verhindert, dass ein management-User versehentlich/absichtlich eine ID aus
    einem anderen Tenant editiert."""
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, description, is_system FROM roles WHERE id = %s AND tenant_id = %s",
                (role_id, tenant_id),
            )
            row = cur.fetchone()
            if row is None:
                raise LookupError("Rolle nicht gefunden.")
            if row[2] and name is not None and name != row[0]:
                raise PermissionError(f"Systemrolle '{row[0]}' kann nicht umbenannt werden.")

            new_name = name if name is not None else row[0]
            new_description = description if description is not None else row[1]
            vector_json = json.dumps(vector.tolist()) if vector is not None else None

            try:
                if vector is not None:
                    cur.execute(
                        "UPDATE roles SET name = %s, description = %s, vector = %s WHERE id = %s AND tenant_id = %s",
                        (new_name, new_description, vector_json, role_id, tenant_id),
                    )
                else:
                    cur.execute(
                        "UPDATE roles SET name = %s, description = %s WHERE id = %s AND tenant_id = %s",
                        (new_name, new_description, role_id, tenant_id),
                    )
            except psycopg2.errors.UniqueViolation:
                raise DuplicateRoleName(f"Rolle '{new_name}' existiert in diesem Tenant bereits.")


def delete_role(role_id: int, tenant_id: str, schema: str = None) -> None:
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, is_system FROM roles WHERE id = %s AND tenant_id = %s",
                (role_id, tenant_id),
            )
            row = cur.fetchone()
            if row is None:
                raise LookupError("Rolle nicht gefunden.")
            name, is_system = row
            if is_system:
                raise PermissionError(f"Systemrolle '{name}' kann nicht geloescht werden.")

            cur.execute("SELECT COUNT(*) FROM users WHERE tenant_id = %s AND role = %s", (tenant_id, name))
            user_count = cur.fetchone()[0]
            cur.execute("SELECT allowed_roles FROM tickets WHERE tenant_id = %s", (tenant_id,))
            ticket_rows = cur.fetchall()
            doc_count = sum(1 for (allowed_json,) in ticket_rows if name in json.loads(allowed_json))

            if user_count or doc_count:
                raise RoleInUse(
                    f"Rolle '{name}' wird noch von {user_count} User(n) und {doc_count} Dokument(en) "
                    "verwendet - erst umbenennen oder neu zuweisen, bevor sie geloescht werden kann."
                )
            cur.execute("DELETE FROM roles WHERE id = %s AND tenant_id = %s", (role_id, tenant_id))


def log_search(username: str, tenant_id: str, query: str, result_count: int, schema: str = None) -> None:
    """Protokolliert eine Suche. Wird von api.py aufgerufen, NICHT von db.py -
    die Suchmaschine selbst kennt gar keinen Username, nur Rolle und Tenant."""
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO search_log (username, tenant_id, query, result_count, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (username, tenant_id, query, result_count, datetime.now(timezone.utc).isoformat()),
            )


def load_search_log(tenant_id: str, limit: int = 100, schema: str = None) -> list:
    """Gibt NUR das Protokoll des eigenen Tenants zurueck - ein management-User
    sieht sonst auch, wonach ein anderer Mandant gesucht hat."""
    with _connect(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, query, result_count, created_at FROM search_log "
                "WHERE tenant_id = %s ORDER BY id DESC LIMIT %s",
                (tenant_id, limit),
            )
            rows = cur.fetchall()
    return [
        {"username": r[0], "query": r[1], "result_count": r[2], "created_at": r[3]}
        for r in rows
    ]
