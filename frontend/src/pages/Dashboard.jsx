import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { search as apiSearch } from "../api";
import Layout from "../components/Layout";
import ResultList from "../components/ResultList";
import GraphView from "../components/GraphView";
import Icon from "../components/Icon";

const EXAMPLES = ["Gehaltserhöhung Budget Quartal", "Rechnung Mahnung Zahlungsfrist", "Urlaub Vertretung Regelung"];

function recentKey(user) {
  return `mvrbac_recent_${user?.tenant_id}_${user?.sub}`;
}

function loadRecent(user) {
  try {
    return JSON.parse(localStorage.getItem(recentKey(user))) || [];
  } catch {
    return [];
  }
}

function saveRecent(user, query) {
  const next = [query, ...loadRecent(user).filter((q) => q !== query)].slice(0, 5);
  try {
    localStorage.setItem(recentKey(user), JSON.stringify(next));
  } catch {
    // Storage gesperrt - Verlauf ist optional
  }
  return next;
}

export default function Dashboard() {
  const { token, user } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [results, setResults] = useState(null);
  const [view, setView] = useState("list"); // "list" | "graph"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recent, setRecent] = useState(() => loadRecent(user));

  async function runSearch(text) {
    const q = text.trim();
    if (!q) return;
    setQuery(q);
    setView("list");
    setLoading(true);
    setError(null);
    try {
      const data = await apiSearch(token, q);
      setResults(data);
      setSubmitted(q);
      setRecent(saveRecent(user, q));
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const suggestions = recent.length > 0 ? recent : EXAMPLES;

  return (
    <Layout title="Suche">
      <div className="page page-wide">
        <div className="page-header">
          <h1>Suche</h1>
          <p>Finde Dokumente nach Bedeutung. Du siehst nur Inhalte deines Mandanten und deiner Rolle.</p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            runSearch(query);
          }}
          role="search"
          className="stack-sm"
        >
          <div className="search-box">
            <span className="input-icon">
              <Icon name="search" size={19} />
            </span>
            <input
              className="input"
              placeholder="Was suchst du? z.B. „Gehaltserhöhung Budget Quartal“"
              aria-label="Suchanfrage"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !query.trim()}>
              {loading ? <span className="spinner" /> : null}
              {loading ? "Suche …" : "Suchen"}
            </button>
          </div>

          <div className="row-wrap" style={{ justifyContent: "space-between" }}>
            <div className="suggest-row">
              <span className="label">{recent.length > 0 ? "Zuletzt:" : "Probier:"}</span>
              {suggestions.map((s) => (
                <button key={s} type="button" className="suggest-chip" onClick={() => runSearch(s)}>
                  {s}
                </button>
              ))}
            </div>

            <div className="segmented" role="group" aria-label="Ansicht">
              <button type="button" aria-pressed={view === "list"} onClick={() => setView("list")}>
                <Icon name="list" size={15} /> Liste
              </button>
              <button type="button" aria-pressed={view === "graph"} onClick={() => setView("graph")}>
                <Icon name="graph" size={15} /> Graph
              </button>
            </div>
          </div>
        </form>

        {error && (
          <div className="alert alert-error" role="alert">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        {view === "list" ? <ResultList results={results} query={submitted} loading={loading} /> : <GraphView />}
      </div>
    </Layout>
  );
}
