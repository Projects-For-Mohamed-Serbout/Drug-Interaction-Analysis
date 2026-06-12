import { useEffect, useMemo, useState } from "react";
import { Target, Grid3x3, GitCompareArrows } from "lucide-react";
import { getNlpEvaluation } from "../api/nlpAnalysis";

interface Confusion { classes: string[]; matrix: number[][]; }
interface Approach {
  accuracy: number | null;
  macro_f1: number | null;
  weighted_f1: number | null;
  confusion: Confusion | null;
}
interface Task {
  task: string;
  best: string | null;
  regex: Approach;
  spacy: Approach;
}
interface Evaluation {
  samples: number | null;
  model: string | null;
  gold_source: string | null;
  tasks: Task[];
}

const pct = (v: number | null | undefined) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const short = (s: string) => s.replace(/_/g, " ").slice(0, 12);

/**
 * Model evaluation (RQ1): regex vs spaCy on the independent census of all
 * distinct interaction texts. Shows an accuracy comparison + an interactive
 * confusion-matrix heatmap. Dependency-free (plain SVG/HTML).
 */
const NlpEvaluation = () => {
  const [evalData, setEvalData] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [taskKey, setTaskKey] = useState("type");
  const [approach, setApproach] = useState<"regex" | "spacy">("spacy");

  useEffect(() => {
    (async () => {
      try {
        setEvalData(await getNlpEvaluation());
      } catch {
        setEvalData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const task = useMemo(
    () => evalData?.tasks.find((t) => t.task === taskKey) ?? null,
    [evalData, taskKey]
  );
  const conf = task ? task[approach].confusion : null;
  const matrixMax = useMemo(
    () => (conf ? Math.max(1, ...conf.matrix.flat()) : 1),
    [conf]
  );

  if (loading) {
    return <div className="h-64 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />;
  }
  if (!evalData || evalData.tasks.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 text-sm text-gray-400">
        No evaluation found. Run <code>scripts/evaluate_nlp.py --gold-csv data/gold_set.csv --output results/</code>.
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <Target size={18} className="text-cyan-500" />
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
          Model Evaluation (RQ1) — Regex vs spaCy
        </h3>
        <span className="ml-auto text-xs text-gray-400">
          census of {evalData.samples} distinct texts
        </span>
      </div>

      <div className="p-5 grid lg:grid-cols-2 gap-6">
        {/* ---------- accuracy comparison ---------- */}
        <div>
          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-1.5">
            <GitCompareArrows size={14} /> Accuracy by task
          </p>
          <div className="space-y-4">
            {evalData.tasks.map((tk) => (
              <div key={tk.task}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="capitalize text-gray-600 dark:text-gray-300">{tk.task}</span>
                  {tk.best && (
                    <span className="text-gray-400">
                      best:{" "}
                      <strong className={tk.best === "regex" ? "text-green-600" : "text-blue-600"}>
                        {tk.best}
                      </strong>
                    </span>
                  )}
                </div>
                <Bar label="Regex" value={tk.regex.accuracy} color="#16a34a" />
                <Bar label="spaCy" value={tk.spacy.accuracy} color="#3b82f6" />
                <div className="text-[10px] text-gray-400 mt-1">
                  macro-F1 {tk.regex.macro_f1?.toFixed(2)} / {tk.spacy.macro_f1?.toFixed(2)} ·
                  weighted-F1 {tk.regex.weighted_f1?.toFixed(2)} / {tk.spacy.weighted_f1?.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ---------- confusion matrix ---------- */}
        <div>
          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-3 flex items-center gap-1.5">
            <Grid3x3 size={14} /> Confusion matrix
          </p>

          {/* selectors */}
          <div className="flex flex-wrap gap-2 mb-3">
            <div className="flex rounded-lg border dark:border-gray-700 overflow-hidden text-xs">
              {["severity", "type", "mechanism"].map((k) => (
                <button
                  key={k}
                  onClick={() => setTaskKey(k)}
                  className={`px-2.5 py-1 capitalize ${taskKey === k ? "bg-cyan-500 text-white" : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"}`}
                >
                  {k}
                </button>
              ))}
            </div>
            <div className="flex rounded-lg border dark:border-gray-700 overflow-hidden text-xs">
              {(["regex", "spacy"] as const).map((k) => (
                <button
                  key={k}
                  onClick={() => setApproach(k)}
                  className={`px-2.5 py-1 ${approach === k ? "bg-cyan-500 text-white" : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"}`}
                >
                  {k}
                </button>
              ))}
            </div>
          </div>

          {conf && conf.classes.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="border-collapse text-[10px]">
                <thead>
                  <tr>
                    <th className="p-1 text-gray-400 font-normal text-right sticky left-0 bg-white dark:bg-gray-800">
                      true ↓ / pred →
                    </th>
                    {conf.classes.map((c) => (
                      <th key={c} className="p-1 text-gray-500 dark:text-gray-400 font-normal" title={c}>
                        <div className="rotate-0 whitespace-nowrap">{short(c)}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {conf.classes.map((rowCls, i) => (
                    <tr key={rowCls}>
                      <td className="p-1 text-right text-gray-500 dark:text-gray-400 whitespace-nowrap sticky left-0 bg-white dark:bg-gray-800" title={rowCls}>
                        {short(rowCls)}
                      </td>
                      {conf.classes.map((colCls, j) => {
                        const v = conf.matrix[i][j];
                        const correct = i === j;
                        const a = v === 0 ? 0 : 0.15 + 0.85 * (v / matrixMax);
                        const rgb = correct ? "34,197,94" : "239,68,68";
                        return (
                          <td
                            key={colCls}
                            className="w-7 h-7 text-center border border-gray-100 dark:border-gray-700/50"
                            style={{
                              backgroundColor: v === 0 ? "transparent" : `rgba(${rgb},${a})`,
                              color: a > 0.55 ? "white" : "inherit",
                            }}
                            title={`true ${rowCls} → pred ${colCls}: ${v}`}
                          >
                            {v || ""}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
                <span className="inline-flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: "rgba(34,197,94,0.7)" }} /> correct (diagonal)</span>
                <span className="inline-flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm" style={{ background: "rgba(239,68,68,0.7)" }} /> error</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">No confusion data for this task.</p>
          )}
        </div>
      </div>
    </div>
  );
};

function Bar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const w = value != null ? value * 100 : 0;
  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="text-[11px] w-12 text-gray-500 dark:text-gray-400">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3">
        <div className="h-3 rounded-full" style={{ width: `${w}%`, backgroundColor: color }} />
      </div>
      <span className="text-[11px] font-mono w-12 text-right text-gray-600 dark:text-gray-300">{pct(value)}</span>
    </div>
  );
}

export default NlpEvaluation;
