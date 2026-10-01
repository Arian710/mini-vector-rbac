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
                allowed_roles TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                query TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_ticket(ticket_id, text: str, vector: np.ndarray, allowed_roles: list, path: str = None) -> None:
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tickets (id, text, vector, allowed_roles) VALUES (?, ?, ?, ?)",
            (ticket_id, text, json.dumps(vector.tolist()), json.dumps(allowed_roles)),
        )


def load_tickets(path: str = None) -> list:
    with _connect(path) as conn:
        rows = conn.execute("SELECT id, text, vector, allowed_roles FROM tickets").fetchall()
    return [
        {
            "id": row[0],
            "text": row[1],
            "vector": np.array(json.loads(row[2])),
            "allowed_roles": json.loads(row[3]),
        }
        for row in rows
    ]


def save_user(username: str, password_hash: str, role: str, path: str = None) -> None:
    with _connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )


def get_user(username: str, path: str = None):
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return None
    return {"username": row[0], "password_hash": row[1], "role": row[2]}


def log_search(username: str, query: str, result_count: int, path: str = None) -> None:
    """Protokolliert eine Suche. Wird von api.py aufgerufen, NICHT von db.py -
    die Suchmaschine selbst kennt gar keinen Username, nur eine Rolle."""
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO search_log (username, query, result_count, created_at) VALUES (?, ?, ?, ?)",
            (username, query, result_count, datetime.now(timezone.utc).isoformat()),
        )


def load_search_log(limit: int = 100, path: str = None) -> list:
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT username, query, result_count, created_at FROM search_log "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"username": r[0], "query": r[1], "result_count": r[2], "created_at": r[3]}
        for r in rows
    ]
