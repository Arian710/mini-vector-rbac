const BASE_URL = "http://127.0.0.1:8000";

async function parseOrThrow(response) {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // keine JSON-Antwort, bleib beim statusText
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function login(username, password) {
  const response = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return parseOrThrow(response);
}

export async function search(token, query, topK = 5) {
  const response = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query, top_k: topK }),
  });
  return parseOrThrow(response);
}

export async function suggestDocument(token, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${BASE_URL}/documents/suggest`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  return parseOrThrow(response);
}

export async function saveDocument(token, { text, allowedRole, customerLabel }) {
  const response = await fetch(`${BASE_URL}/documents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text, allowed_role: allowedRole, customer_label: customerLabel || null }),
  });
  return parseOrThrow(response);
}

export async function graphData(token) {
  const response = await fetch(`${BASE_URL}/graph-data`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseOrThrow(response);
}

/**
 * Liest username/role/tenant_id aus dem JWT-Payload fuer die Anzeige
 * (z.B. "Rolle: management" in der Sidebar). KEINE Signaturpruefung -
 * das macht ausschliesslich der Server bei jeder Anfrage (siehe
 * auth.decode_access_token in auth.py). Hier geht es nur um UI-Anzeige,
 * niemals um eine Sicherheitsentscheidung im Frontend.
 */
export function decodeTokenPayload(token) {
  const payloadBase64 = token.split(".")[1];
  const json = atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/"));
  return JSON.parse(json);
}
