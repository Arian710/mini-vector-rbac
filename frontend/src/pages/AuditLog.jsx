import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { auditLog } from "../api";
import Layout from "../components/Layout";
import Icon from "../components/Icon";

function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" });
}

export default function AuditLog() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState(null);
  const [user, setUser] = useState("all");
  const [filter, setFilter] = useState("");

  function load() {
    auditLog(token)
      .then((data) => {
        setError(null);
        setEntries(data);
      })
      .catch((err) => {
        if (!handleSessionExpiry(err)) setError(err.message);
      });
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const users = useMemo(() => [...new Set((entries || []).map((e) => e.username))].sort(), [entries]);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return (entries || []).filter(
      (e) => (user === "all" || e.username === user) && (!q || e.query.toLowerCase().includes(q))
    );
  }, [entries, user, filter]);

  const zeroHits = (entries || []).filter((e) => e.result_count === 0).length;

  return (
    <Layout title="Audit-Log">
      <div className="page page-wide">
        <div className="page-header">
          <h1>Audit-Log</h1>
          <p>Wer hat wann wonach gesucht – nur für deinen Mandanten sichtbar. Nachweis für Datenschutz und Compliance.</p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        {entries && (
          <div className="stat-grid">
            <div className="stat">
              <div className="v">{entries.length}</div>
              <div className="k">Suchanfragen gesamt</div>
            </div>
            <div className="stat">
              <div className="v">{users.length}</div>
              <div className="k">Aktive Nutzer</div>
            </div>
            <div className="stat">
              <div className="v">{zeroHits}</div>
              <div className="k">Ohne Treffer</div>
            </div>
          </div>
        )}

        <div className="row-wrap">
          <div className="input-wrap" style={{ flex: "1 1 240px" }}>
            <span className="input-icon">
              <Icon name="search" size={16} />
            </span>
            <input
              className="input"
              style={{ paddingLeft: 40, paddingRight: 12 }}
              placeholder="Suchanfragen filtern …"
              aria-label="Suchanfragen filtern"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          <select className="select" style={{ width: "auto" }} aria-label="Nach Nutzer filtern" value={user} onChange={(e) => setUser(e.target.value)}>
            <option value="all">Alle Nutzer</option>
            {users.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <button className="btn btn-ghost" onClick={load}>
            Aktualisieren
          </button>
        </div>

        {entries === null && !error && (
          <div className="stack-sm" aria-busy="true">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: 44 }} />
            ))}
          </div>
        )}

        {entries && visible.length === 0 && (
          <div className="empty">
            <span className="empty-icon">
              <Icon name="shield" size={22} />
            </span>
            <strong>{entries.length === 0 ? "Noch keine Suchanfragen protokolliert" : "Keine Einträge für diesen Filter"}</strong>
          </div>
        )}

        {visible.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Zeitpunkt</th>
                  <th>Nutzer</th>
                  <th>Suchanfrage</th>
                  <th className="num">Treffer</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((e, i) => (
                  <tr key={i}>
                    <td style={{ whiteSpace: "nowrap", color: "var(--muted)" }}>{formatDate(e.created_at)}</td>
                    <td>
                      <span className="pill pill-neutral">{e.username}</span>
                    </td>
                    <td style={{ overflowWrap: "anywhere" }}>{e.query}</td>
                    <td className="num">
                      <span className={`pill ${e.result_count === 0 ? "pill-restricted" : "pill-all"}`}>{e.result_count}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
