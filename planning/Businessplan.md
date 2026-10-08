# Businessplan Vektordatenbank mit RBAC

Oct 1, 2026 · @Arian

## Executive Summary

Eine selbst entwickelte Mini-Vektordatenbank, die Dokumente per KI-ähnlicher Bedeutungssuche durchsuchbar macht — mit einer Besonderheit, die das eigentliche Geschäftsmodell trägt: **Zugriffskontrolle wird serverseitig erzwungen, nicht nur in der Oberfläche simuliert.** Ein Nutzer ohne passende Rolle oder aus einem anderen Mandanten sieht ein Dokument nie — selbst wenn es inhaltlich der beste Treffer wäre, selbst wenn er versucht, seine Rolle technisch zu fälschen.

**Technischer Stand:** vollständig entwickelt und getestet — JWT-Login mit bcrypt-Passwort-Hashing, SQLite-Persistenz, Audit-Log, Multi-Tenancy (mehrere Mandanten strikt datengetrennt auf derselben Infrastruktur), 18 automatisierte Tests, 4 GitHub Issues vollständig abgearbeitet und geschlossen. Live demonstrierbar unter `/demo`.

**Strategische Ausrichtung:** Start als Einzelperson, ohne Kapital, neben einem neuen Hauptjob. Bewusste Entscheidung gegen hoch regulierte Branchen (Kanzleien, Gesundheitswesen, Banken) zugunsten von zwei konkreten, schnell erreichbaren Nischen mit niedrigen Compliance-Hürden: Immobilienmarketing (eigene Branche, eigenes Netzwerk) und bezahlte Coaching-/Kurs-Communities (zweites Standbein). Ziel ist kein Blitzstart, sondern ein kontrolliert wachsendes Nebengeschäft mit echter Option auf spätere Vollzeit-Skalierung.

## Use Cases

### 1. Freelancer & kleine Agenturen mit mehreren Mandaten (priorisiert, Phase 1)

Freelancer und kleine Agenturen — in Marketing, Design, Beratung oder Immobilienmarketing — arbeiten häufig gleichzeitig für mehrere Kunden, teils direkte Konkurrenten in derselben Nische oder Region. Projektunterlagen, Strategiepapiere und interne Notizen pro Mandat müssen strikt getrennt bleiben, besonders wenn Subunternehmer oder freie Mitarbeitende nur für bestimmte Kunden arbeiten sollen.

**Konkreter Einstieg: Immobilienmarketing.** Exposé-Texte, Grundrisse, Zielgruppen-Strategien und Preisverhandlungs-Notizen pro Objekt dürfen nie zwischen konkurrierenden Maklern/Bauträgern vermischt werden — besonders wenn Subunternehmer (Fotografen, Texter, Social-Media-Manager) nur für bestimmte Projekte arbeiten sollen.

**Lösung:** Eine durchsuchbare interne Wissensbasis, `tenant_id` = Kunde/Projekt-Portfolio, Rolle = Fotograf/Texter/Projektleiter — oder analog in anderen Branchen: Designer/Berater/Consultant — mit Zugriff nur auf zugewiesene Projekte. Der Gründer ist dabei selbst erster Nutzer im Immobilienmarketing (Dogfooding) — das liefert eine authentische Verkaufsstory statt einer theoretischen Demo, und das gleiche Setup lässt sich 1:1 auf andere Freelancer-/Agentur-Nischen übertragen.

### 2. Bezahlte Coaching-/Kurs-Communities (Phase 2)

Creator mit laufender, zahlender Multi-Tier-Community (Skool/Circle, 200–3000 Mitglieder) haben zwei Probleme gleichzeitig: ihr Content-Archiv wird mit der Zeit unauffindbar, und Premium-Inhalte sollen klar von Basis-Inhalten getrennt sein (als Kaufanreiz).

**Lösung:** KI-Suche über das gesamte Archiv (Transkripte, Kursmodule, Posts), Ergebnisse gefiltert nach Mitgliedschaftsstufe — dieselbe RBAC-Logik, nur ist die "Rolle" hier die Preisstufe statt eine Jobbezeichnung. Technisch aufwändiger als Fall 1 (keine offenen APIs bei Skool/Circle, periodischer statt Live-Import), deshalb zeitlich nachgelagert.

### Validierte, aber zurückgestellte Alternativen

Aus einer systematischen 10-Perspektiven-Analyse zusätzlich identifiziert, bewusst nicht priorisiert: Agenturen/Consultancies mit Freelancern auf mehreren Kundenprojekten (ähnliches Muster wie Fall 1, aber ohne eigene Branchenerfahrung), interne Wissenssuche für E-Commerce-Teams. Beide bleiben als Erweiterungsoptionen bestehen, sobald Kapazität für ein drittes Standbein da ist.

## Zielgruppe

| Segment | Buyer Persona | Wo zu finden |
| --- | --- | --- |
| Freelancer & kleine Agenturen (Immobilienmarketing, Marketing, Design, Beratung u.ä.) | 1–10 Personen, arbeiten für mehrere, teils konkurrierende Kunden parallel, brauchen interne Mandats-/Projekttrennung | Branchennetzwerk und -foren je nach Fachrichtung |
| → Einstiegspunkt: Immobilienmarketing | Eigene Branche, eigenes Netzwerk — schnellster Weg zum ersten Kunden | Direkt über bestehende Kontakte ansprechbar |
| Coaching-Communities | Creator mit laufender Skool/Circle-Community, 200–3000 zahlende Mitglieder | Skool/Circle direkt, IndieHackers, Twitter/X unter Produktname |

Das zugrunde liegende Muster — mehrere, teils konkurrierende Mandate/Projekte, die strikt getrennt bleiben müssen — ist branchenunabhängig. Immobilienmarketing ist der Einstiegspunkt, weil dort eigene Erfahrung und eigenes Netzwerk den schnellsten Zugang zu ersten Gesprächen ermöglichen — nicht, weil das Produkt darauf beschränkt wäre.

### Explizit ausgeschlossene Segmente

- **Recruiting/Personalvermittlung** — wirkt compliance-arm, ist es aber nicht: Lebensläufe enthalten oft besondere Datenkategorien nach Art. 9 DSGVO (Nationalität, Foto, Gesundheitslücken). Ein RBAC-Bug wäre dort meldepflichtig.
- **Gesundheitswesen, Kanzleien, Banken** — hohe regulatorische Hürden, lange Vertriebszyklen, Zertifizierungsanforderungen, die ein Solo-Gründer ohne Kapital nicht kurzfristig stemmen kann.
- **Handwerksbetriebe** — niedrige digitale Zahlungsbereitschaft, langsamer Vor-Ort-Vertrieb, widerspricht der Ortsunabhängigkeit.

Durchgängiges Auswahlkriterium: Branchen, in denen ein Datenleck ärgerlich, aber nicht melde- oder haftungspflichtig ist.

## Pricing & Geschäftsmodell

**Phase 1–2 — Festpreis pro Einzelprojekt** (kein SaaS von Anfang an, bewusst):

- Ersteinrichtung: **1.500–2.500 €**
- Pilot-Einstieg: **500 €**, voll anrechenbar auf das Setup — verschiebt das Risiko vom Kunden zum Anbieter, wichtig weil das Versprechen abstrakt ist, bis man es live sieht

**Phase 3 — Übergang zu SaaS**, erst ab 3–5 bezahlten Einzelprojekten, nicht vorher:

- Gestaffeltes Abo: **49 € (Starter) / 99–149 € (Pro) / 199 € (Team)** pro Monat

**Warum Festpreis vor SaaS:** Ein Einzelprojekt bringt schneller echtes Geld als ein generisches Produkt zu bauen, das noch niemand zahlt. Multi-Tenancy ist technisch bereits eingebaut — die spätere Produktisierung ist eine Frage des Self-Serve-Onboardings, nicht der Architektur.

**Azure-Infrastrukturkosten:** werden gebündelt, nicht pro Kunde durchgereicht. Embedding-Kosten liegen real bei Centbeträgen pro Kunde (z.B. \~500 Dokumente einmalig einbetten ≈ 0,005 $) — ein eigener Azure-Account pro Kunde würde nur Reibung erzeugen, ohne finanziellen Vorteil. Absicherung: Azure-Budget-Warnung bei ca. 20 €/Monat.

## Mitarbeiter & Organisation

**Aktuell:** Einzelperson, nebenberuflich neben einem neuen Hauptjob. Bewusst kein frühes Einstellen von Mitarbeitenden — bei noch unsicherem, langsam anlaufendem Cashflow wäre eine Festanstellung ein Fixkosten-Risiko ohne Gegenwert.

**KI-gestützte Unterstützung statt früher Personaleinstellung:** Entwicklung, Architekturentscheidungen, Marketing-Material und operative Routinen (tägliches Status-Briefing, GitHub-Überwachung) laufen über Claude als durchgängigen Entwicklungs- und Organisationspartner. Das ersetzt keine Vertriebsgespräche oder Entscheidungen (die bleiben beim Gründer), reduziert aber den Bedarf an frühen Festanstellungen für Entwicklung und Koordination erheblich.

**Realistischer Wachstumspfad:**

1. Jetzt – nach ersten 3–5 Kunden: Solo, alles selbst
2. Nach Produktisierung (Phase 3): punktuelle Freelance-Unterstützung bei Bedarf (z.B. Content/Design), keine Festanstellung
3. Bei stabilem, planbarem MRR: erste Teilzeitkraft für Vertrieb/Support denkbar
4. Erst bei nachhaltigem Wachstum: Entscheidung zwischen Vollzeit-Wechsel in das eigene Unternehmen oder bewusstem Verbleib als Nebeneinkommen

## Zukunftsvision

**Kurzfristig (6–12 Monate):** erste 3–5 zahlende Kunden über beide Standbeine, validiertes Pricing, erste echte Referenzen statt nur technischer Demo.

**Mittelfristig (Jahr 2):** Übergang zu einem Self-Serve-SaaS-Angebot für das am besten validierte Segment, gestützt auf die bereits bestehende Multi-Tenancy-Architektur. Prüfung einer dritten Nische nach demselben Auswahlmuster (niedrige Compliance-Hürden, eigene oder leicht zugängliche Branchennähe).

**Langfristig:** Die zugrunde liegende Architektur — Rollenfilter plus Tenant-Filter vor jeder Suche, serverseitig erzwungen — ist generisch genug, um auf jede Branche mit mehreren Zugriffsstufen und mehreren Kunden auf gemeinsamer Infrastruktur übertragen zu werden. Ob daraus ein Vollzeit-Unternehmen wird, das den Hauptjob ersetzt, oder ein bewusst kleingehaltenes, stabiles Nebeneinkommen bleibt — beide Pfade bleiben offen und werden anhand des tatsächlichen Wachstums entschieden, nicht vorab festgelegt.
