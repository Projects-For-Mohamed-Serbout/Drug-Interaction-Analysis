import { useEffect, useState } from "react";
import { Flame } from "lucide-react";
import { getSeverityTypeMatrix } from "../api/nlpAnalysis";

const SEV_COLOR: Record<string, string> = {
  contraindicated: "239,68,68", // red
  severe: "249,115,22", // orange
  moderate: "234,179,8", // yellow
  mild: "34,197,94", // green
  unknown: "148,163,184", // gray
};

interface TypeRow { type: string; total: number; counts: Record<string, number>; }
interface Matrix { severities: string[]; types: TypeRow[]; total: number; }

const label = (s: string) => s.replace(/_/g, " ");

/**
 * Severity x interaction-type heatmap. Each row is an interaction type; cell
 * colour intensity = share of that type's interactions at a given severity.
 * Reveals which interaction types concentrate the clinical danger.
 */
const SeverityTypeHeatmap = () => {
  const [data, setData] = useState<Matrix | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setData(await getSeverityTypeMatrix());
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <div className="h-64 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />;
  }
  if (!data || data.types.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 text-sm text-gray-400">
        No interaction data available.
      </div>
    );
  }

  // only show severities that actually occur in the corpus
  const activeSev = data.severities.filter((s) => data.types.some((t) => t.counts[s] > 0));
  const maxTotal = Math.max(...data.types.map((t) => t.total), 1);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <Flame size={18} className="text-rose-500" />
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
          Where the danger concentrates — interaction type × severity
        </h3>
        <span className="ml-auto text-xs text-gray-400">{data.total.toLocaleString()} interactions</span>
      </div>

      <div className="p-5 overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="text-left font-normal text-xs text-gray-400 p-2">interaction type</th>
              {activeSev.map((s) => (
                <th key={s} className="p-2 text-xs font-medium capitalize" style={{ color: `rgb(${SEV_COLOR[s]})` }}>
                  {s}
                </th>
              ))}
              <th className="p-2 text-xs font-normal text-gray-400 text-right">total</th>
            </tr>
          </thead>
          <tbody>
            {data.types.map((row) => (
              <tr key={row.type} className="border-t dark:border-gray-700/50">
                <td className="p-2 capitalize text-gray-700 dark:text-gray-300 whitespace-nowrap">{label(row.type)}</td>
                {activeSev.map((s) => {
                  const c = row.counts[s] || 0;
                  const frac = row.total > 0 ? c / row.total : 0;
                  const a = c === 0 ? 0 : 0.12 + 0.88 * frac;
                  return (
                    <td
                      key={s}
                      className="p-2 text-center"
                      style={{
                        backgroundColor: c === 0 ? "transparent" : `rgba(${SEV_COLOR[s]},${a})`,
                        color: a > 0.5 ? "white" : "inherit",
                      }}
                      title={`${label(row.type)} · ${s}: ${c.toLocaleString()} (${(frac * 100).toFixed(0)}%)`}
                    >
                      {c > 0 ? `${(frac * 100).toFixed(0)}%` : "·"}
                    </td>
                  );
                })}
                <td className="p-2 text-right text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  <div className="flex items-center justify-end gap-2">
                    <div className="hidden sm:block w-16 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-gray-400" style={{ width: `${(row.total / maxTotal) * 100}%` }} />
                    </div>
                    <span className="text-xs tabular-nums">{row.total.toLocaleString()}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 border-l-4 border-rose-400 pl-3">
          <strong className="text-gray-700 dark:text-gray-300">Reading it — </strong>
          cell = share of that interaction type at each severity (colour intensity = share). Cardiac and
          muscular interactions concentrate the contraindicated/severe cases, while metabolic, efficacy and
          gastrointestinal interactions are predominantly moderate.
        </p>
      </div>
    </div>
  );
};

export default SeverityTypeHeatmap;
