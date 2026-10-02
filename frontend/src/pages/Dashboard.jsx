import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { search as apiSearch } from "../api";
import Layout from "../components/Layout";
import ResultList from "../components/ResultList";
import GraphView from "../components/GraphView";

export default function Dashboard() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [view, setView] = useState("list"); // "list" | "graph"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runSearch(event) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiSearch(token, query);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <form onSubmit={runSearch} style={styles.searchRow}>
        <input
          style={styles.searchInput}
          placeholder="Suche z.B. 'Gehaltserhoehung Budget Quartal'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" style={styles.searchButton} disabled={loading}>
          {loading ? "Suche laeuft..." : "Suchen"}
        </button>

        <div style={styles.toggle}>
          <button
            type="button"
            onClick={() => setView("list")}
            style={view === "list" ? styles.toggleBtnActive : styles.toggleBtn}
          >
            Liste
          </button>
          <button
            type="button"
            onClick={() => setView("graph")}
            style={view === "graph" ? styles.toggleBtnActive : styles.toggleBtn}
          >
            Graph
          </button>
        </div>
      </form>

      {error && <div style={styles.error}>{error}</div>}

      {view === "list" ? <ResultList results={results} /> : <GraphView />}
    </Layout>
  );
}

const styles = {
  searchRow: { display: "flex", gap: 10, alignItems: "center" },
  searchInput: {
    flex: 1,
    padding: "11px 14px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    fontSize: 15,
  },
  searchButton: {
    padding: "11px 22px",
    border: "none",
    borderRadius: "var(--radius-sm)",
    background: "var(--teal)",
    color: "white",
    fontSize: 15,
    fontWeight: 500,
  },
  toggle: {
    display: "flex",
    background: "var(--bg)",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    padding: 3,
  },
  toggleBtn: {
    border: "none",
    background: "transparent",
    padding: "8px 14px",
    borderRadius: 8,
    fontSize: 13,
    color: "var(--muted)",
  },
  toggleBtnActive: {
    border: "none",
    background: "var(--card-bg)",
    boxShadow: "var(--shadow)",
    padding: "8px 14px",
    borderRadius: 8,
    fontSize: 13,
    color: "var(--ink)",
    fontWeight: 600,
  },
  error: {
    background: "var(--mgmt-pale)",
    color: "var(--mgmt)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
};
