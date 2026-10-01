# Mini-Vektordatenbank mit RBAC

Eine minimale Vektordatenbank für KMU-Support-Tickets, bei der die Rollenprüfung
(RBAC) fest in die Such-Engine eingebaut ist statt nachträglich in der
Oberfläche oder im API-Aufrufer. Entstanden als Lernprojekt, um Vektoren,
Embeddings, Cosine Similarity und serverseitiges RBAC von Grund auf sauber zu
verstehen und sichtbar zu machen.

## Setup & Ausführen

```bash
pip install -r requirements.txt

python seed_data.py     # einmalig: Datenbank mit Beispieldaten + Demo-Usern befüllen

python main.py          # Demo: gleiche Suche, zwei Rollen, zwei Mandanten
python test_rbac.py     # Tests: Rollen- UND Tenant-Trennung auf Engine-Ebene (db.py)
python test_auth.py     # Tests: Passwort-Hashing, JWT-Erzeugung/-Prüfung
python test_audit.py    # Tests: Audit-Log + Autorisierung auf API-Ebene
python test_tenancy.py  # Tests: Mandantentrennung auf echter API-Ebene

uvicorn api:app --reload   # Web-API starten, Swagger-UI unter /docs
```

Demo-Login (aus `seed_data.py`), zwei Mandanten mit je einem `support`- und
einem `management`-User: `anna`/`bernd` gehören zu `kanzlei-mueller`,
`carla`/`david` zu `steuerberatung-schmidt`. Passwort für alle `demo1234` —
nur fürs lokale Ausprobieren.

**Echte Embeddings statt Platzhalter:** `.env.example` nach `.env` kopieren und
mit einer eigenen Azure-OpenAI-Ressource befüllen (Endpoint, Key,
Deployment-Name eines Embedding-Modells wie `text-embedding-3-small`), plus
einen eigenen `JWT_SECRET_KEY`. Ohne `.env` läuft alles automatisch mit dem
kostenlosen `HashingEmbedder` weiter.

## Projektstruktur

- `data.py` – Beispiel-Tickets für **zwei Mandanten** (`kanzlei-mueller`,
  `steuerberatung-schmidt`), je gemischt aus allgemeinen (`allowed_roles=["all"]`)
  und sensiblen Finanz-/HR-Tickets (`allowed_roles=["management"]`)
- `auth.py` – echtes Login: bcrypt-Passwort-Hashing, JWT-Erzeugung und -Prüfung
  (Token enthält Username, Rolle UND `tenant_id`)
- `storage.py` – SQLite-Persistenz (Tickets inkl. Vektor und Tenant, User inkl.
  Tenant, Such-Protokoll inkl. Tenant); komplett getrennt von der Suchlogik in `db.py`
- `embeddings.py` – Embedder-Abstraktion: `HashingEmbedder` (kostenloser,
  deterministischer Platzhalter) und `AzureOpenAIEmbedder` (echtes, trainiertes
  Modell über die Azure-OpenAI-API); `get_default_embedder()` wählt automatisch
- `db.py` – `MiniVectorDB` mit `add()`/`load_entry()` und `search()`, inkl.
  Cosine Similarity, Brute-Force-Suche, Tenant-Filter und Rollenfilter (in
  dieser Reihenfolge); bekommt den Embedder als Abhängigkeit injiziert statt
  ihn selbst festzulegen
- `main.py` – CLI-Demo: gleiche Anfrage über zwei Rollen UND zwei Mandanten
- `api.py` – FastAPI-Web-API: `/login` gibt ein JWT aus, `/search` verlangt es
  im `Authorization`-Header, `/audit-log` zusätzlich nur für Rolle `management`
  (und nur das Protokoll des eigenen Mandanten). Username, Rolle und Tenant
  kommen ausschließlich aus dem geprüften Token, nie aus dem Request-Body
- `seed_data.py` – befüllt die SQLite-Datenbank einmalig mit Beispiel-Tickets
  und Demo-Usern für beide Mandanten
- `test_rbac.py` – beweist Rollen- und Tenant-Trennung auf Engine-Ebene, auch
  wenn ein sensibles Ticket inhaltlich der beste Treffer wäre oder ein anderer
  Mandant exakt dieselbe Rolle hat
- `test_auth.py` – Passwort-Hashing, Token-Erzeugung/-Prüfung, manipulierte Tokens
- `test_audit.py` – Such-Protokollierung plus Autorisierung (`support` bekommt
  403 auf `/audit-log`, `management` sieht den Log-Eintrag)
- `test_tenancy.py` – beweist auf echter API-Ebene, dass zwei Mandanten mit
  identischer Rolle und fast identischem Ticket-Text sich nie gegenseitig sehen,
  auch nicht im Audit-Log

Alle Tests nutzen bewusst immer den `HashingEmbedder` und eine eigene
Test-Datenbankdatei, damit sie offline, kostenlos und ohne Seiteneffekte auf
die echten Daten laufen.

**Nicht Teil dieses Projekts:** HTTPS/Deployment (Reverse-Proxy, TLS-Zertifikat).

## Die 5 Konzepte dahinter

### 1. Vektor

Ein Vektor ist einfach eine Liste von Zahlen, die einen Punkt im Raum
beschreibt. Zwei Zahlen `[80, 3]` beschreiben einen Punkt in 2D, drei Zahlen
einen Punkt in 3D. Jede zusätzliche Zahl ist eine weitere Achse, die den
Punkt genauer beschreibt — ob 2, 3 oder 1000 Zahlen, das Prinzip bleibt
gleich, auch wenn wir uns Räume ab 4 Dimensionen nicht mehr vorstellen
können.

### 2. Embedding

Ein Embedding ist ein Vektor, der die *Bedeutung* von Text beschreibt. Ein
trainiertes Modell übersetzt einen Satz in eine Zahlenliste — niemand legt
diese Zahlen von Hand fest. Weil das Modell darauf trainiert wurde, ähnlichen
Bedeutungen ähnliche Vektoren zuzuweisen, zeigen zwei Sätze mit ähnlichem Sinn
in eine ähnliche *Richtung* im Vektorraum, selbst wenn sie kein einziges
gemeinsames Wort benutzen. Das Modell übersetzt also die Gesamtbedeutung
eines Satzes, nicht einzelne Wörter.

### 3. Cosine Similarity

Cosine Similarity misst, wie ähnlich zwei Vektoren sind — und zwar über den
**Winkel** zwischen ihnen, nicht über den reinen Abstand. Formel:

```
cos(A, B) = (A · B) / (|A| × |B|)
```

Zwei Vektoren, die exakte Vielfache voneinander sind (z.B. `[2,1]` und
`[4,2]`), zeigen in dieselbe Richtung und bekommen Cosine Similarity `1.0` —
obwohl ihre reinen Zahlenwerte und ihr Euklidischer Abstand komplett
unterschiedlich sind. Genau deshalb ist der Winkel das richtige Maß für
Embeddings: die "Länge" eines Vektors kann technisch bedingt schwanken, ohne
dass sich die Bedeutung ändert — Cosine Similarity ignoriert diese Länge
bewusst.

### 4. Brute-Force-Suche

Bei der Brute-Force-Suche wird die Anfrage in einen Vektor umgewandelt und
dann mit **jedem einzelnen** gespeicherten Vektor per Cosine Similarity
verglichen — kein Index, keine Abkürzung. Bei 10.000 gespeicherten
Dokumenten bedeutet eine einzige Anfrage 10.000 Cosine-Similarity-Berechnungen.
Der Name kommt genau daher: es wird stur jeder Vektor durchgerechnet, statt
sich smarter Abkürzungen zu bedienen. Für große Datenmengen wird das
irgendwann zu langsam — dafür gibt es Verfahren wie HNSW, die hier bewusst
nicht gebaut wurden, weil sie für dieses Fundament nicht nötig sind.

### 5. RBAC muss serverseitig passieren

Der Rollenfilter darf niemals im Client (Browser/App) entschieden werden,
sondern nur im Server-Code, den der Nutzer nicht einsehen oder verändern
kann. Sobald Daten über das Netzwerk beim Client ankommen, sind sie
faktisch schon "geleakt" — egal ob die Oberfläche sie anschließend anzeigt
oder nicht. Ein Nutzer kann mit den Browser-Entwicklertools die rohe
Server-Antwort im Netzwerk-Tab einsehen oder die API direkt aufrufen und so
jeden Client-seitigen Filter umgehen. Deshalb muss jede Suche zwingend mit
einer Rolle versehen sein, und der Filter muss dafür sorgen, dass unerlaubte
Daten den Server erst gar nicht verlassen — nicht erst nachträglich
ausgeblendet werden. In `db.py` sitzt der Filter deshalb direkt in
`search()`, bevor überhaupt eine Ähnlichkeit berechnet wird.

### 6. Authentication vs. Authorization

Zwei unterschiedliche Fragen, die leicht verwechselt werden: **Authentication**
("Wer bist du?") prüft ein gültiges JWT bei jeder Anfrage. **Authorization**
("Darfst du *das hier*?") ist eine zusätzliche, endpunkt-spezifische Prüfung
obendrauf — ein gültig eingeloggter `support`-User ist authentifiziert, aber
für `/audit-log` nicht autorisiert und bekommt `403`. In `api.py` baut
`require_management()` deshalb bewusst auf `get_current_user()` auf, statt die
Rollenprüfung zu duplizieren.

### 7. Multi-Tenancy

Teilen sich mehrere Kunden (Mandanten) dieselbe Infrastruktur, reicht die
Rolle allein nicht mehr aus: zwei Mandanten können beide eine Rolle
`management` haben, dürfen sich aber niemals gegenseitig sehen. Der
Tenant-Filter ist deshalb eine zweite, **härtere und vorgelagerte** Schranke
in `search()` — er wird zuerst angewendet, noch vor dem Rollenfilter.
`allowed_roles=["all"]` bedeutet dadurch "alle Rollen *dieses Mandanten*",
nicht "alle Rollen weltweit". Derselbe Grundsatz wie bei RBAC gilt auch hier:
`tenant_id` kommt ausschließlich aus dem geprüften JWT, nie aus einem
Client-Feld — sonst könnte sich ein Nutzer einfach als anderer Mandant
ausgeben.
