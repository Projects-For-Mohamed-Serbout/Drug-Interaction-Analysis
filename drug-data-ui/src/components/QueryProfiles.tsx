import { useEffect, useState } from "react";
import { Gauge, Wifi, Server } from "lucide-react";
import { getQueryProfiles } from "../api/dbPerformance";

interface Spread { median: number | null; min: number | null; max: number | null; runs: number; }
interface Side { server_ms: number | null; wall_ms: number | null; spread?: Spread; used_index?: boolean; scan?: string; docs_examined?: number; db_hits?: number; }
interface Row { id: string; category: string; name: string; mongodb: Side; neo4j: Side; }
interface Profiles { generated_at: string | null; server_runs: number | null; queries: Row[]; }

const ms = (v: number | null | undefined) => (v == null ? "—" : `${v} ms`);
const MONGO = "#10b981";
const NEO = "#3b82f6";

/**
 * Server-side vs wall-clock query profiling. Isolates real engine execution time
 * (MongoDB explain / Neo4j PROFILE) from the cloud-network round-trip captured by
 * wall-clock — the key fairness correction for RQ2/RQ3.
 */
const QueryProfiles = () => {
  const [data, setData] = useState<Profiles | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setData(await getQueryProfiles());
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="h-72 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />;
  if (!data || data.queries.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 text-sm text-gray-400">
        No query profiles found. Run <code>scripts/profile_queries.py --output results/</code>.
      </div>
    );
  }

  // max across server-side values, for bar scaling
  const maxServer = Math.max(
    1,
    ...data.queries.flatMap((q) => [q.mongodb.server_ms ?? 0, q.neo4j.server_ms ?? 0])
  );
  const maxWall = Math.max(
    1,
    ...data.queries.flatMap((q) => [q.mongodb.wall_ms ?? 0, q.neo4j.wall_ms ?? 0])
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <Gauge size={18} className="text-rose-500" />
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
          Engine time vs wall-clock — isolating the network
        </h3>
        <span className="ml-auto text-xs text-gray-400">
          server = median of {data.server_runs} warm runs
        </span>
      </div>

      <div className="p-5">
        {/* legend */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 mb-4 text-xs text-gray-500 dark:text-gray-400">
          <span className="inline-flex items-center gap-1.5"><Server size={13} /> server-side = real DB work (explain / PROFILE)</span>
          <span className="inline-flex items-center gap-1.5"><Wifi size={13} /> wall-clock = incl. cloud round-trip</span>
          <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: MONGO }} /> MongoDB</span>
          <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: NEO }} /> Neo4j</span>
        </div>

        <div className="space-y-4">
          {data.queries.map((q) => (
            <div key={q.id} className="border-b dark:border-gray-700/50 pb-3 last:border-0">
              <div className="flex justify-between items-baseline mb-1.5">
                <span className="text-sm text-gray-700 dark:text-gray-200">
                  <span className="font-mono text-xs text-gray-400 mr-1.5">{q.id}</span>
                  {q.name}
                </span>
                <span className="text-[11px] text-gray-400">{q.category}</span>
              </div>

              <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5">
                <Engine label="MongoDB" color={MONGO} side={q.mongodb} maxServer={maxServer} maxWall={maxWall}
                  detail={q.mongodb.scan ? `${q.mongodb.scan}${q.mongodb.docs_examined != null ? ` · ${q.mongodb.docs_examined.toLocaleString()} docs` : ""}` : undefined} />
                <Engine label="Neo4j" color={NEO} side={q.neo4j} maxServer={maxServer} maxWall={maxWall}
                  detail={q.neo4j.db_hits != null ? `${q.neo4j.used_index ? "index" : "scan"} · ${q.neo4j.db_hits.toLocaleString()} db hits` : undefined} />
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 border-l-4 border-rose-400 pl-3">
          <strong className="text-gray-700 dark:text-gray-300">Reading it — </strong>
          well-indexed queries run in single-digit ms on both engines (the long wall-clock bars are
          the ~35–40 ms cloud round-trip, not the database). The genuine engine-level difference is
          aggregation, where Neo4j is much faster (Q6), while MongoDB keeps an edge on the indexed
          range scan (Q3).
        </p>
      </div>
    </div>
  );
};

function Engine({
  label, color, side, maxServer, maxWall, detail,
}: {
  label: string; color: string; side: Side; maxServer: number; maxWall: number; detail?: string;
}) {
  const sp = side.spread;
  const showSpread = sp && sp.runs > 1 && sp.min !== sp.max;
  return (
    <div>
      <div className="flex items-center gap-2 text-[11px] mb-0.5">
        <span className="w-14 font-medium" style={{ color }}>{label}</span>
        <Bar value={side.server_ms} max={maxServer} color={color} solid />
        <span className="w-20 text-right font-mono text-gray-600 dark:text-gray-300">
          {ms(side.server_ms)}{showSpread ? ` (${sp!.min}-${sp!.max})` : ""}
        </span>
      </div>
      <div className="flex items-center gap-2 text-[11px]">
        <span className="w-14" />
        <Bar value={side.wall_ms} max={maxWall} color={color} />
        <span className="w-20 text-right font-mono text-gray-400">{ms(side.wall_ms)}</span>
      </div>
      {detail && <div className="pl-16 text-[10px] text-gray-400 mt-0.5">{detail}</div>}
    </div>
  );
}

function Bar({ value, max, color, solid }: { value: number | null; max: number; color: string; solid?: boolean }) {
  const w = value != null ? Math.max(1.5, (value / max) * 100) : 0;
  return (
    <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2.5 relative">
      <div className="h-2.5 rounded-full" style={{ width: `${w}%`, backgroundColor: color, opacity: solid ? 1 : 0.4 }} />
    </div>
  );
}

export default QueryProfiles;
