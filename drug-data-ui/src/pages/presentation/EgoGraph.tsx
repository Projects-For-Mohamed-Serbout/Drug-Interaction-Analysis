import { useMemo } from "react";
import { useTranslation } from "react-i18next";

/* severity → colour (shared palette) */
const SEV_BAR: Record<string, string> = {
  contraindicated: "#ef4444",
  severe: "#f97316",
  moderate: "#eab308",
  mild: "#22c55e",
  unknown: "#9ca3af",
};
const SEV_ORDER = ["contraindicated", "severe", "moderate", "mild", "unknown"];

export interface Target {
  name: string;
  severity: string;
}
interface EgoGraphProps {
  center: string;
  targets: Target[];
  /** total interactions (for the "+N more" note); defaults to targets.length */
  total?: number;
  maxNodes?: number;
}

const truncate = (s: string, n = 22) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

/**
 * Presentational radial ego-network: a centre drug surrounded by its
 * interacting drugs, edges/nodes coloured by severity. Pure SVG, no data
 * fetching — feed it a centre + targets. Reused by the static Part-3 graph
 * and the live interaction lookup.
 */
const EgoGraph = ({ center, targets, total, maxNodes = 10 }: EgoGraphProps) => {
  const { t } = useTranslation();

  const layout = useMemo(() => {
    const W = 680;
    const H = 440;
    const cx = W / 2;
    const cy = H / 2;
    const R = 165;
    const sorted = [...targets].sort(
      (a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity)
    );
    const shown = sorted.slice(0, maxNodes);
    const nodes = shown.map((tg, i) => {
      const angle = (2 * Math.PI * i) / shown.length - Math.PI / 2;
      return {
        ...tg,
        x: cx + R * Math.cos(angle),
        y: cy + R * Math.sin(angle),
        right: Math.cos(angle) >= -0.01,
      };
    });
    return { W, H, cx, cy, nodes, hidden: (total ?? targets.length) - shown.length };
  }, [targets, total, maxNodes]);

  if (targets.length === 0) return null;

  const legend = SEV_ORDER.filter((s) => layout.nodes.some((n) => n.severity === s));

  return (
    <div>
      <svg viewBox={`0 0 ${layout.W} ${layout.H}`} className="w-full h-auto" role="img" aria-label={center}>
        {/* edges */}
        {layout.nodes.map((n, i) => (
          <line
            key={`e${i}`}
            x1={layout.cx}
            y1={layout.cy}
            x2={n.x}
            y2={n.y}
            stroke={SEV_BAR[n.severity] || SEV_BAR.unknown}
            strokeWidth={2}
            strokeOpacity={0.55}
          />
        ))}

        {/* target nodes */}
        {layout.nodes.map((n, i) => (
          <g key={`n${i}`}>
            <circle cx={n.x} cy={n.y} r={9} fill={SEV_BAR[n.severity] || SEV_BAR.unknown} />
            <text
              x={n.right ? n.x + 14 : n.x - 14}
              y={n.y + 4}
              textAnchor={n.right ? "start" : "end"}
              className="fill-gray-600 dark:fill-gray-300"
              style={{ fontSize: 12 }}
            >
              {truncate(n.name)}
            </text>
          </g>
        ))}

        {/* centre node */}
        <circle cx={layout.cx} cy={layout.cy} r={26} fill="#4f46e5" />
        <circle cx={layout.cx} cy={layout.cy} r={26} fill="none" stroke="#312e81" strokeWidth={2} />
        <text
          x={layout.cx}
          y={layout.cy + 4}
          textAnchor="middle"
          className="fill-white"
          style={{ fontSize: 11, fontWeight: 700 }}
        >
          {truncate(center, 14)}
        </text>
      </svg>

      {/* legend + overflow note */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs text-gray-500 dark:text-gray-400">
        {legend.map((s) => (
          <span key={s} className="inline-flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SEV_BAR[s] }} />
            <span className="capitalize">{s}</span>
          </span>
        ))}
        {layout.hidden > 0 && (
          <span className="ml-auto italic">{t("presentation.graph.more", { count: layout.hidden })}</span>
        )}
      </div>
    </div>
  );
};

export default EgoGraph;
