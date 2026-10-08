import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { listRoles, createRole, updateRole, deleteRole } from "../api";
import { ROLE_TEMPLATES } from "../roleTemplates";
import Layout from "../components/Layout";
import Icon from "../components/Icon";
import ConfirmDialog from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";

export default function Roles() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const toast = useToast();

  const [roles, setRoles] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const [toDelete, setToDelete] = useState(null);

  const [showTemplates, setShowTemplates] = useState(false);
  const [industryIndex, setIndustryIndex] = useState(0);
  const [checkedRoles, setCheckedRoles] = useState(() => new Set(ROLE_TEMPLATES[0].roles.map((r) => r.name)));

  function selectIndustry(index) {
    setIndustryIndex(index);
    setCheckedRoles(new Set(ROLE_TEMPLATES[index].roles.map((r) => r.name)));
  }

  function toggleTemplateRole(name) {
    setCheckedRoles((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
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
    toast.success(
      skipped > 0
        ? `${created} Rolle(n) angelegt, ${skipped} übersprungen (existierten vermutlich schon).`
        : `${created} Rolle(n) angelegt.`
    );
    await refresh();
    setLoading(false);
  }

  async function handleCreate(event) {
    event.preventDefault();
    if (!newName.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createRole(token, { name: newName.trim(), description: newDescription.trim() });
      toast.success(`Rolle „${newName.trim()}“ angelegt.`);
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

  async function handleSaveEdit(roleId) {
    setLoading(true);
    setError(null);
    try {
      await updateRole(token, roleId, { name: editName.trim(), description: editDescription.trim() });
      setEditingId(null);
      toast.success("Rolle aktualisiert.");
      await refresh();
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    const role = toDelete;
    setLoading(true);
    setError(null);
    try {
      await deleteRole(token, role.id);
      toast.success(`Rolle „${role.name}“ gelöscht.`);
      await refresh();
    } catch (err) {
      if (!handleSessionExpiry(err)) toast.error(err.message);
    } finally {
      setLoading(false);
      setToDelete(null);
    }
  }

  return (
    <Layout title="Rollen">
      <div className="page" style={{ maxWidth: 760 }}>
        <div className="page-header">
          <h1>Rollen verwalten</h1>
          <p>
            Lege eigene Rollen an und beschreibe sie – die Beschreibung nutzt der Upload, um automatisch die passende Rolle
            vorzuschlagen (Keywords + KI-Ähnlichkeit).
          </p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        <section className="card stack">
          <div className="row">
            <div>
              <h2 className="card-title">Bestehende Rollen</h2>
              <div className="card-sub">{roles ? `${roles.length} Rollen` : "Lade …"}</div>
            </div>
          </div>

          {roles === null && (
            <div className="stack-sm" aria-busy="true">
              {[0, 1, 2].map((i) => (
                <div key={i} className="skeleton" style={{ height: 58 }} />
              ))}
            </div>
          )}
          {roles && roles.length === 0 && (
            <div className="empty">
              <strong>Noch keine eigenen Rollen</strong>
              <span>Starte mit einer Branchenvorlage oder lege unten eine Rolle an.</span>
            </div>
          )}

          <div className="stack-sm">
            {roles?.map((role) => (
              <div key={role.id} className="role-row">
                {editingId === role.id ? (
                  <form
                    className="stack-sm"
                    style={{ width: "100%" }}
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSaveEdit(role.id);
                    }}
                  >
                    <input
                      className="input"
                      aria-label="Rollenname"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      autoFocus
                    />
                    <input
                      className="input"
                      aria-label="Beschreibung"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="Beschreibung"
                    />
                    <div className="row-wrap">
                      <button type="submit" className="btn btn-primary btn-sm" disabled={loading || !editName.trim()}>
                        Speichern
                      </button>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}>
                        Abbrechen
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div className="row-wrap" style={{ gap: 8 }}>
                        <span className="name">{role.name}</span>
                        {role.is_system && (
                          <span className="pill pill-neutral" style={{ fontSize: 10 }}>
                            <Icon name="lock" size={11} /> System
                          </span>
                        )}
                      </div>
                      {role.description && <div className="desc">{role.description}</div>}
                    </div>
                    {!role.is_system && (
                      <div className="row-wrap" style={{ flexShrink: 0 }}>
                        <button className="btn btn-ghost btn-sm" onClick={() => startEdit(role)}>
                          <Icon name="edit" size={14} /> Bearbeiten
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => setToDelete(role)}>
                          <Icon name="trash" size={14} /> Löschen
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </section>

        <form onSubmit={handleCreate} className="card stack">
          <h2 className="card-title">Neue Rolle anlegen</h2>
          <label className="field">
            Name
            <input
              className="input"
              placeholder="z.B. Buchhaltung"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </label>
          <label className="field">
            <span>
              Beschreibung <span className="hint">(wird für den Rollenvorschlag genutzt)</span>
            </span>
            <input
              className="input"
              placeholder="z.B. Rechnungen, Mahnwesen, Kontoauszüge, Zahlungsverkehr"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
            />
          </label>
          <button type="submit" className="btn btn-primary" style={{ alignSelf: "flex-start" }} disabled={!newName.trim() || loading}>
            <Icon name="plus" size={16} /> Rolle anlegen
          </button>
        </form>

        <section className="card stack">
          <button
            type="button"
            className="row"
            style={{ background: "none", border: "none", padding: 0, textAlign: "left", width: "100%" }}
            onClick={() => setShowTemplates((s) => !s)}
            aria-expanded={showTemplates}
          >
            <span style={{ flex: 1 }}>
              <span className="card-title" style={{ display: "block" }}>
                Branchenvorlage als Starthilfe
              </span>
              <span className="card-sub">Vorgeschlagene Rollen für typische Teams – übernehmen, anpassen oder ignorieren.</span>
            </span>
            <span className="btn-ghost btn btn-sm">{showTemplates ? "Einklappen" : "Öffnen"}</span>
          </button>

          {showTemplates && (
            <>
              <label className="field">
                Branche
                <select className="select" value={industryIndex} onChange={(e) => selectIndustry(Number(e.target.value))}>
                  {ROLE_TEMPLATES.map((group, i) => (
                    <option key={group.industry} value={i}>
                      {group.industry}
                    </option>
                  ))}
                </select>
              </label>

              <div className="stack-sm">
                {ROLE_TEMPLATES[industryIndex].roles.map((role) => (
                  <label key={role.name} className="template-row">
                    <input type="checkbox" checked={checkedRoles.has(role.name)} onChange={() => toggleTemplateRole(role.name)} />
                    <div>
                      <div className="name" style={{ fontWeight: 600, fontSize: 14 }}>
                        {role.name}
                      </div>
                      <div className="desc card-sub">{role.description}</div>
                    </div>
                  </label>
                ))}
              </div>

              <button
                type="button"
                onClick={handleApplyTemplates}
                className="btn btn-primary"
                style={{ alignSelf: "flex-start" }}
                disabled={loading || checkedRoles.size === 0}
              >
                {loading && <span className="spinner" />}
                {loading ? "Übernehme …" : `${checkedRoles.size} ausgewählte übernehmen`}
              </button>
            </>
          )}
        </section>
      </div>

      {toDelete && (
        <ConfirmDialog
          title={`Rolle „${toDelete.name}“ löschen?`}
          message="Die Rolle wird entfernt. Falls noch Dokumente oder Nutzer diese Rolle verwenden, lehnt der Server das Löschen ab."
          confirmLabel="Endgültig löschen"
          busy={loading}
          onConfirm={handleDelete}
          onCancel={() => setToDelete(null)}
        />
      )}
    </Layout>
  );
}
