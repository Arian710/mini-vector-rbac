import { useState } from "react";
import Icon from "./Icon";
import { useToast } from "./Toast";

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Hebt Suchbegriffe (>= 3 Zeichen) im Text hervor - rein visuell, die Treffer selbst sind semantisch. */
function Highlighted({ text, query }) {
  const terms = [...new Set(query.toLowerCase().split(/\s+/).filter((t) => t.length >= 3))];
  if (terms.length === 0) return text;
  const regex = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "gi");
  return text.split(regex).map((part, i) =>
    i % 2 === 1 ? <mark key={i}>{part}</mark> : <span key={i}>{part}</span>
  );
}

function ResultCard({ result, query, index }) {
  const toast = useToast();
  const [expanded, setExpanded] = useState(false);
  const long = result.text.length > 280;
  const pct = Math.round(Math.max(0, Math.min(1, result.score)) * 100);

  async function copy() {
    try {
      await navigator.clipboard.writeText(result.text);
      toast.success("Text kopiert.");
    } catch {
      toast.error("Kopieren nicht möglich.");
    }
  }

  return (
    <article className="result" style={{ animationDelay: `${index * 40}ms` }}>
      <div className="result-meta">
        <span className="score" title={`Cosine-Ähnlichkeit ${result.score}`}>
          <span className="score-bar" aria-hidden="true">
            <span style={{ width: `${pct}%` }} />
          </span>
          {pct}% Treffer
        </span>
        {result.source_document && (
          <span className="row" style={{ gap: 5 }}>
            <Icon name="file" size={13} /> {result.source_document}
            {result.chunk_total > 1 && ` · Abschnitt ${result.chunk_index}/${result.chunk_total}`}
          </span>
        )}
        <span className="spacer" />
        <button className="btn-icon" style={{ padding: 4 }} onClick={copy} aria-label="Text kopieren" title="Kopieren">
          <Icon name="copy" size={15} />
        </button>
      </div>
      <p className={`result-text ${long && !expanded ? "clamped" : ""}`}>
        <Highlighted text={result.text} query={query} />
      </p>
      {long && (
        <button className="link-btn" style={{ alignSelf: "flex-start" }} onClick={() => setExpanded((e) => !e)}>
          {expanded ? "Weniger anzeigen" : "Mehr anzeigen"}
        </button>
      )}
    </article>
  );
}

function SkeletonList() {
  return (
    <div className="stack-sm" aria-busy="true" aria-label="Suche läuft">
      {[0, 1, 2].map((i) => (
        <div key={i} className="skeleton" style={{ height: 96 }} />
      ))}
    </div>
  );
}

export default function ResultList({ results, query, loading }) {
  if (loading) return <SkeletonList />;

  if (results === null) {
    return (
      <div className="empty">
        <span className="empty-icon">
          <Icon name="sparkles" size={22} />
        </span>
        <strong>Stell eine Frage in eigenen Worten</strong>
        <span>Die Suche versteht Bedeutung, nicht nur Stichwörter – und zeigt dir nur, was deine Rolle sehen darf.</span>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="empty">
        <span className="empty-icon">
          <Icon name="search" size={22} />
        </span>
        <strong>Keine sichtbaren Treffer</strong>
        <span>Formuliere die Frage anders. Dokumente außerhalb deiner Berechtigung erscheinen hier nie.</span>
      </div>
    );
  }

  return (
    <div className="stack-sm">
      <div className="card-sub" aria-live="polite">
        {results.length} {results.length === 1 ? "Treffer" : "Treffer"} für „{query}“
      </div>
      {results.map((r, i) => (
        <ResultCard key={r.id} result={r} query={query} index={i} />
      ))}
    </div>
  );
}
