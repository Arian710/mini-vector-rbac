import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { suggestDocument, saveDocument, listRoles } from "../api";
import Layout from "../components/Layout";
import Icon from "../components/Icon";
import { useToast } from "../components/Toast";

const ACCEPTED = [".pdf", ".docx", ".txt"];
const MAX_MB = 20;

function formatSize(bytes) {
  return bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function Stepper({ step }) {
  const steps = ["Datei", "Prüfen", "Gespeichert"];
  return (
    <ol className="stepper" style={{ listStyle: "none", padding: 0, margin: 0 }} aria-label="Fortschritt">
      {steps.map((label, i) => (
        <li key={label} className="row" style={{ gap: 10 }}>
          <span className={`step ${i === step ? "active" : i < step ? "done" : ""}`} aria-current={i === step ? "step" : undefined}>
            <span className="step-n">{i < step ? <Icon name="check" size={13} strokeWidth={2.6} /> : i + 1}</span>
            {label}
          </span>
          {i < steps.length - 1 && <span className="step-line" />}
        </li>
      ))}
    </ol>
  );
}

export default function Upload() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const toast = useToast();
  const inputRef = useRef(null);
  const [roles, setRoles] = useState([]);
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [customerLabel, setCustomerLabel] = useState("");
  const [suggestion, setSuggestion] = useState(null); // {text, suggested_role, reasons, chunk_count, ocr_used}
  const [chosenRole, setChosenRole] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveResult, setSaveResult] = useState(null); // {ids, chunk_count, allowed_role}

  useEffect(() => {
    listRoles(token)
      .then(setRoles)
      .catch((err) => {
        if (!handleSessionExpiry(err)) setError(err.message);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const step = saveResult ? 2 : suggestion ? 1 : 0;

  function pickFile(f) {
    if (!f) return;
    const ext = "." + f.name.split(".").pop().toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Dateityp „${ext}“ wird nicht unterstützt. Erlaubt: PDF, DOCX, TXT.`);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`Datei ist zu groß (max. ${MAX_MB} MB).`);
      return;
    }
    setError(null);
    setSaveResult(null);
    setSuggestion(null);
    setFile(f);
  }

  function reset() {
    setFile(null);
    setSuggestion(null);
    setSaveResult(null);
    setCustomerLabel("");
    setError(null);
  }

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
      toast.success("Dokument gespeichert und durchsuchbar.");
    } catch (err) {
      if (!handleSessionExpiry(err)) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const roleNames = roles.length > 0 ? roles.map((r) => r.name) : ["all", "management"];

  return (
    <Layout title="Upload">
      <div className="page" style={{ maxWidth: 720 }}>
        <div className="page-header">
          <h1>Dokument hochladen</h1>
          <p>PDF, DOCX oder TXT. Der Text wird extrahiert, eine Rolle vorgeschlagen – du prüfst und bestätigst.</p>
        </div>

        <Stepper step={step} />

        {error && (
          <div className="alert alert-error" role="alert">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        {saveResult && (
          <div className="card stack" role="status">
            <div className="row" style={{ gap: 12 }}>
              <span className="empty-icon" style={{ background: "var(--support-pale)", color: "var(--support)", width: 44, height: 44, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Icon name="checkCircle" size={22} />
              </span>
              <div>
                <strong>Gespeichert</strong>
                <div className="card-sub">
                  {saveResult.chunk_count > 1
                    ? `In ${saveResult.chunk_count} Abschnitte aufgeteilt`
                    : "Als ein Abschnitt gespeichert"}{" "}
                  · Rolle:{" "}
                  <span className={`pill ${saveResult.allowed_role === "all" ? "pill-all" : "pill-restricted"}`}>
                    {saveResult.allowed_role}
                  </span>
                </div>
              </div>
            </div>
            <div className="row-wrap">
              <button className="btn btn-primary" onClick={reset}>
                <Icon name="plus" size={16} /> Weiteres Dokument
              </button>
              <Link to="/" className="btn btn-ghost" style={{ textDecoration: "none" }}>
                <Icon name="search" size={16} /> Zur Suche
              </Link>
            </div>
          </div>
        )}

        {!saveResult && !suggestion && (
          <form onSubmit={handleAnalyze} className="card stack">
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED.join(",")}
              className="sr-only"
              tabIndex={-1}
              onChange={(e) => pickFile(e.target.files[0])}
            />

            {!file ? (
              <div
                className={`dropzone ${drag ? "drag" : ""}`}
                role="button"
                tabIndex={0}
                aria-label="Datei auswählen oder hierher ziehen"
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), inputRef.current?.click())}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDrag(true);
                }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDrag(false);
                  pickFile(e.dataTransfer.files[0]);
                }}
              >
                <span className="dz-icon">
                  <Icon name="upload" size={22} />
                </span>
                <strong>Datei hierher ziehen</strong>
                <span className="card-sub">oder klicken zum Auswählen · PDF, DOCX, TXT · max. {MAX_MB} MB</span>
              </div>
            ) : (
              <div className="file-chip">
                <Icon name="file" size={22} />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div className="name">{file.name}</div>
                  <div className="card-sub">{formatSize(file.size)}</div>
                </div>
                <button type="button" className="btn-icon" onClick={() => setFile(null)} aria-label="Datei entfernen">
                  <Icon name="x" />
                </button>
              </div>
            )}

            <label className="field">
              <span>
                Kunde / Projekt <span className="hint">(optional – nur Organisation, keine Sicherheitsgrenze)</span>
              </span>
              <input
                className="input"
                type="text"
                placeholder="z.B. Müller GmbH"
                value={customerLabel}
                onChange={(e) => setCustomerLabel(e.target.value)}
              />
            </label>

            <button type="submit" className="btn btn-primary btn-lg" style={{ alignSelf: "flex-start" }} disabled={!file || loading}>
              {loading ? <span className="spinner" /> : <Icon name="sparkles" size={17} />}
              {loading ? "Analysiere …" : "Rollenvorschlag abrufen"}
            </button>
          </form>
        )}

        {suggestion && (
          <div className="card stack">
            <div className="row">
              <strong className="card-title">Extrahierter Text</strong>
              <span className="spacer" />
              <span className="card-sub row" style={{ gap: 6 }}>
                <Icon name="file" size={14} /> {file?.name}
              </span>
            </div>
            <div className="preview">{suggestion.text}</div>

            {suggestion.ocr_used && (
              <div className="alert alert-info">
                <Icon name="alert" size={16} /> PDF hatte keine Text-Ebene (vermutlich gescannt) – Text per Azure-OCR erkannt.
                Bei schlechter Scan-Qualität kann die Erkennung Fehler enthalten, kurz gegenprüfen lohnt sich.
              </div>
            )}
            {suggestion.chunk_count > 1 && (
              <div className="alert alert-info">
                <Icon name="list" size={16} /> Langes Dokument – wird beim Speichern in {suggestion.chunk_count} durchsuchbare
                Abschnitte aufgeteilt.
              </div>
            )}

            <div className="stack-sm">
              <div className="row-wrap">
                <strong className="card-title">Vorgeschlagene Rolle</strong>
                <span className={`pill ${suggestion.suggested_role === "all" ? "pill-all" : "pill-restricted"}`}>
                  {suggestion.suggested_role}
                </span>
              </div>
              {suggestion.reasons.length > 0 && (
                <ul className="reasons">
                  {suggestion.reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="stack-sm" role="radiogroup" aria-label="Rolle wählen">
              <span className="field">Wer darf dieses Dokument sehen?</span>
              <div className="role-choices">
                {roleNames.map((name) => (
                  <button
                    key={name}
                    type="button"
                    role="radio"
                    aria-checked={chosenRole === name}
                    className="role-choice"
                    onClick={() => setChosenRole(name)}
                  >
                    {chosenRole === name && <Icon name="check" size={14} strokeWidth={2.6} />}
                    {name}
                  </button>
                ))}
              </div>
            </div>

            <div className="row-wrap">
              <button type="button" onClick={handleSave} className="btn btn-primary btn-lg" disabled={loading}>
                {loading && <span className="spinner" />}
                {loading ? "Speichere …" : "Dokument speichern"}
              </button>
              <button type="button" onClick={reset} className="btn btn-ghost btn-lg" disabled={loading}>
                Abbrechen
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
