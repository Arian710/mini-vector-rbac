"""
Beispiel-Datensatz: KMU-Support-Tickets fuer ZWEI Mandanten (Tenants), die
sich dieselbe Infrastruktur teilen - genau das Szenario aus Konzept 6
(Multi-Tenancy).

Allgemeine Tickets sind fuer alle Rollen SICHTBAR, aber nur innerhalb
desselben Tenants (allowed_roles=["all"] bedeutet NICHT "alle Tenants").
Sensible Finanz-/HR-Tickets sind zusaetzlich auf die Rolle "management"
beschraenkt (allowed_roles=["management"]).

Die Vektoren werden hier bewusst NICHT gespeichert - das Embedding passiert
erst in db.py, wenn ein Ticket per add() in die Datenbank aufgenommen wird.
"""

TICKETS = [
    # --- Tenant: kanzlei-mueller --------------------------------------
    {
        "id": 1,
        "tenant_id": "kanzlei-mueller",
        "text": "Der Drucker im 2. Stock druckt keine Dokumente mehr aus.",
        "allowed_roles": ["all"],
    },
    {
        "id": 2,
        "tenant_id": "kanzlei-mueller",
        "text": "Login ins Kundenportal funktioniert seit heute Morgen nicht mehr.",
        "allowed_roles": ["all"],
    },
    {
        "id": 3,
        "tenant_id": "kanzlei-mueller",
        "text": "Kunde bittet um Rueckerstattung fuer eine fehlerhafte Lieferung.",
        "allowed_roles": ["all"],
    },
    {
        "id": 4,
        "tenant_id": "kanzlei-mueller",
        "text": "WLAN im Konferenzraum bricht waehrend Meetings staendig ab.",
        "allowed_roles": ["all"],
    },
    {
        "id": 5,
        "tenant_id": "kanzlei-mueller",
        "text": "Neue Mitarbeiterin benoetigt Zugang zum internen Wiki.",
        "allowed_roles": ["all"],
    },
    {
        "id": 6,
        "tenant_id": "kanzlei-mueller",
        "text": "E-Mail-Anhaenge ueber 10 Megabyte werden nicht zugestellt.",
        "allowed_roles": ["all"],
    },
    {
        "id": 7,
        "tenant_id": "kanzlei-mueller",
        "text": "Kunde meldet einen Fehler in der mobilen App beim Checkout.",
        "allowed_roles": ["all"],
    },
    {
        "id": 8,
        "tenant_id": "kanzlei-mueller",
        "text": "Gehaltserhoehung fuer das Vertriebsteam genehmigt, neues Budget 42000 Euro pro Quartal.",
        "allowed_roles": ["management"],
    },
    {
        "id": 9,
        "tenant_id": "kanzlei-mueller",
        "text": "Quartalsergebnisse zeigen einen Umsatzrueckgang von acht Prozent gegenueber Vorjahr.",
        "allowed_roles": ["management"],
    },
    {
        "id": 10,
        "tenant_id": "kanzlei-mueller",
        "text": "Kuendigung eines Mitarbeiters in der Buchhaltung wird vorbereitet, streng vertraulich behandeln.",
        "allowed_roles": ["management"],
    },
    {
        "id": 11,
        "tenant_id": "kanzlei-mueller",
        "text": "Verhandlung ueber Uebernahmeangebot eines Wettbewerbers laeuft, hoechste Vertraulichkeit erforderlich.",
        "allowed_roles": ["management"],
    },

    # --- Tenant: steuerberatung-schmidt --------------------------------
    {
        "id": 12,
        "tenant_id": "steuerberatung-schmidt",
        "text": "Mandant fragt nach Fristverlaengerung fuer die Steuererklaerung.",
        "allowed_roles": ["all"],
    },
    {
        "id": 13,
        "tenant_id": "steuerberatung-schmidt",
        "text": "WLAN im Buero funktioniert seit heute Morgen nicht mehr.",
        "allowed_roles": ["all"],
    },
    {
        "id": 14,
        "tenant_id": "steuerberatung-schmidt",
        "text": "Jahresabschluss fuer Mandant X zeigt Unstimmigkeiten, streng vertraulich klaeren.",
        "allowed_roles": ["management"],
    },
    {
        "id": 15,
        "tenant_id": "steuerberatung-schmidt",
        "text": "Gehaltserhoehung fuer das Team ab naechstem Quartal beschlossen, 15 Prozent mehr Budget.",
        "allowed_roles": ["management"],
    },
]
