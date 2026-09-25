# Mini-Vektordatenbank mit RBAC

Eine minimale Vektordatenbank für KMU-Support-Tickets, bei der die Rollenprüfung
(RBAC) fest in die Such-Engine eingebaut ist statt nachträglich in der
Oberfläche. Dient als Lern- und Demo-Grundlage für ein späteres Business rund
um durchgängig sichere Vektorsuche.

## Setup & Ausführen

```bash
pip install -r requirements.txt
python main.py          # Demo: gleiche Suche, zwei Rollen, unterschiedliche Ergebnisse
python test_rbac.py     # 5 Tests, die die Rollentrennung beweisen
```

## Projektstruktur

- `data.py` – Beispiel-Tickets, gemischt aus allgemeinen (`allowed_roles=["all"]`)
  und sensiblen Finanz-/HR-Tickets (`allowed_roles=["management"]`)
- `auth.py` – simulierte User→Rolle-Zuordnung (kein echtes Login)
- `db.py` – `MiniVectorDB` mit `add()` und `search()`, inkl. Embedding,
  Cosine Similarity, Brute-Force-Suche und Rollenfilter
- `main.py` – Demo: dieselbe Anfrage von zwei Usern mit unterschiedlichen Rollen
- `test_rbac.py` – Tests, die beweisen, dass unautorisierte Nutzer sensible
  Tickets nie sehen, auch wenn sie der beste inhaltliche Treffer wären

**Nicht Teil dieses Schritts:** Azure-Anbindung, echtes JWT/Login, Web-API. Das
Platzhalter-Embedding in `db.py` (Wortüberlappung statt trainiertem Modell) ist
bewusst austauschbar gehalten für einen späteren Schritt mit echtem Modell.

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
