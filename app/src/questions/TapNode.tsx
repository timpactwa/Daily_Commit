import { useId } from "react";
import type { PublicQuestion } from "../api";
export function TapNode({
  question,
  value,
  onChange,
  disabled,
  excludedIds = [],
}: {
  question: PublicQuestion;
  value?: string;
  onChange: (id: string) => void;
  disabled: boolean;
  excludedIds?: string[];
}) {
  const arrowId = useId().replaceAll(":", "");
  const diagram = question.diagram;
  if (!diagram || !diagram.nodes.length || diagram.nodes.length > 12)
    return null;
  const ids = new Set(diagram.nodes.map((n) => n.id));
  if (
    ids.size !== diagram.nodes.length ||
    diagram.edges.some((e) => !ids.has(e.from) || !ids.has(e.to))
  )
    return null;
  const ranks = new Map<string, number>();
  const remaining = new Set(ids);
  for (let pass = 0; pass < diagram.nodes.length; pass++) {
    for (const id of remaining) {
      const parents = diagram.edges
        .filter((e) => e.to === id)
        .map((e) => e.from);
      if (parents.every((parent) => ranks.has(parent))) {
        ranks.set(
          id,
          parents.length
            ? Math.max(...parents.map((p) => ranks.get(p)!)) + 1
            : 0,
        );
        remaining.delete(id);
      }
    }
  }
  if (remaining.size) return null;
  const maxRank = Math.max(...ranks.values());
  const rankNodes = Array.from({ length: maxRank + 1 }, (_, rank) =>
    diagram.nodes.filter((n) => ranks.get(n.id) === rank),
  );
  const width = (maxRank + 1) * 180;
  const height = Math.max(...rankNodes.map((n) => n.length)) * 120 + 16;
  const positions = new Map(
    diagram.nodes.map((node) => {
      const rank = ranks.get(node.id)!;
      const peers = rankNodes[rank];
      return [
        node.id,
        {
          x: rank * 180 + 10,
          y:
            peers.indexOf(node) * 120 +
            8 +
            (height - 16 - peers.length * 120) / 2,
        },
      ];
    }),
  );
  return (
    <div
      className="diagram-scroll"
      tabIndex={0}
      aria-label="Flow diagram, scroll horizontally to explore"
    >
      <div className="diagram" style={{ width, height }}>
        <svg width={width} height={height} aria-hidden="true">
          <defs>
            <marker
              id={arrowId}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#9aaa86" />
            </marker>
          </defs>
          {diagram.edges.map((edge, i) => {
            const from = positions.get(edge.from)!;
            const to = positions.get(edge.to)!;
            return (
              <g key={i}>
                <path
                  d={`M ${from.x + 145} ${from.y + 45} C ${from.x + 170} ${from.y + 45}, ${to.x - 25} ${to.y + 45}, ${to.x - 3} ${to.y + 45}`}
                  stroke="#a7b494"
                  strokeWidth="1.5"
                  fill="none"
                  markerEnd={`url(#${arrowId})`}
                />
                {edge.label && <title>{edge.label}</title>}
              </g>
            );
          })}
        </svg>
        {diagram.nodes.map((node) => {
          const p = positions.get(node.id)!;
          return (
            <button
              key={node.id}
              style={{ left: p.x, top: p.y }}
              className={`diagram-node ${value === node.id ? "selected" : ""}`}
              aria-pressed={value === node.id}
              disabled={disabled || excludedIds.includes(node.id)}
              onClick={() => onChange(node.id)}
            >
              <span className="node-kind">{node.kind ?? "service"}</span>
              <strong>{node.label}</strong>
              {node.note && <small>{node.note}</small>}
            </button>
          );
        })}
      </div>
      <p className="small">Tap a node above, or choose from the list below.</p>
      <ul className="connections">
        {diagram.edges
          .filter((e) => e.label)
          .map((e, i) => (
            <li key={i}>
              {diagram.nodes.find((n) => n.id === e.from)?.label} →{" "}
              {diagram.nodes.find((n) => n.id === e.to)?.label}: {e.label}
            </li>
          ))}
      </ul>
    </div>
  );
}
