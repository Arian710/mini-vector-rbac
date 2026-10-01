"""
Statische Live-Demo-Seite fuer die API (Route /demo in api.py).

Zeigt das Kernversprechen in einem Blick: zwei User, dieselbe Suche,
unterschiedliche Ergebnisse - kein Terminal noetig, ideal fuer ein kurzes
Demo-GIF. Reiner Vanilla-JS-Frontend-Code, kein Build-Schritt.
"""

DEMO_HTML = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Mini-Vektordatenbank mit RBAC &mdash; Live-Demo</title>
<style>
  :root { --teal: #0F6E56; --teal-deep: #0A4536; --ink: #1C1C1A; --muted: #6B6A63; --rule: #DAD7CC; --bg: #F8F7F2; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink);
         max-width: 920px; margin: 48px auto; padding: 0 20px; }
  h1 { font-size: 21px; font-weight: 600; margin-bottom: 4px; }
  .sub { color: var(--muted); font-size: 14px; margin-bottom: 28px; }
  .searchbar { display: flex; gap: 8px; margin-bottom: 32px; }
  input[type=text] { flex: 1; padding: 11px 14px; border: 1px solid var(--rule); border-radius: 8px; font-size: 15px; }
  input[type=text]:focus { outline: 2px solid var(--teal); outline-offset: -1px; }
  button { padding: 11px 22px; border: none; border-radius: 8px; background: var(--teal);
           color: white; font-size: 15px; font-weight: 500; cursor: pointer; }
  button:hover { background: var(--teal-deep); }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .col h2 { font-size: 16px; margin: 0 0 2px; }
  .col .role { color: var(--muted); font-size: 13px; margin-bottom: 14px; }
  .col .role b { color: var(--teal-deep); }
  .result { background: white; border: 1px solid var(--rule); border-radius: 10px;
            padding: 12px 14px; margin-bottom: 10px; }
  .result .score { color: var(--muted); font-size: 11px; font-family: ui-monospace, monospace; margin-bottom: 4px; }
  .empty { color: var(--muted); font-style: italic; padding: 28px 14px; text-align: center;
           border: 1px dashed var(--rule); border-radius: 10px; }
</style>
</head>
<body>
<h1>Mini-Vektordatenbank mit RBAC</h1>
<div class="sub">Dieselbe Suche, zwei Rollen &mdash; jeder sieht nur, wofuer er berechtigt ist.</div>

<div class="searchbar">
  <input type="text" id="q" value="Gehaltserhoehung Budget Quartal">
  <button onclick="runSearch()">Suchen</button>
</div>

<div class="cols">
  <div class="col">
    <h2>Anna</h2>
    <div class="role">Rolle: <b>support</b></div>
    <div id="results-anna"></div>
  </div>
  <div class="col">
    <h2>Bernd</h2>
    <div class="role">Rolle: <b>management</b></div>
    <div id="results-bernd"></div>
  </div>
</div>

<script>
let tokens = {};

async function login(username, password) {
  const resp = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  const data = await resp.json();
  return data.access_token;
}

async function search(token, query) {
  const resp = await fetch("/search", {
    method: "POST",
    headers: {"Content-Type": "application/json", "Authorization": "Bearer " + token},
    body: JSON.stringify({query, top_k: 3})
  });
  return resp.json();
}

function render(containerId, results) {
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  if (!results.length) {
    el.innerHTML = '<div class="empty">(keine sichtbaren Treffer)</div>';
    return;
  }
  for (const r of results) {
    const div = document.createElement("div");
    div.className = "result";
    div.innerHTML = '<div class="score">Score: ' + r.score + '</div><div>' + r.text + '</div>';
    el.appendChild(div);
  }
}

async function runSearch() {
  const query = document.getElementById("q").value;
  if (!tokens.anna) tokens.anna = await login("anna", "demo1234");
  if (!tokens.bernd) tokens.bernd = await login("bernd", "demo1234");
  const [resAnna, resBernd] = await Promise.all([
    search(tokens.anna, query),
    search(tokens.bernd, query)
  ]);
  render("results-anna", resAnna);
  render("results-bernd", resBernd);
}

window.onload = runSearch;
</script>
</body>
</html>
"""
