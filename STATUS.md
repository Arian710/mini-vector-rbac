# Projektstand: Mini-Vektordatenbank mit RBAC

Stand: 2026-10-08 (UI/UX-Überarbeitung)

## Was fertig ist

**Produkt-Kern**
- Vektordatenbank mit serverseitigem RBAC- und Multi-Tenancy-Filter (`db.py`), Azure-OpenAI-Embeddings produktiv (`embeddings.py`), Azure Document Intelligence als OCR-Fallback für gescannte PDFs
- Automatisches Chunking langer Dokumente (Token-Limit-Problem gelöst)
- Individuelle Rollen-Verwaltung durchs Management: eigene Rollen anlegen/bearbeiten/löschen, KI-gestützter Rollenvorschlag beim Upload (Keyword-Treffer + Embedding-Ähnlichkeit zum Rollen-Ankervektor + Centroid aus bereits getaggten Dokumenten), optionale Branchen-Rollenvorlagen als Starthilfe (Steuerberatung, Marketing-/Design-Agentur, Beratung, Immobilienmarketing)
- Login gehärtet: Rate-Limiting (5 Versuche/Minute) + Passwort-Komplexitätsregeln
- Persistenz auf Azure Database for PostgreSQL migriert (SQLite-Datei war auf Azure App Service nicht garantiert persistent)

**Dashboard (React/Vite)**
- Login, Sidebar/Layout, Suche, Obsidian-artige Graph-Ansicht, Dokumenten-Upload mit KI-Rollenvorschlag, Rollen-Verwaltung inkl. Branchenvorlagen
- Session-Timeout leitet automatisch zum Login zurück
- **UI/UX-Überarbeitung (2026-10-08):** Design-System in `index.css` (Tokens, Buttons, Karten, Formulare) statt Inline-Styles; Dark/Light/System-Theme; responsive mit Mobile-Drawer; SVG-Icons statt Emojis; neuer Login (Split-Layout, Passwort anzeigen, Demo-User per Klick); Suche mit Skeletons, Treffer-Highlighting, Score-Balken, Suchverlauf; Graph mit Detail-Panel, Zoom und Theme-Farben; Upload mit Drag-&-Drop und Stepper; Rollen mit Lösch-Bestätigung und Toasts; **neue Audit-Log-Seite** (nutzt bestehenden `/audit-log`-Endpoint) mit Kennzahlen und Filtern; 404-Seite; Management-Routen im Frontend abgesichert (echte Prüfung bleibt serverseitig). Visuell geprüft gegen einen Mock-Server (kein Azure-Zugang auf diesem Rechner), noch nicht gegen das echte Backend

**Tests**
- `test_rbac.py`, `test_auth.py`, `test_audit.py`, `test_tenancy.py`, `test_security.py` (neu: Passwort-Stärke, Rate-Limit) — laufen alle gegen echtes Azure-Postgres (Schema-basierte Testisolation statt Datei-basiert), bewusste Entscheidung für volle Test/Prod-Parität
- `TESTPLAN.md` als lebender Testfall-Katalog, wird vor Veröffentlichung gemeinsam durchgegangen

**Business/Strategie**
- Pivot entschieden: Phase 1 jetzt "Freelancer & kleine Agenturen" allgemein statt nur Immobiliennetzwerk (das ursprüngliche Netzwerk trägt nicht mehr: nur noch 2 Kontakte, einer nutzt schon ein Konkurrenzsystem)
- Zielgruppenliste & Akquise-Tracker mit recherchierten, echten Kanälen aufgebaut (Freelancer-Plattformen, IHK-Netzwerke, Online-Communities — ohne erfundene Quellen)
- Security-/Hosting-Konzept für Azure durchdacht; Identity-Provider-Frage (Entra External ID vs. eigenes Auth) bewusst diskutiert und vorerst beim aktuellen Ansatz geblieben
- Living Docs in Claude: Fahrplan, Businessplan, Feature-Backlog, Zielgruppenliste & Akquise-Tracker — Snapshots davon liegen jetzt unter [`planning/`](planning/)

## Was offen ist

- **WhatsApp-Integration**: wartet auf Meta Business Verification (liegt bei Arian) — dafür muss zuerst die Gewerbe-Frage geklärt werden (bestehendes Gewerbe erweitern vs. neues Gewerbe vs. Freiberufler-Status nach §18 EStG; keine abschließende Rechtsberatung, Empfehlung: kurzer Anruf beim Gewerbeamt/Steuerberater)
- Neues UI einmal gegen das echte Backend durchklicken (Upload-Flow, Rollen löschen, Audit-Log); danach Feinschliff nach Feedback
- Erste Kunden über die Zielgruppenliste ansprechen
- User-Verwaltung (über reine Rollen-Verwaltung hinaus) — bewusst zurückgestellt, im Feature-Backlog
- Migration auf einen Managed-Identity-Provider (z.B. Entra External ID) — bewusst zurückgestellt, im Feature-Backlog

## Dateien in diesem Repo

- [`planning/Fahrplan.md`](planning/Fahrplan.md) — Phasenplan, Pipeline-Tracker, tägliche Routinen
- [`planning/Businessplan.md`](planning/Businessplan.md) — Use Cases, Zielgruppe, Pricing, Wettbewerb
- [`planning/Feature-Backlog.md`](planning/Feature-Backlog.md) — v2/v3-Ideen
- [`planning/Zielgruppenliste.md`](planning/Zielgruppenliste.md) — konkrete Akquise-Kanäle + Tracker-Vorlage

Diese Dateien sind Snapshots der jeweils aktuellen Claude-Docs-Artefakte zum Zeitpunkt dieses Commits — die Live-Dokumente in Claude bleiben die Quelle der Wahrheit für laufende Bearbeitung.
