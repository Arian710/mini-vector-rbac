# Testplan — Mini-Vektordatenbank mit RBAC

Sammelstelle für alle Testfälle vor einer Veröffentlichung. Wird laufend ergänzt,
wenn neue Features dazukommen. Durchgeführt wird die komplette Liste gemeinsam,
sobald eine erste Grundversion steht — Zeitpunkt entscheiden wir dann zusammen.

**Legende:**
- 🤖 Automatisiert — existiert bereits als Test-Datei, oder ist als "zu ergänzen" markiert
- 👤 Manuell — durch dich im Browser/Terminal auszuführen, Ergebnis hier abhaken

---

## 1. Authentifizierung (Login/JWT)

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 1.1 | Login mit korrektem Username/Passwort gibt gültiges JWT zurück | 🤖 `test_auth.py` | ✅ vorhanden |
| 1.2 | Login mit falschem Passwort wird abgelehnt | 🤖 `test_auth.py` | ✅ vorhanden |
| 1.3 | Passwort wird nie im Klartext gespeichert (nur Hash) | 🤖 `test_auth.py` | ✅ vorhanden |
| 1.4 | Manipuliertes Token (ein Zeichen geändert) wird abgelehnt | 🤖 `test_auth.py` | ✅ vorhanden |
| 1.5 | Token enthält korrekte Rolle + Tenant nach Roundtrip | 🤖 `test_auth.py` | ✅ vorhanden |
| 1.6 | Abgelaufenes Token (>60 Min) führt im Dashboard automatisch zum Login-Redirect | 👤 Browser | ☐ offen |
| 1.7 | Login mit unbekanntem Username zeigt generische Fehlermeldung (kein Hinweis "User existiert nicht") | 👤 Browser | ☐ offen |
| 1.8 | Leeres Formular absenden (Username/Passwort leer) verhält sich sinnvoll (kein Crash) | 👤 Browser | ☐ offen |

## 2. Rollenbasierte Zugriffskontrolle (RBAC)

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 2.1 | `support` sieht nie management-only-Tickets, auch nicht bei perfektem inhaltlichen Match | 🤖 `test_rbac.py` | ✅ vorhanden |
| 2.2 | `management` sieht sensible Tickets | 🤖 `test_rbac.py` | ✅ vorhanden |
| 2.3 | Allgemeine Tickets (`allowed_roles=["all"]`) sind für alle Rollen sichtbar | 🤖 `test_rbac.py` | ✅ vorhanden |
| 2.4 | Unbekannte Rolle sieht nur allgemeine Tickets | 🤖 `test_rbac.py` | ✅ vorhanden |
| 2.5 | `support`-User bekommt 403 auf `/audit-log` | 🤖 `test_audit.py` | ✅ vorhanden |
| 2.6 | `management`-User bekommt 200 auf `/audit-log` | 🤖 `test_audit.py` | ✅ vorhanden |
| 2.7 | `support`-User kann `/documents/suggest` und `/documents` nicht aufrufen (403) | 🤖 zu ergänzen | ☐ offen |
| 2.8 | Rolle aus Request-Body wird ignoriert — nur die Rolle aus dem JWT zählt | 🤖 zu ergänzen | ☐ offen |

## 3. Multi-Tenancy

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 3.1 | Tenant-Filter schlägt härter als Rollen-Match (identische Rolle, anderer Tenant → kein Zugriff) | 🤖 `test_rbac.py` | ✅ vorhanden |
| 3.2 | Allgemeines Ticket eines Tenants ist für den anderen Tenant unsichtbar | 🤖 `test_rbac.py` | ✅ vorhanden |
| 3.3 | Zwei Tenants mit identischer Rolle sehen nie die Tickets des jeweils anderen (echte API-Ebene) | 🤖 `test_tenancy.py` | ✅ vorhanden |
| 3.4 | Audit-Log ist pro Tenant isoliert | 🤖 `test_tenancy.py` | ✅ vorhanden |
| 3.5 | Hochgeladenes Dokument landet garantiert im Tenant des einloggten Users, nicht im Request-Body wählbar | 🤖 zu ergänzen | ☐ offen |

## 4. Suche (Cosine Similarity / Vektor-Suche)

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 4.1 | Suche mit leerem Query-String verhält sich sinnvoll (kein Crash/500) | 👤 Browser + 🤖 zu ergänzen | ☐ offen |
| 4.2 | Suche mit Sonderzeichen/Emoji im Query crasht nicht | 👤 Browser | ☐ offen |
| 4.3 | Suche mit `top_k=0` und sehr hohem `top_k` (z.B. 10000) verhält sich sinnvoll | 🤖 zu ergänzen | ☐ offen |
| 4.4 | Score-Werte liegen immer zwischen -1 und 1 | 🤖 zu ergänzen | ☐ offen |
| 4.5 | Suche ohne Treffer zeigt "(keine sichtbaren Treffer)" statt leerer Seite | 👤 Browser | ☐ offen |
| 4.6 | Jede Suche wird im Audit-Log protokolliert | 🤖 `test_audit.py` | ✅ vorhanden (Grundfall) |

## 5. Selfservice-Dokumenten-Upload

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 5.1 | PDF mit Text-Ebene wird korrekt extrahiert | 👤 Browser + 🤖 curl verifiziert | ✅ manuell geprüft |
| 5.2 | DOCX wird korrekt extrahiert | 👤 Browser + 🤖 curl verifiziert | ✅ manuell geprüft |
| 5.3 | TXT wird korrekt extrahiert | 👤 Browser | ☐ offen |
| 5.4 | Nicht unterstützter Dateityp (z.B. .xlsx, .jpg) zeigt klare Fehlermeldung | 👤 Browser | ☐ offen |
| 5.5 | Leere/inhaltslose Datei (0 Byte oder nur Whitespace) zeigt klare Fehlermeldung statt Crash | 👤 Browser | ☐ offen |
| 5.6 | Gescanntes/bild-only PDF ohne Text-Ebene → aktuell erwartbarer Fehler ("kein Text extrahiert") bis OCR-Feature kommt | 👤 Browser | ☐ offen |
| 5.7 | Sehr langes Dokument (>8191 Tokens) wird automatisch in mehrere Abschnitte (Chunks) zerlegt statt zu scheitern | 🤖 curl mit echtem eBook verifiziert | ✅ geprüft |
| 5.8 | Jeder Chunk ist einzeln durchsuchbar mit korrekter Quellenangabe (Dateiname + Abschnitt X/Y) | 🤖 curl verifiziert | ✅ geprüft |
| 5.9 | Dokument landet sofort im Suchindex, ohne Server-Neustart | 🤖 curl verifiziert | ✅ geprüft |
| 5.10 | "Kunde/Projekt"-Label wird korrekt gespeichert und bleibt reine Organisations-Metadaten (keine Sicherheitsauswirkung) | 👤 Browser | ☐ offen |
| 5.11 | Azure-Rate-Limit (429) wird automatisch mit Backoff wiederholt statt sofort zu scheitern | 🤖 zu ergänzen (lässt sich schwer isoliert testen ohne echten Azure-Call) | ☐ offen |
| 5.12 | Azure-Ausfall zeigt klare Fehlermeldung im Frontend statt "Failed to fetch" | 👤 Browser (Azure-Key temporär ungültig machen) | ☐ offen |
| 5.13 | Upload-Seite ist für `support`-Rolle in der Sidebar nicht sichtbar | 👤 Browser (als anna einloggen) | ☐ offen |
| 5.14 | Direkter Aufruf von `/upload` als `support`-User (URL manuell eingeben) führt zu sauberem 403, nicht zu kaputter Seite | 👤 Browser | ☐ offen |

## 6. Automatischer Rollenvorschlag

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 6.1 | Dokument mit sensiblen Keywords (z.B. "Gehalt", "vertraulich") → Vorschlag `management` | 🤖 curl verifiziert | ✅ geprüft |
| 6.2 | Neutrales Dokument ohne Keywords/Ähnlichkeit → Vorschlag `all` | 🤖 curl verifiziert | ✅ geprüft |
| 6.3 | Bei <3 Referenzdokumenten pro Kategorie wird NUR die Keyword-Heuristik genutzt (kein Embedding-Vergleich) | 🤖 zu ergänzen | ☐ offen |
| 6.4 | Vorschlag kann vor dem Speichern manuell überschrieben werden | 👤 Browser | ☐ offen |
| 6.5 | Kein Dokument wird je ohne menschliche Bestätigung gespeichert (kein Auto-Save direkt nach Upload) | 👤 Code-Review (Architektur-Check) | ✅ geprüft (zweistufiger Flow) |

## 7. Graph-Visualisierung

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 7.1 | Graph zeigt nur Dokumente, die die Rolle/der Tenant sehen darf | 🤖 zu ergänzen (DB-Ebene testbar) | ☐ offen |
| 7.2 | Knotenfarbe korrekt: teal = alle Rollen, orange = nur management | 👤 Browser | ✅ geprüft |
| 7.3 | Schwache Kanten (< Ähnlichkeitsschwelle) werden nicht angezeigt | 👤 Browser (visuelle Prüfung) | ✅ geprüft |
| 7.4 | Klick auf Knoten hebt verbundene Dokumente hervor | 👤 Browser | ✅ geprüft |
| 7.5 | Scrollen zoomt den Graph | 👤 Browser | ✅ geprüft |
| 7.6 | Graph mit 0 Dokumenten (leerer Tenant) crasht nicht | 👤 Browser / 🤖 zu ergänzen | ☐ offen |
| 7.7 | Graph mit sehr vielen Dokumenten (Performance-Test, z.B. 200+) bleibt bedienbar | 👤 Browser (später, braucht größeren Testdatensatz) | ☐ offen (v2) |

## 8. Fehlerbehandlung & Resilienz

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 8.1 | Backend nicht erreichbar → Frontend zeigt verständliche Meldung, kein kaputter weißer Screen | 👤 Browser (Backend stoppen) | ☐ offen |
| 8.2 | Ungültiges/kaputtes JWT im LocalStorage → sauberer Redirect zu Login statt Endlosschleife | 👤 Browser (Token manuell im DevTools verfälschen) | ☐ offen |
| 8.3 | CORS-Header korrekt gesetzt für den Dev-Server-Origin | 🤖 bereits implizit durch funktionierenden Login geprüft | ✅ geprüft |

## 9. Allgemeine Qualitätssicherung

| # | Testfall | Typ | Status |
|---|----------|-----|--------|
| 9.1 | Komplette Test-Suite (`test_rbac.py`, `test_auth.py`, `test_audit.py`, `test_tenancy.py`) läuft grün | 🤖 | ✅ laufend geprüft |
| 9.2 | `python seed_data.py` läuft fehlerfrei auf frischer Datenbank | 🤖 | ✅ geprüft |
| 9.3 | App funktioniert nach frischem `git clone` + `pip install -r requirements.txt` + `npm install` ohne manuelle Zusatzschritte außer `.env` befüllen | 👤 Browser (am besten auf einem zweiten Rechner/Mac testen) | ☐ offen |
| 9.4 | Responsives Verhalten auf kleineren Bildschirmen (Laptop-Breite) ist nutzbar | 👤 Browser | ☐ offen |
| 9.5 | Kein Secret (Azure-Key, JWT-Secret) taucht in Git-Historie oder in Browser-DevTools-Netzwerk-Tab im Klartext auf (JWT-Payload ist zwar sichtbar, aber unsigniert nicht fälschbar — das ist gewollt) | 👤 Review | ☐ offen |

---

## Noch zu schreibende automatisierte Tests (Vorschlag für nächste Iteration)

- `test_documents.py`: `extract_text()` für PDF/DOCX/TXT, `chunk_text()` Grenzfälle (sehr kurzer Text, Text genau an der Token-Grenze, Text mit extrem langem Einzelabsatz)
- `test_role_suggestion.py`: Keyword-Treffer, Embedding-Centroid-Logik, Kaltstart-Fall (<3 Referenzdokumente)
- Erweiterung von `test_tenancy.py` oder neue `test_documents_api.py`: `/documents/suggest` und `/documents` End-to-End über den echten TestClient, inkl. 403 für `support`-Rolle

## Nicht Teil dieses Testplans (bewusst ausgeklammert)

- Lasttests/Performance bei hunderten gleichzeitigen Nutzern — erst relevant ab echten zahlenden Kunden mit entsprechendem Volumen
- Browser-Kompatibilität über Chrome hinaus (Safari/Firefox) — nachholen, sobald eine erste Demo an echte Kunden geht
