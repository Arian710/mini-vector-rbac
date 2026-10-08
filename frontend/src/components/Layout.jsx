import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../hooks/useTheme";
import Icon from "./Icon";

function initials(username) {
  return (username || "?").slice(0, 2).toUpperCase();
}

const THEMES = [
  { mode: "light", label: "Hell", icon: "sun" },
  { mode: "dark", label: "Dunkel", icon: "moon" },
  { mode: "system", label: "System", icon: "globe" },
];

export default function Layout({ title, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { mode, setMode } = useTheme();
  const [navOpen, setNavOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const isManagement = user?.role === "management";

  useEffect(() => {
    if (title) document.title = `${title} · Mini-Vector RBAC`;
  }, [title]);

  useEffect(() => {
    if (!menuOpen) return;
    const onDown = (e) => menuRef.current && !menuRef.current.contains(e.target) && setMenuOpen(false);
    const onKey = (e) => e.key === "Escape" && setMenuOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="shell">
      <aside className={`sidebar ${navOpen ? "open" : ""}`} aria-label="Hauptnavigation">
        <div className="brand">
          <span className="brand-mark">MV</span>
          <div>
            <div className="brand-name">Vector RBAC</div>
            <div className="brand-sub">Wissensdatenbank</div>
          </div>
        </div>

        <nav className="nav" onClick={() => setNavOpen(false)}>
          <div className="nav-label">Arbeiten</div>
          <NavLink to="/" end>
            <Icon name="search" /> Suche
          </NavLink>
          {isManagement && (
            <NavLink to="/upload">
              <Icon name="upload" /> Upload
            </NavLink>
          )}
          {isManagement && (
            <>
              <div className="nav-label" style={{ paddingTop: 18 }}>
                Verwalten
              </div>
              <NavLink to="/roles">
                <Icon name="tag" /> Rollen
              </NavLink>
              <NavLink to="/audit">
                <Icon name="shield" /> Audit-Log
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-foot">
          <span className="region-badge">
            <Icon name="lock" size={13} /> Serverseitig erzwungenes RBAC
          </span>
          <span>Jeder sieht nur, wofür er berechtigt ist.</span>
        </div>
      </aside>
      <div className={`scrim ${navOpen ? "open" : ""}`} onClick={() => setNavOpen(false)} />

      <div className="main">
        <header className="topbar">
          <button
            className="btn-icon menu-toggle"
            onClick={() => setNavOpen((o) => !o)}
            aria-label="Navigation öffnen"
            aria-expanded={navOpen}
          >
            <Icon name="menu" size={20} />
          </button>
          <span className="tenant-chip" title="Dein Mandant">
            <Icon name="building" size={14} /> {user?.tenant_id}
          </span>
          <span className="spacer" />

          <div className="user-menu" ref={menuRef}>
            <button
              className="user-btn"
              onClick={() => setMenuOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <span className="avatar">{initials(user?.sub)}</span>
              <span className="hide-mobile" style={{ fontSize: 14, fontWeight: 500 }}>
                {user?.sub}
              </span>
            </button>
            {menuOpen && (
              <div className="popover" role="menu">
                <div className="popover-head">
                  <strong style={{ fontSize: 14 }}>{user?.sub}</strong>
                  <span className="row-wrap">
                    <span className={`pill ${isManagement ? "pill-restricted" : "pill-all"}`}>{user?.role}</span>
                    <span className="muted" style={{ fontSize: 12 }}>
                      {user?.tenant_id}
                    </span>
                  </span>
                </div>
                <div className="nav-label" style={{ padding: "4px 10px" }}>
                  Darstellung
                </div>
                {THEMES.map((t) => (
                  <button
                    key={t.mode}
                    className="item"
                    role="menuitemradio"
                    aria-checked={mode === t.mode}
                    onClick={() => setMode(t.mode)}
                  >
                    <Icon name={t.icon} size={16} />
                    <span style={{ flex: 1 }}>{t.label}</span>
                    {mode === t.mode && <Icon name="check" size={16} />}
                  </button>
                ))}
                <div style={{ borderTop: "1px solid var(--rule)", margin: "6px 0" }} />
                <button className="item" role="menuitem" onClick={handleLogout}>
                  <Icon name="logout" size={16} /> Abmelden
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="content">{children}</main>
      </div>
    </div>
  );
}
