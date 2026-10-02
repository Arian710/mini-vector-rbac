import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { suggestDocument, saveDocument } from "../api";
import Layout from "../components/Layout";

const ROLE_LABELS = { all: "Alle Rollen", management: "Nur Management" };

export default function Upload() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const [file, setFile] = useState(null);
  const [customerLabel, setCustomerLabel] = useState("");
  const [suggestion, setSuggestion] = useState(null); // {text, suggested_role, reasons, chunk_count}
  const [chosenRole, setChosenRole] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveResult, setSaveResult] = useState(null); // {ids, chunk_count}

  async function handleAnalyze(event) {
    event.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    setSaveResult(null);
    try {
      const result = await suggestDocument(token, file);
      setSuggestion(result);
      setChosenRole(result.suggested_role);
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setLoading(true);
    setError(null);
    try {
      const result = await saveDocument(token, {
        text: suggestion.text,
        allowedRole: chosenRole,
        customerLabel,
        sourceDocumentName: file?.name,
      });
      setSaveResult(result);
      setSuggestion(null);
      setFile(null);
      setCustomerLabel("");
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      <div style={styles.wrapper}>
        <h2 style={styles.heading}>Dokument hochladen</h2>
        <p style={styles.sub}>PDF, DOCX oder TXT &mdash; Text wird extrahiert, eine Rolle vorgeschlagen, du bestaetigst.</p>

        <form onSubmit={handleAnalyze} style={styles.card}>
          <label style={styles.label}>
            Datei
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files[0] || null)}
              style={styles.fileInput}
            />
          </label>

          <label style={styles.label}>
            Kunde / Projekt <span style={styles.optional}>(optional, nur Organisation &mdash; keine Sicherheitsgrenze)</span>
            <input
              type="text"
              placeholder="z.B. Mueller GmbH"
              value={customerLabel}
              onChange={(e) => setCustomerLabel(e.target.value)}
              style={styles.textInput}
            />
          </label>

          <button type="submit" style={styles.button} disabled={!file || loading}>
            {loading ? "Analysiere..." : "Vorschlag abrufen"}
          </button>
        </form>

        {error && <div style={styles.error}>{error}</div>}

        {saveResult && (
          <div style={styles.success}>
            {saveResult.chunk_count > 1
              ? `Dokument in ${saveResult.chunk_count} Abschnitte gespeichert und sofort durchsuchbar (IDs ${saveResult.ids[0]}–${saveResult.ids[saveResult.ids.length - 1]}, Rolle: ${ROLE_LABELS[saveResult.allowed_role]}).`
              : `Dokument #${saveResult.ids[0]} gespeichert und sofort durchsuchbar (Rolle: ${ROLE_LABELS[saveResult.allowed_role]}).`}
          </div>
        )}

        {suggestion && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Extrahierter Text</h3>
            <div style={styles.textPreview}>{suggestion.text}</div>

            {suggestion.ocr_used && (
              <div style={styles.notice}>
                PDF hatte keine Text-Ebene (vermutlich gescannt/fotografiert) &mdash; Text per Azure-OCR erkannt.
                Bei schlechter Scan-Qualitaet kann die Erkennung Fehler enthalten, kurz gegenpruefen lohnt sich.
              </div>
            )}

            {suggestion.chunk_count > 1 && (
              <div style={styles.notice}>
                Dokument ist lang &mdash; wird beim Speichern automatisch in {suggestion.chunk_count} durchsuchbare
                Abschnitte aufgeteilt (jeder einzeln eingebettet), statt als ein einziges, zu großes Dokument.
              </div>
            )}

            <div style={styles.suggestionBox}>
              <div style={styles.suggestionHeader}>
                Vorschlag:{" "}
                <span
                  style={{
                    ...styles.pill,
                    background: suggestion.suggested_role === "management" ? "var(--mgmt-pale)" : "var(--support-pale)",
                    color: suggestion.suggested_role === "management" ? "var(--mgmt)" : "var(--support)",
                  }}
                >
                  {ROLE_LABELS[suggestion.suggested_role]}
                </span>
              </div>
              <ul style={styles.reasons}>
                {suggestion.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>

            <label style={styles.label}>
              Rolle (vor dem Speichern pruefen/aendern)
              <div style={styles.toggle}>
                <button
                  type="button"
                  onClick={() => setChosenRole("all")}
                  style={chosenRole === "all" ? styles.toggleBtnActive : styles.toggleBtn}
                >
                  Alle Rollen
                </button>
                <button
                  type="button"
                  onClick={() => setChosenRole("management")}
                  style={chosenRole === "management" ? styles.toggleBtnActive : styles.toggleBtn}
                >
                  Nur Management
                </button>
              </div>
            </label>

            <button type="button" onClick={handleSave} style={styles.button} disabled={loading}>
              {loading ? "Speichere..." : "Dokument speichern"}
            </button>
          </div>
        )}
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
  fileInput: { fontSize: 14 },
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
  textPreview: {
    background: "var(--bg)",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    padding: 12,
    fontSize: 13,
    color: "var(--ink)",
    maxHeight: 160,
    overflowY: "auto",
    whiteSpace: "pre-wrap",
  },
  suggestionBox: { display: "flex", flexDirection: "column", gap: 6 },
  suggestionHeader: { fontSize: 14 },
  pill: {
    fontSize: 12,
    fontWeight: 600,
    padding: "4px 10px",
    borderRadius: 999,
  },
  reasons: { margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--muted)" },
  toggle: {
    display: "flex",
    background: "var(--bg)",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius-sm)",
    padding: 3,
    width: "fit-content",
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
  notice: {
    background: "var(--bg)",
    border: "1px solid var(--rule)",
    color: "var(--muted)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 12,
  },
  success: {
    background: "var(--support-pale)",
    color: "var(--support)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
};
