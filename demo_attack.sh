#!/bin/bash
# Demo-Skript fuer die zweite GIF-Szene: Angriffsversuche gegen die API.
# Voraussetzung: Server laeuft (uvicorn api:app --reload), Datenbank geseedet.
#
# Zum Aufnehmen: dieses Skript ausfuehren, waehrend ScreenToGif das Terminal
# filmt. Die Pausen (sleep) geben dir Zeit, jede Antwort kurz lesen zu lassen.

BASE="http://127.0.0.1:8000"

echo "=== 1. Normaler Login als bernd (management) ==="
TOKEN=$(curl -s -X POST $BASE/login -H "Content-Type: application/json" \
  -d '{"username":"bernd","password":"demo1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token erhalten."
sleep 2

echo
echo "=== 2. Suche OHNE Token ==="
curl -s -i -X POST $BASE/search -H "Content-Type: application/json" \
  -d '{"query":"Gehalt Budget"}' | head -1
sleep 2

echo
echo "=== 3. Suche mit MANIPULIERTEM Token (letztes Zeichen veraendert) ==="
curl -s -i -X POST $BASE/search -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}X" -d '{"query":"Gehalt Budget"}' | head -1
sleep 2

echo
echo "=== 4. support-User versucht /audit-log aufzurufen ==="
TOKEN_ANNA=$(curl -s -X POST $BASE/login -H "Content-Type: application/json" \
  -d '{"username":"anna","password":"demo1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -i -X GET $BASE/audit-log -H "Authorization: Bearer $TOKEN_ANNA" | head -1
sleep 2

echo
echo "=== 5. management-User ruft /audit-log erfolgreich auf ==="
curl -s -X GET $BASE/audit-log -H "Authorization: Bearer $TOKEN" | python -m json.tool
