# Fahrplan: Vector-RBAC-Produkt zur Marktreife

Oct 1, 2026 · @Arian

## Zusammenfassung & Entscheidung

Zwei Standbeine, zeitlich versetzt statt parallel von Anfang an:

1. **Freelancer & kleine Agenturen (Phase 1, sofort)** — breiteste Zielgruppe ohne Branchen-Lock-in. Das urspruengliche Immobilienmarketing-Netzwerk traegt nicht mehr als alleiniger schneller Weg (nur noch 2 Kontakte, einer nutzt bereits ein Konkurrenzsystem).
2. **Coaching-/Kurs-Communities (Phase 2, ab Monat 2)** — technisch aufwändiger (keine fertigen APIs bei Skool/Circle), deshalb als zweites Standbein, nicht als Starter.

**Bewusst verworfen** (aus der 10-Perspektiven-Analyse):

- *Recruiting-Mandantentrennung* — wirkt compliance-arm, ist es aber nicht: Lebensläufe enthalten oft besondere Datenkategorien nach Art. 9 DSGVO (Nationalität, Foto, Gesundheitslücken). Ein RBAC-Bug wäre dort meldepflichtig, kein Schönheitsfehler.
- *Handwerksbetriebe* — langsamer Vertrieb, niedrige Zahlungsbereitschaft, WhatsApp-ToS-Fragen, widerspricht Ortsunabhängigkeit.

Durchgängiges Prinzip aus allen 10 Agenten-Perspektiven: der Flaschenhals ist nie die Technik (die steht), sondern Vertrauen und Vertrieb bei null bestehendem Netzwerk — das gilt inzwischen auch für Immobilienmarketing, seit das dortige Netzwerk weitgehend weggebrochen ist (Stand 2026-10-02).

## Phase 0 — Rechtliche Basis (diese Woche)

- [ ] Nebentätigkeitsklausel im neuen Arbeitsvertrag prüfen — blockiert: noch kein Arbeitsvertrag vorhanden, andere rechtliche Schritte bewusst zurückgestellt bis dahin
- [ ] Prüfen, ob das über dein bestehendes Gewerbe (Immobilienmarketing-Selbstständigkeit) läuft oder ein eigenes Gewerbe nötig ist
- [ ] Haftungsfrage klar machen: Berufs-/Vermögensschadenhaftpflicht prüfen, die auch IT-Dienstleistung abdeckt — als Einzelperson ohne Haftungsbeschränkung trägst du bei einem Datenleck das volle Risiko
- [ ] Secrets-Management/Backup-Basics fest etablieren, bevor echte Kundendaten gehostet werden (größtes übersehenes Risiko laut Skeptiker-Agent — nicht die DSGVO-Paragraphen selbst)
- [ ] README im Repo um einen „Verfügbar für Auftragsarbeit“-Absatz ergänzen
- [ ] Demo-GIF erstellen: Szene 1 (Browser-Vergleich Anna/Bernd) fertig, gekuerzt, einsatzbereit. Szene 2 (Terminal, 401/403-Ablehnung via demo\_attack.sh) steht noch aus

## Phase 1 — Freelancer & kleine Agenturen (Wochen 1–4)

**Zielgruppe:** Freelancer/kleine Agenturen mit mehreren Mitarbeitenden oder Subunternehmern, die für mehrere Kunden/Projekte gleichzeitig arbeiten (z.B. Marketing-, Design- oder Beratungsagenturen) — ohne bestehendes persönliches Netzwerk in einer einzelnen Branche, da das ursprüngliche Immobilien-Netzwerk nicht mehr ausreicht.

**Schritt 1 — Eigene Nutzung als Demo (Woche 1):** Baue dir selbst eine kleine Instanz für deine eigenen Kundenprojekte (Exposés, Briefings, Marketingstrategien pro Objekt, `tenant_id` = Kunde/Objekt). Das ist gleichzeitig dein Arbeitswerkzeug und deine stärkste Verkaufsstory: „Ich nutze das selbst in meinem eigenen Geschäft.“

**Schritt 2 — Ansprache (Wochen 2–3):**

- [ ] Zielgruppen-Liste ohne bestehendes Netzwerk aufbauen: Branchenforen, lokale Unternehmerverbände, Freelancer-Plattformen (z.B. Facebook-Gruppen, IHK-Netzwerke, Freelancer-Plattformen - Details siehe Zielgruppenliste für Agenturen)
- [ ] Lokale Makler-Büros mit mehreren Mitarbeitenden, direkt oder über Branchenverzeichnisse
- [ ] Immobilien-Facebook-Gruppen und -Foren (DACH-Raum)
- [ ] Erstnachricht mit Demo-GIF statt langer Erklärung

**Pricing:**

- Festpreis-Ersteinrichtung: **1.500–2.500 €**
- Pilot-Rabatt: **500 €**, voll anrechenbar auf das Setup — verschiebt das Risiko vom Kunden zu dir, wichtig weil das Versprechen abstrak ist, bis man es live sieht

**Meilenstein Ende Phase 1:** erstes bezahltes Pilotprojekt, realistisch 2–6 Wochen bei aktiver täglicher Ansprache.

## Phase 2 — Coaching-Communities (Monate 2–3)

Erst starten, wenn Phase 1 einen zahlenden Kunden gebracht hat — technisch deutlich aufwändiger, da Skool/Circle keine umfangreichen offenen APIs haben.

**Technische Pipeline:**

- [ ] Dateneingang: Video-Transkripte (Zoom/Loom), Kursmodul-Texte, manuell exportierte Posts
- [ ] Chunking: Dokumente in Abschnitte zerlegen (pro Transkript-Absatz/Video-Kapitel)
- [ ] Embedding + Speicherung über das bestehende `embeddings.py`/`db.py`/`storage.py` — `tenant_id` = Community, `allowed_roles` = Mitgliedschaftsstufe
- [ ] Mitgliedschaftsstufen-Sync: anfangs CSV-Liste des Creators, später Zapier-Webhook wo verfügbar
- [ ] Suchoberfläche: Magic-Link-Login, Ergebnisse mit Zeitstempel-Link zurück ins Video, Premium-Treffer für Free-Mitglieder als Upgrade-Teaser statt leer

**Ansprache:** Skool/Circle-Creator direkt, IndieHackers, Twitter/X unter Produktname (nicht Privatprofil — passt zur „kein LinkedIn\"-Anforderung).

**Pricing:** ähnlich wie Phase 1, Festpreis-Setup zuerst, später Abo-Option.

## Phase 3 — Produktisierung Richtung SaaS

Erst ab **3–5 bezahlten Einzelprojekten**, nicht vorher — vorher wäre es spekulative Arbeit an einer generischen Lösung ohne validierte Nachfrage.

- [ ] Muster aus den Einzelprojekten identifizieren: was war bei allen Kunden gleich, was unterschiedlich?
- [ ] Gemeinsame Codebasis aus den Bespoke-Projekten extrahieren (Multi-Tenancy ist bereits eingebaut — genau dafür gedacht)
- [ ] Self-Serve-Onboarding bauen (Signup, Daten-Import-Flow, Rollen-Zuweisung ohne dich als Flaschenhals)
- [ ] Abo-Preise einführen: gestaffelt **49 € (Starter) / 99–149 € (Pro) / 199 € (Team)** pro Monat

**Entscheidung: Azure-Kosten werden gebündelt, nicht pro Kunde durchgereicht.** Embedding-Kosten liegen real bei Centbeträgen pro Kunde (z.B. \~500 Dokumente einmalig einbetten ≈ $0,005) — ein Rundungsfehler gegenüber den Festpreisen. Ein eigener Azure-Account pro Kunde würde nur unnötige Reibung erzeugen, ohne echten finanziellen Vorteil. Absicherung: Azure Cost Management Budget-Warnung bei ca. 20 €/Monat einrichten. Erst bei wirklich großen Kunden (zehntausende Dokumente, sehr hohe Suchfrequenz) wäre ein nutzungsbasierter Aufpreis zu prufen.

Bis dahin bleibt jedes Projekt ein Einzelauftrag mit Festpreis — das bringt schneller echtes Geld als früh in eine Plattform zu investieren, die noch niemand zahlt.

## Tägliche Routinen & Rollenverteilung

Ich bin dein Entwickler und organisatorischer Unterstützer — mit einer wichtigen, bewussten Grenze: Ich kann nichts automatisch in deinem Namen **versenden oder veröffentlichen** (E-Mails, Forenposts, Nachrichten). Das verlangt jedes Mal dein ausdrückliches Go, nicht weil ich es nicht könnte, sondern weil das zu den Aktionen gehört, bei denen ich immer erst nachfrage — sonst könnte in deinem Namen etwas rausgehen, das du nie gesehen hast.

**Was ich laufend automatisiert übernehme (eingerichtet als Routine):**

- Tägliche Zusammenfassung offener GitHub Issues/PRs im Repo
- Erinnerung an offene Pipeline-Einträge aus der Tabelle unten, die seit X Tagen ohne nächsten Schritt sind
- Entwürfe für Outreach-Nachrichten, Angebote, Posts — fertig zum Absenden, aber nie automatisch abgeschickt

**Was nur du tun kannst/darfst:**

- Nachrichten tatsächlich versenden, Posts tatsächlich veröffentlichen
- Gespräche/Calls führen, Vertrauen aufbauen
- Verträge/Angebote final absegnen und unterschreiben
- Entscheidungen über Nebentätigkeit, Gewerbe, Haftung (Phase 0) — das sind Rechtsfragen, die ich einordnen, aber nicht für dich entscheiden kann

## Pipeline-Tracker

Verwandte Dokumente: [Businessplan Vektordatenbank mit RBAC](https://claude.ai/artifact/6sjMpjZS8vG5NvRmcViYup) (Use Cases, Zielgruppe, Pricing, Wettbewerb), [Feature-Backlog & Ideen-Board](https://claude.ai/artifact/5KkVLzztovvk3fmCFZ7DV3) (v2/v3-Ideen) und [Zielgruppenliste & Akquise-Tracker](https://claude.ai/artifact/0ba59922-e409-4f6a-b403-55ee257fce1d) (konkrete Kanäle + Tracker ohne bestehendes Netzwerk).

| Kontakt | Segment | Status | Nächster Schritt | Datum |
| --- | --- | --- | --- | --- |
| (eigene Instanz) | Freelancer/Agenturen (allgemein) | Dashboard komplett (Login, Suche, Graph, Upload, Rollen-Verwaltung). Login gehaertet (Rate-Limiting + Passwort-Regeln). Persistenz auf Azure Database for PostgreSQL umgestellt (Azure-App-Service-faehig, SQLite-Dateispeicher war nicht persistent genug fuer Hosting). Azure-Embeddings, Chunking, OCR produktiv. Session-Timeout leitet automatisch zum Login zurueck. | Branchen-Rollenvorlagen umgesetzt. Naechster Schritt: WhatsApp-Anbindung - Meta-Business-Verifizierung liegt bei dir (Gewerbeanmeldung aus Phase 0 klaeren, dann business.facebook.com), ich bereite Webhook/Integration parallel vor. Weiterhin offen: Dashboard-Design verfeinern, Zielgruppen-Liste ohne bestehendes Netzwerk aufbauen, erste Kunden ansprechen. | 2026-10-02 |
| — | Freelancer/Agenturen (allgemein) | Noch nicht angesprochen | Zielgruppen-Liste ohne bestehendes Netzwerk aufbauen (Foren/Verbände/Plattformen) | — |
| — | Coaching-Community | Backlog (Phase 2) | — | — |
