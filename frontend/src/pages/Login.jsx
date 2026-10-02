import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.hero}>
        <div style={styles.heroBadge}>Mini-Vektordatenbank mit RBAC</div>
        <h1 style={styles.heroTitle}>Dashboard</h1>
        <p style={styles.heroSub}>Jeder sieht nur, wofuer er berechtigt ist.</p>
      </div>

      <form onSubmit={handleSubmit} style={styles.card}>
        <h2 style={styles.cardTitle}>Anmelden</h2>

        <label style={styles.label}>
          Username
          <input
            style={styles.input}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
          />
        </label>

        <label style={styles.label}>
          Passwort
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <div style={styles.error}>{error}</div>}

        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Einloggen..." : "Einloggen"}
        </button>

        <div style={styles.hint}>Demo-User: anna / bernd / carla / david &mdash; Passwort: demo1234</div>
      </form>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "column",
    gap: 28,
    padding: 20,
  },
  hero: {
    textAlign: "center",
    background: "linear-gradient(135deg, #0f6e56 0%, #0a4536 100%)",
    color: "white",
    padding: "40px 48px",
    borderRadius: 18,
    maxWidth: 420,
    width: "100%",
  },
  heroBadge: {
    fontSize: 12,
    opacity: 0.8,
    letterSpacing: 0.4,
    marginBottom: 10,
    textTransform: "uppercase",
  },
  heroTitle: { fontSize: 28, margin: "0 0 6px", fontWeight: 600 },
  heroSub: { fontSize: 14, opacity: 0.9, margin: 0 },
  card: {
    background: "var(--card-bg)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    padding: 32,
    width: "100%",
    maxWidth: 420,
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  cardTitle: { margin: 0, fontSize: 18 },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    fontSize: 13,
    color: "var(--muted)",
  },
  input: {
    padding: "10px 12px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    fontSize: 15,
    color: "var(--ink)",
  },
  button: {
    padding: "12px 20px",
    border: "none",
    borderRadius: "var(--radius-sm)",
    background: "var(--teal)",
    color: "white",
    fontSize: 15,
    fontWeight: 500,
  },
  error: {
    background: "var(--mgmt-pale)",
    color: "var(--mgmt)",
    padding: "8px 12px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
  hint: { fontSize: 12, color: "var(--muted)", textAlign: "center" },
};
