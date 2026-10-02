export default function ResultList({ results }) {
  if (results === null) {
    return <div style={styles.empty}>Noch keine Suche gestartet &ndash; Begriff eingeben und Enter druecken.</div>;
  }
  if (results.length === 0) {
    return <div style={styles.empty}>(keine sichtbaren Treffer)</div>;
  }

  return (
    <div style={styles.list}>
      {results.map((r) => (
        <div key={r.id} style={styles.card}>
          <div style={styles.score}>
            Score: {r.score}
            {r.source_document && (
              <span style={styles.source}>
                {" "}
                &middot; {r.source_document}
                {r.chunk_total > 1 && ` (Abschnitt ${r.chunk_index}/${r.chunk_total})`}
              </span>
            )}
          </div>
          <div style={styles.text}>{r.text}</div>
        </div>
      ))}
    </div>
  );
}

const styles = {
  list: { display: "flex", flexDirection: "column", gap: 10 },
  card: {
    background: "var(--card-bg)",
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow)",
    padding: "14px 18px",
  },
  score: {
    fontFamily: "ui-monospace, monospace",
    fontSize: 11,
    color: "var(--muted)",
    marginBottom: 4,
  },
  text: { fontSize: 15 },
  source: { fontStyle: "italic" },
  empty: {
    color: "var(--muted)",
    fontStyle: "italic",
    padding: "40px 16px",
    textAlign: "center",
    border: "1px dashed var(--rule)",
    borderRadius: "var(--radius)",
  },
};
