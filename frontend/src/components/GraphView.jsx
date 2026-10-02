import { useEffect, useRef, useState } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";
import "vis-network/styles/vis-network.css";
import { useAuth } from "../context/AuthContext";
import { graphData as fetchGraphData } from "../api";

function truncate(text, max = 30) {
  return text.length > max ? text.slice(0, max) + "…" : text;
}

/**
 * Obsidian-artige Netzwerk-Ansicht: jedes Dokument ein Knoten, eine Kante
 * zu seinen aehnlichsten Nachbarn (siehe db.py graph_data - serverseitig
 * bereits auf Top-5-Nachbarn und RBAC/Tenant begrenzt). Physik-Simulation
 * sortiert die Knoten selbst zu Clustern, genau wie bei Obsidian's Graph View.
 */
export default function GraphView() {
  const { token } = useAuth();
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nodeCount, setNodeCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchGraphData(token);
        if (cancelled) return;
        setNodeCount(data.nodes.length);

        const nodes = new DataSet(
          data.nodes.map((n) => ({
            id: n.id,
            label: truncate(n.text),
            title: n.text,
          }))
        );
        const edges = new DataSet(
          data.edges.map((e, i) => ({
            id: i,
            from: e.source,
            to: e.target,
            value: e.weight,
            title: `Aehnlichkeit: ${e.weight}`,
          }))
        );

        const options = {
          nodes: {
            shape: "dot",
            size: 9,
            color: {
              background: "#0f6e56",
              border: "#0a4536",
              highlight: { background: "#0a4536", border: "#0a4536" },
            },
            font: { color: "#1c1c1a", size: 12, face: "-apple-system, Segoe UI, sans-serif" },
            borderWidth: 2,
          },
          edges: {
            color: { color: "#dad7cc", highlight: "#0f6e56", opacity: 0.6 },
            smooth: { type: "continuous" },
            scaling: { min: 1, max: 6 },
          },
          physics: {
            barnesHut: { gravitationalConstant: -4000, springLength: 120, springConstant: 0.04 },
            stabilization: { iterations: 150 },
          },
          interaction: { hover: true, tooltipDelay: 100 },
        };

        if (networkRef.current) {
          networkRef.current.destroy();
        }
        const network = new Network(containerRef.current, { nodes, edges }, options);
        networkRef.current = network;

        // Klick auf einen Knoten hebt ihn + direkt verbundene Nachbarn hervor -
        // macht Cluster-Zugehoerigkeit greifbar, genau wie bei Obsidian.
        network.on("click", (params) => {
          if (params.nodes.length === 0) {
            network.unselectAll();
            return;
          }
          const clicked = params.nodes[0];
          const connected = network.getConnectedNodes(clicked);
          network.selectNodes([clicked, ...connected]);
        });
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [token]);

  return (
    <div style={styles.wrapper}>
      {loading && <div style={styles.status}>Graph wird geladen...</div>}
      {error && <div style={styles.error}>{error}</div>}
      {!loading && !error && (
        <div style={styles.meta}>
          {nodeCount} Dokumente &mdash; Klick auf einen Knoten hebt verbundene Dokumente hervor, Scrollen zoomt.
        </div>
      )}
      <div ref={containerRef} style={styles.canvas} />
    </div>
  );
}

const styles = {
  wrapper: { display: "flex", flexDirection: "column", gap: 10 },
  canvas: {
    height: 520,
    border: "1px solid var(--rule)",
    borderRadius: "var(--radius)",
    background: "var(--card-bg)",
  },
  status: { color: "var(--muted)", fontSize: 13 },
  meta: { color: "var(--muted)", fontSize: 12 },
  error: {
    background: "var(--mgmt-pale)",
    color: "var(--mgmt)",
    padding: "10px 14px",
    borderRadius: "var(--radius-sm)",
    fontSize: 13,
  },
};
