"""
Beispiel-Datensatz: KMU-Support-Tickets.

Allgemeine Tickets sind fuer alle Rollen sichtbar (allowed_roles=["all"]).
Sensible Finanz-/HR-Tickets sind nur fuer die Rolle "management" sichtbar
(allowed_roles=["management"]).

Die Vektoren werden hier bewusst NICHT gespeichert - das Embedding passiert
erst in db.py, wenn ein Ticket per add() in die Datenbank aufgenommen wird.
"""

TICKETS = [
    {
        "id": 1,
        "text": "Der Drucker im 2. Stock druckt keine Dokumente mehr aus.",
        "allowed_roles": ["all"],
    },
    {
        "id": 2,
        "text": "Login ins Kundenportal funktioniert seit heute Morgen nicht mehr.",
        "allowed_roles": ["all"],
    },
    {
        "id": 3,
        "text": "Kunde bittet um Rueckerstattung fuer eine fehlerhafte Lieferung.",
        "allowed_roles": ["all"],
    },
    {
        "id": 4,
        "text": "WLAN im Konferenzraum bricht waehrend Meetings staendig ab.",
        "allowed_roles": ["all"],
    },
    {
        "id": 5,
        "text": "Neue Mitarbeiterin benoetigt Zugang zum internen Wiki.",
        "allowed_roles": ["all"],
    },
    {
        "id": 6,
        "text": "E-Mail-Anhaenge ueber 10 Megabyte werden nicht zugestellt.",
        "allowed_roles": ["all"],
    },
    {
        "id": 7,
        "text": "Kunde meldet einen Fehler in der mobilen App beim Checkout.",
        "allowed_roles": ["all"],
    },
    {
        "id": 8,
        "text": "Gehaltserhoehung fuer das Vertriebsteam genehmigt, neues Budget 42000 Euro pro Quartal.",
        "allowed_roles": ["management"],
    },
    {
        "id": 9,
        "text": "Quartalsergebnisse zeigen einen Umsatzrueckgang von acht Prozent gegenueber Vorjahr.",
        "allowed_roles": ["management"],
    },
    {
        "id": 10,
        "text": "Kuendigung eines Mitarbeiters in der Buchhaltung wird vorbereitet, streng vertraulich behandeln.",
        "allowed_roles": ["management"],
    },
    {
        "id": 11,
        "text": "Verhandlung ueber Uebernahmeangebot eines Wettbewerbers laeuft, hoechste Vertraulichkeit erforderlich.",
        "allowed_roles": ["management"],
    },
]
