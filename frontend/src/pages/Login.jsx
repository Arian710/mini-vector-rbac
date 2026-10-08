import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Icon from "../components/Icon";

// Nur fuer die lokale Demo (seed_data.py) - kein Produktiv-Feature.
const DEMO_USERS = [
  { name: "anna", role: "support", tenant: "kanzlei-mueller" },
  { name: "bernd", role: "management", tenant: "kanzlei-mueller" },
  { name: "carla", role: "support", tenant: "steuerberatung-schmidt" },
  { name: "david", role: "management", tenant: "steuerberatung-schmidt" },
];

export default function Login() {
  const { token, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Anmelden · Mini-Vector RBAC";
  }, []);

  if (token) return <Navigate to="/" replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(name) {
    setUsername(name);
    setPassword("demo1234");
    setError(null);
  }

  return (
    <div className="auth">
      <section className="auth-hero">
        <div style={{ position: "relative", zIndex: 1 }}>
          <div className="row" style={{ marginBottom: 36 }}>
            <span className="brand-mark" style={{ background: "rgba(255,255,255,0.16)" }}>
              MV
            </span>
            <strong>Vector RBAC</strong>
          </div>
          <h1>Wissen finden. Nur das, was du sehen darfst.</h1>
          <p className="lead">
            Semantische Suche über alle Dokumente deines Teams, mit Rollen- und Mandantentrennung direkt in der
            Such-Engine.
          </p>
        </div>
        <ul className="auth-points">
          <li>
            <span className="dot">
              <Icon name="shield" size={15} />
            </span>
            Zugriffsrechte werden serverseitig erzwungen, nicht in der Oberfläche versteckt.
          </li>
          <li>
            <span className="dot">
              <Icon name="building" size={15} />
            </span>
            Strikte Mandantentrennung: Jede Kanzlei, Agentur oder Firma bleibt für sich.
          </li>
          <li>
            <span className="dot">
              <Icon name="clock" size={15} />
            </span>
            Jede Suche wird im Audit-Log nachvollziehbar protokolliert.
          </li>
        </ul>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div>
            <h2>Willkommen zurück</h2>
            <p className="card-sub" style={{ marginTop: 4 }}>
              Melde dich mit deinem Konto an.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="stack" noValidate>
            <label className="field">
              Benutzername
              <input
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                autoFocus
              />
            </label>

            <label className="field">
              Passwort
              <span className="input-wrap">
                <input
                  className="input"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="btn-icon"
                  onClick={() => setShowPw((s) => !s)}
                  aria-label={showPw ? "Passwort verbergen" : "Passwort anzeigen"}
                >
                  <Icon name={showPw ? "eyeOff" : "eye"} />
                </button>
              </span>
            </label>

            {error && (
              <div className="alert alert-error" role="alert">
                <Icon name="alert" size={16} /> {error}
              </div>
            )}

            <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={loading || !username || !password}>
              {loading && <span className="spinner" />}
              {loading ? "Anmelden …" : "Anmelden"}
            </button>
          </form>

          <div className="demo-users stack-sm">
            <span className="card-sub">Demo-Zugänge (Passwort: demo1234) – ein Klick füllt das Formular:</span>
            <div className="row-wrap">
              {DEMO_USERS.map((u) => (
                <button key={u.name} type="button" className="chip" onClick={() => fillDemo(u.name)}>
                  {u.name}
                  <small>
                    {u.role} · {u.tenant}
                  </small>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
