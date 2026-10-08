import { useEffect, useRef } from "react";

/** Bestaetigungsdialog fuer destruktive Aktionen (statt sofort zu loeschen). */
export default function ConfirmDialog({ title, message, confirmLabel = "Bestätigen", busy, onConfirm, onCancel }) {
  const cancelRef = useRef(null);

  useEffect(() => {
    cancelRef.current?.focus();
    const onKey = (e) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div className="dialog-scrim" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dlg-title">
        <h3 id="dlg-title">{title}</h3>
        <p>{message}</p>
        <div className="actions">
          <button ref={cancelRef} className="btn btn-ghost" onClick={onCancel} disabled={busy}>
            Abbrechen
          </button>
          <button className="btn btn-danger-solid" onClick={onConfirm} disabled={busy}>
            {busy && <span className="spinner" />} {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
