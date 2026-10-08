import { useEffect, useRef, useState } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";
import "vis-network/styles/vis-network.css";
import { useAuth } from "../context/AuthContext";
import { useSessionExpiry } from "../hooks/useSessionExpiry";
import { graphData as fetchGraphData } from "../api";
import Icon from "./Icon";

function truncate(text, max = 28) {
  return text.length > max ? text.slice(0, max) + "…" : text;
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** Zaehlt Theme-Wechsel, damit der Graph mit den neuen Farben neu aufgebaut wird. */
function useThemeTick() {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const observer = new MutationObserver(() => setTick((t) => t + 1));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);
  return tick;
}

/**
 * Obsidian-artige Netzwerk-Ansicht: jedes Dokument ein Knoten, eine Kante
 * zu seinen aehnlichsten Nachbarn (siehe db.py graph_data - serverseitig
 * bereits auf Top-5-Nachbarn und RBAC/Tenant begrenzt). Klick auf einen
 * Knoten zeigt Details im Seitenpanel und hebt Nachbarn hervor.
 */
export default function GraphView() {
  const { token } = useAuth();
  const handleSessionExpiry = useSessionExpiry();
  const themeTick = useThemeTick();
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null); // {node, neighbors}

  useEffect(() => {
    let cancelled = false;
    fetchGraphData(token)
      .then((d) => !cancelled && setData(d))
      .catch((err) => {
        if (!cancelled && !handleSessionExpiry(err)) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    if (!data || !containerRef.current) return;

    const allColor = cssVar("--teal");
    const restrictedColor = cssVar("--mgmt");
    const edgeColor = cssVar("--rule");
    const textColor = cssVar("--ink");
    const cardBg = cssVar("--card-bg");
    const byId = new Map(data.nodes.map((n) => [n.id, n]));

    const nodeColor = (c) => ({
      background: c,
      border: cardBg,
      highlight: { background: c, border: textColor },
      hover: { background: c, border: textColor },
    });

    const nodes = new DataSet(
      data.nodes.map((n) => ({
        id: n.id,
        label: truncate(n.text),
        color: nodeColor(n.restricted ? restrictedColor : allColor),
      }))
    );
    const edges = new DataSet(
      data.edges.map((e, i) => ({
        id: i,
        from: e.source,
        to: e.target,
        value: e.weight,
        title: `Ähnlichkeit: ${e.weight}`,
      }))
    );

    const network = new Network(
      containerRef.current,
      { nodes, edges },
      {
        nodes: {
          shape: "dot",
          size: 11,
          borderWidth: 2,
          font: { color: textColor, size: 12, face: "-apple-system, Segoe UI, sans-serif" },
        },
        edges: {
          color: { color: edgeColor, highlight: allColor, hover: allColor, opacity: 0.9 },
          smooth: { type: "continuous" },
          scaling: { min: 1, max: 5 },
        },
        physics: {
          barnesHut: { gravitationalConstant: -4000, springLength: 120, springConstant: 0.04 },
          stabilization: { iterations: 150 },
        },
        interaction: { hover: true, tooltipDelay: 150, zoomView: true },
      }
    );
    networkRef.current = network;

    network.on("click", (params) => {
      if (params.nodes.length === 0) {
        network.unselectAll();
        setSelected(null);
        return;
      }
      const clicked = params.nodes[0];
      const connected = network.getConnectedNodes(clicked);
      network.selectNodes([clicked, ...connected]);
      setSelected({
        node: byId.get(clicked),
        neighbors: connected.map((id) => byId.get(id)).filter(Boolean),
      });
    });

    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, [data, themeTick]);

  function zoom(factor) {
    const net = networkRef.current;
    if (net) net.moveTo({ scale: net.getScale() * factor, animation: { duration: 200 } });
  }

  if (error)
    return (
      <div className="alert alert-error" role="alert">
        <Icon name="alert" size={16} /> {error}
      </div>
    );

  if (!data) return <div className="skeleton" style={{ height: 420 }} aria-busy="true" aria-label="Graph wird geladen" />;

  if (data.nodes.length === 0)
    return (
      <div className="empty">
        <span className="empty-icon">
          <Icon name="graph" size={22} />
        </span>
        <strong>Noch keine Dokumente</strong>
        <span>Sobald Dokumente hochgeladen sind, erscheinen sie hier als vernetzte Knoten.</span>
      </div>
    );

  return (
    <div className="stack-sm">
      <div className="row-wrap" style={{ justifyContent: "space-between" }}>
        <span className="card-sub">
          {data.nodes.length} Dokumente · Klick auf einen Knoten zeigt Details, Scrollen zoomt.
        </span>
        <span className="row-wrap">
          <span className="pill pill-all">● Alle Rollen</span>
          <span className="pill pill-restricted">● Nur Management</span>
        </span>
      </div>

      <div className="graph-layout">
        <div className="graph-canvas-wrap">
          <div className="graph-tools">
            <button className="btn-icon" onClick={() => zoom(1.3)} aria-label="Vergrößern">
              <Icon name="zoomIn" />
            </button>
            <button className="btn-icon" onClick={() => zoom(1 / 1.3)} aria-label="Verkleinern">
              <Icon name="zoomOut" />
            </button>
            <button
              className="btn-icon"
              onClick={() => networkRef.current?.fit({ animation: { duration: 250 } })}
              aria-label="Alles einpassen"
            >
              <Icon name="maximize" />
            </button>
          </div>
          <div ref={containerRef} className="graph-canvas" role="img" aria-label="Netzwerk der Dokumente" />
        </div>

        <aside className="card graph-side stack-sm" aria-live="polite">
          {selected ? (
            <>
              <div className="row-wrap">
                <span className={`pill ${selected.node.restricted ? "pill-restricted" : "pill-all"}`}>
                  {selected.node.restricted ? "Nur Management" : "Alle Rollen"}
                </span>
                {selected.node.customer_label && <span className="pill pill-neutral">{selected.node.customer_label}</span>}
              </div>
              <p style={{ fontSize: 14, overflowWrap: "anywhere" }}>{selected.node.text}</p>
              {selected.node.source_document && (
                <span className="card-sub row" style={{ gap: 6 }}>
                  <Icon name="file" size={14} /> {selected.node.source_document}
                </span>
              )}
              <div className="card-sub" style={{ paddingTop: 8, borderTop: "1px solid var(--rule)" }}>
                {selected.neighbors.length} ähnliche Dokumente verbunden
              </div>
            </>
          ) : (
            <>
              <strong className="card-title">Details</strong>
              <span className="card-sub">Wähle einen Knoten, um Text, Quelle und Berechtigung zu sehen.</span>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
