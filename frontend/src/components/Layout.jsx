import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function initials(username) {
  return username.slice(0, 2).toUpperCase();
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const roleIsManagement = user?.role === "management";

  function navStyle(path) {
    return location.pathname === path ? styles.navItemActive : styles.navItem;
  }

  return (
    <div style={styles.shell}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <span style={styles.logoMark}>MV</span>
          <span style={styles.logoText}>RBAC</span>
        </div>
        <nav style={styles.nav}>
          <Link to="/" style={navStyle("/")}>
            <span>🔎</span> Dashboard
          </Link>
          {roleIsManagement && (
            <Link to="/upload" style={navStyle("/upload")}>
              <span>📤</span> Upload
            </Link>
          )}
        </nav>
      </aside>

      <div style={styles.main}>
        <header style={styles.topbar}>
          <div style={styles.tenant}>{user?.tenant_id}</div>
          <div style={styles.userBlock}>
            <span
              style={{
                ...styles.pill,
                background: roleIsManagement ? "var(--mgmt-pale)" : "var(--support-pale)",
                color: roleIsManagement ? "var(--mgmt)" : "var(--support)",
              }}
            >
              {user?.role}
            </span>
            <span style={styles.avatar}>{initials(user?.sub || "?")}</span>
            <span style={styles.username}>{user?.sub}</span>
            <button style={styles.logoutButton} onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <main style={styles.content}>{children}</main>
      </div>
    </div>
  );
}

const styles = {
  shell: { display: "flex", minHeight: "100vh" },
  sidebar: {
    width: 220,
    background: "var(--card-bg)",
    borderRight: "1px solid var(--rule)",
    padding: "24px 16px",
    display: "flex",
    flexDirection: "column",
    gap: 28,
  },
  logo: { display: "flex", alignItems: "center", gap: 10, padding: "0 8px" },
  logoMark: {
    width: 32,
    height: 32,
    borderRadius: 9,
    background: "var(--teal)",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 12,
    fontWeight: 700,
  },
  logoText: { fontWeight: 600, fontSize: 15 },
  nav: { display: "flex", flexDirection: "column", gap: 4 },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 12px",
    borderRadius: "var(--radius-sm)",
    color: "var(--muted)",
    fontSize: 14,
    fontWeight: 500,
    textDecoration: "none",
  },
  navItemActive: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 12px",
    borderRadius: "var(--radius-sm)",
    background: "var(--teal-pale)",
    color: "var(--teal-deep)",
    fontSize: 14,
    fontWeight: 500,
    textDecoration: "none",
  },
  main: { flex: 1, display: "flex", flexDirection: "column" },
  topbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px 28px",
    borderBottom: "1px solid var(--rule)",
    background: "var(--card-bg)",
  },
  tenant: { fontSize: 13, color: "var(--muted)" },
  userBlock: { display: "flex", alignItems: "center", gap: 10 },
  pill: {
    fontSize: 12,
    fontWeight: 600,
    padding: "4px 10px",
    borderRadius: 999,
    textTransform: "capitalize",
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    background: "var(--teal-deep)",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 11,
    fontWeight: 700,
  },
  username: { fontSize: 14 },
  logoutButton: {
    border: "1px solid var(--rule)",
    background: "transparent",
    borderRadius: "var(--radius-sm)",
    padding: "6px 12px",
    fontSize: 13,
    color: "var(--ink)",
  },
  content: { flex: 1, padding: 28, display: "flex", flexDirection: "column", gap: 20 },
};
