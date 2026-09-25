"""
Simulierte User-Rollen-Zuordnung.

In einem echten System wuerde diese Zuordnung aus einem Login/JWT/einer
Nutzerdatenbank kommen. Echtes Login/Auth ist in diesem Schritt bewusst
ausgeklammert - hier reicht ein einfaches Dictionary, um zu zeigen, dass
jede Suche IRGENDEINE Rolle mitbekommen muss.
"""

USERS = {
    "anna": "support",
    "bernd": "management",
    "carla": "support",
    "david": "management",
}


def get_role(username: str) -> str:
    """Gibt die Rolle eines Users zurueck. Wirft einen Fehler bei unbekanntem User."""
    if username not in USERS:
        raise ValueError(f"Unbekannter User: {username}")
    return USERS[username]
