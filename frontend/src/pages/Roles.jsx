import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { listRoles, createRole, updateRole, deleteRole } from "../api";
import { ROLE_TEMPLATES } from "../roleTemplates";
import Layout from "../components/Layout";

export default function Roles() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();

  const [roles, setRoles] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const [industryIndex, setIndustryIndex] = useState(0);
  const [checkedRoles, setCheckedRoles] = useState(() => new Set(ROLE_TEMPLATES[0].roles.map((r) => r.name)));
  const [templateStatus, setTemplateStatus] = useState(null);

  function selectIndustry(index) {
    setIndustryIndex(index);
    setCheckedRoles(new Set(ROLE_TEMPLATES[index].roles.map((r) => r.name)));
    setTemplateStatus(null);
  }

  function toggleTemplateRole(name) {
    setCheckedRoles((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  async function handleApplyTemplates() {
    const toCreate = ROLE_TEMPLATES[industryIndex].roles.filter((r) => checkedRoles.has(r.name));
    if (toCreate.length === 0) return;
    setLoading(true);
    setError(null);
    let created = 0;
    let skipped = 0;
    for (const role of toCreate) {
      try {
        await createRole(token, { name: role.name, description: role.description });
        created++;
      } catch (err) {
        if (handleSessionExpiry(err)) return;
        skipped++; // meist Duplikat (Rolle existiert schon) - naechste trotzdem versuchen
      }
    }
    setTemplateStatus(
      skipped > 0
        ? `${created} Rolle(n) angelegt, ${skipped} übersprungen (existierten vermutlich schon).`
        : `${created} Rolle(n) angelegt.`
    );
    await refresh();
    setLoading(false);
  }

  async function refresh() {
    try {
      setRoles(await listRoles(token));
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    if (!newName.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createRole(token, { name: newName.trim(), description: newDescription.trim() });
      setNewName("");
      setNewDescription("");
      await refresh();
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function startEdit(role) {
    setEditingId(role.id);
    setEditName(role.name);
    setEditDescription(role.description || "");
  }

  function cancelEdit() {
    setEditingId(null);
  }

  async function handleSaveEdit(roleId) {
    setLoading(true);
    setError(null);
    try {
      await updateRole(token, roleId, { name: editName.trim(), description: editDescription.trim() });
      setEditingId(null);
      await refresh();
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(role) {
    setLoading(true);
    setError(null);
    try {
      await deleteRole(token, role.id);
      await refresh();
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div style={styles.wrapper}>
        <h2 style={styles.heading}>Rollen verwalten</h2>
        <p style={styles.sub}>
          Eigene Rollen anlegen und beschreiben &mdash; die Beschreibung wird beim Dokumenten-Upload automatisch
          genutzt, um die passende Rolle vorzuschlagen (Keywords + KI-Ähnlichkeit).
        </p>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Branchenvorlage als Starthilfe</h3>
          <label style={styles.label}>
            Branche
            <select
              value={industryIndex}
              onChange={(e) => selectIndustry(Number(e.target.value))}
              style={styles.textInput}
            >
              {ROLE_TEMPLATES.map((group, i) => (
                <option key={group.industry} value={i}>
                  {group.industry}
                </option>
              ))}
            </select>
          </label>

          <div style={styles.templateList}>
            {ROLE_TEMPLATES[industryIndex].roles.map((role) => (
              <label key={role.name} style={styles.templateRow}>
                <input
                  type="checkbox"
                  checked={checkedRoles.has(role.name)}
                  onChange={() => toggleTemplateRole(role.name)}
                />
                <div>
                  <div style={styles.roleName}>{role.name}</div>
                  <div style={styles.roleDescription}>{role.description}</div>
                </div>
              </label>
            ))}
          </div>

          <button
            type="button"
            onClick={handleApplyTemplates}
            style={styles.button}
            disabled={loading || checkedRoles.size === 0}
          >
            {loading ? "Übernehme..." : "Ausgewählte übernehmen"}
          </button>

          {templateStatus && <div style={styles.success}>{templateStatus}</div>}
        </div>

        <form onSubmit={handleCreate} style={styles.card}>
          <h3 style={styles.cardTitle}>Neue Rolle anlegen</h3>
          <label style={styles.label}>
            Name
            <input
              type="text"
              placeholder="z.B. Buchhaltung"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              style={styles.textInput}
            />
          </label>
          <label style={styles.label}>
            Beschreibung <span style={styles.optional}>(wird für den Rollenvorschlag genutzt)</span>
            <input
              type="text"
              placeholder="z.B. Rechnungen, Mahnwesen, Kontoauszüge, Zahlungsverkehr"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              style={styles.textInput}
            />
          </label>
          <button type="submit" style={styles.button} disabled={!newName.trim() || loading}>
            {loading ? "Speichere..." : "Rolle anlegen"}
          </button>
        </form>

        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Bestehende Rollen</h3>
          {roles === null && <div style={styles.muted}>Lade...</div>}
          {roles && roles.length === 0 && <div style={styles.muted}>Noch keine Rollen.</div>}
          <div style={styles.list}>
            {roles?.map((role) => (
              <div key={role.id} style={styles.roleRow}>
                {editingId === role.id ? (
                  <div style={styles.editForm}>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      style={styles.textInput}
                    />
                    <input
                      type="text"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="Beschreibung"
                      style={styles.textInput}
                    />
                    <div style={styles.rowActions}>
                      <button
                        type="button"
                        onClick={() => handleSaveEdit(role.id)}
                        style={styles.smallButton}
                        disabled={loading}
                      >
                        Speichern
                      </button>
                      <button type="button" onClick={cancelEdit} style={styles.smallButtonGhost}>
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div style={styles.roleInfo}>
                      <div style={styles.roleNameRow}>
                        <span style={styles.roleName}>{role.name}</span>
                        {role.is_system && <span style={styles.systemBadge}>System</span>}
                      </div>
                      {role.description && <div style={styles.roleDescription}>{role.description}</div>}
                    </div>
                    {!role.is_system && (
                      <div style={styles.rowActions}>
                        <button type="button" onClick={() => startEdit(role)} style={styles.smallButtonGhost}>
                          Bearbeiten
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(role)}
                          style={styles.smallButtonDanger}
                          disabled={loading}
                        >
                          Löschen
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}

const styles = {
  wrapper: { display: "flex", flexDirection: "column", gap: 16, maxWidth: 640 },
  heading: { margin: 0, fontSize: 20 },
  sub: { margin: 0, color: "var(--muted)", fontSize: 13 },
  card: {
    background: "var(--card-bg)",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    padding: 20,
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },
  cardTitle: { margin: 0, fontSize: 14, color: "var(--muted)" },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 13, color: "var(--muted)" },
  optional: { fontWeight: 400, fontStyle: "italic" },
  textInput: {
    padding: "10px 12px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    fontSize: 14,
    color: "var(--ink)",
  },
  button: {
    padding: "11px 20px",
    border: "none",
    borderRadius: "var(--radius-sm)",
    background: "var(--teal)",
    color: "white",
    fontSize: 14,
    fontWeight: 500,
    alignSelf: "flex-start",
  },
  smallButton: {
    padding: "7px 14px",
    border: "none",
    borderRadius: "var(--radius-sm)",
    background: "var(--teal)",
    color: "white",
    fontSize: 13,
  },
  smallButtonGhost: {
    padding: "7px 14px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    background: "transparent",
    color: "var(--ink)",
    fontSize: 13,
  },
  smallButtonDanger: {
    padding: "7px 14px",
    border: "1px solid var(--mgmt)",
    borderRadius: "var(--radius-sm)",
    background: "transparent",
    color: "var(--mgmt)",
    fontSize: 13,
  },
  list: { display: "flex", flexDirection: "column", gap: 10 },
  roleRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: "10px 14px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
  },
  roleInfo: { display: "flex", flexDirection: "column", gap: 3, minWidth: 0 },
  roleNameRow: { display: "flex", alignItems: "center", gap: 8 },
  roleName: { fontSize: 14, fontWeight: 600 },
  roleDescription: { fontSize: 12, color: "var(--muted)" },
  systemBadge: {
    fontSize: 10,
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 999,
    background: "var(--bg)",
    color: "var(--muted)",
    border: "1px solid var(--rule)",
  },
  rowActions: { display: "flex", gap: 8, flexShrink: 0 },
  editForm: { display: "flex", flexDirection: "column", gap: 8, width: "100%" },
  muted: { color: "var(--muted)", fontSize: 13, fontStyle: "italic" },
  templateList: { display: "flex", flexDirection: "column", gap: 8 },
  templateRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
    padding: "8px 10px",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    cursor: "pointer",
  },
  error: {
    background: "var(--mgmt-pale)",
    color: "var(--mgmt)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
  success: {
    background: "var(--support-pale)",
    color: "var(--support)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
};
