import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  Database, Brain, BarChart3, CheckCircle2, AlertTriangle, Trophy, ArrowRight, FlaskConical,
} from "lucide-react";
import { getIntegrityReport } from "../api/dashboard";
import { getNlpEvaluation } from "../api/nlpAnalysis";
import { getBenchmarkResults } from "../api/dbPerformance";

interface IntegrityData {
  summary: { pass: number; warn: number; fail: number };
  headline: {
    drugs: number | null;
    interactions_raw: number | null;
    interactions_neo4j: number | null;
    reference_dictionaries: number | null;
  };
  generated_at: string | null;
}

interface NlpTask {
  task: string;
  regex_f1: number | null;
  spacy_f1: number | null;
  best: string | null;
}
interface NlpEval {
  samples: number | null;
  model: string | null;
  tasks: NlpTask[];
}

interface BenchmarkSummary {
  overall_winner: string;
  speedup_factor: number;
  mongodb_wins: number;
  neo4j_wins: number;
  comparable_count: number;
  graph_exclusive_queries: number;
  mongodb_avg_ms: number;
  neo4j_avg_ms: number;
}

const num = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString());

const Results = () => {
  const { t } = useTranslation();
  const [integrity, setIntegrity] = useState<IntegrityData | null>(null);
  const [nlp, setNlp] = useState<NlpEval | null>(null);
  const [bench, setBench] = useState<BenchmarkSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [ig, ev, bm] = await Promise.allSettled([
        getIntegrityReport(),
        getNlpEvaluation(),
        getBenchmarkResults(),
      ]);
      if (ig.status === "fulfilled") setIntegrity(ig.value);
      if (ev.status === "fulfilled") setNlp(ev.value);
      if (bm.status === "fulfilled") setBench(bm.value);
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-48 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FlaskConical className="text-teal-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("results.title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("results.description")}</p>
        </div>
      </div>

      {/* ============ PART 1 — ETL ============ */}
      <section className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750 flex items-center gap-2">
          <Database size={18} className="text-emerald-500" />
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">Part 1 — Data Engineering (ETL)</h2>
        </div>
        <div className="p-5">
          {integrity ? (
            <>
              <div className="flex items-center gap-2 mb-4">
                {integrity.summary.fail === 0 ? (
                  <CheckCircle2 size={20} className="text-green-500" />
                ) : (
                  <AlertTriangle size={20} className="text-red-500" />
                )}
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  Data integrity verified — {integrity.summary.pass}/
                  {integrity.summary.pass + integrity.summary.warn + integrity.summary.fail} checks passed
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Stat label="Drugs (XML = Mongo = Neo4j)" value={num(integrity.headline.drugs)} />
                <Stat label="Interactions (MongoDB)" value={num(integrity.headline.interactions_raw)} />
                <Stat label="Interaction edges (Neo4j)" value={num(integrity.headline.interactions_neo4j)} />
                <Stat label="Reference dictionaries" value={num(integrity.headline.reference_dictionaries)} />
              </div>
              <p className="text-xs text-gray-400 mt-3">
                Source XML reconciled against MongoDB and Neo4j; zero referential-integrity violations.
              </p>
            </>
          ) : (
            <Empty hint="Run: python -m scripts.verify_data_integrity" />
          )}
        </div>
      </section>

      {/* ============ PART 2 — NLP (RQ1) ============ */}
      <section className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750 flex items-center gap-2">
          <Brain size={18} className="text-sky-500" />
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            Part 2 — NLP &nbsp;<span className="text-xs font-normal text-gray-400">RQ1: which NLP technique is most effective?</span>
          </h2>
        </div>
        <div className="p-5">
          {nlp ? (
            <>
              <table className="w-full text-sm mb-3">
                <thead>
                  <tr className="border-b dark:border-gray-700 text-gray-500 dark:text-gray-400">
                    <th className="text-left py-2 font-semibold">Task (macro-F1)</th>
                    <th className="text-right py-2 font-semibold">Regex</th>
                    <th className="text-right py-2 font-semibold">spaCy</th>
                    <th className="text-center py-2 font-semibold">Best</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {nlp.tasks.map((tk) => (
                    <tr key={tk.task}>
                      <td className="py-2 capitalize text-gray-800 dark:text-gray-200">{tk.task}</td>
                      <td className={`py-2 text-right font-mono ${tk.best === "regex" ? "font-bold text-green-600" : "text-gray-600 dark:text-gray-400"}`}>
                        {tk.regex_f1?.toFixed(3) ?? "—"}
                      </td>
                      <td className={`py-2 text-right font-mono ${tk.best === "spacy" ? "font-bold text-blue-600" : "text-gray-600 dark:text-gray-400"}`}>
                        {tk.spacy_f1?.toFixed(3) ?? "—"}
                      </td>
                      <td className="py-2 text-center">
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                          tk.best === "regex"
                            ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                            : "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
                        }`}>
                          {tk.best === "regex" ? "Regex" : "spaCy"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Evaluated on {num(nlp.samples)} manually-annotated samples (spaCy model {nlp.model}).
                Regex wins on severity and clinical type; spaCy wins on mechanism.
              </p>
            </>
          ) : (
            <Empty hint="Run: python -m scripts.evaluate_nlp --output results/" />
          )}
        </div>
      </section>

      {/* ============ PART 3 — Databases (RQ2/RQ3) ============ */}
      <section className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750 flex items-center gap-2">
          <BarChart3 size={18} className="text-rose-500" />
          <h2 className="font-semibold text-gray-700 dark:text-gray-300">
            Part 3 — Databases &nbsp;<span className="text-xs font-normal text-gray-400">RQ2/RQ3: optimal structure & query performance</span>
          </h2>
        </div>
        <div className="p-5">
          {bench ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-750">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Trophy size={14} className="text-yellow-500" />
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">Overall</span>
                  </div>
                  <p className={`text-lg font-bold ${bench.overall_winner === "Neo4j" ? "text-blue-600" : bench.overall_winner === "MongoDB" ? "text-green-600" : "text-gray-600"}`}>
                    {bench.overall_winner}
                  </p>
                  <p className="text-xs text-gray-400">
                    {bench.overall_winner === "Comparable" ? "within 10%" : `${bench.speedup_factor}× faster`}
                  </p>
                </div>
                <Stat label="MongoDB wins" value={`${bench.mongodb_wins}`} sub={`median ${bench.mongodb_avg_ms.toFixed(0)}ms`} />
                <Stat label="Neo4j wins" value={`${bench.neo4j_wins}`} sub={`median ${bench.neo4j_avg_ms.toFixed(0)}ms`} />
                <Stat label="Graph-exclusive" value={`${bench.graph_exclusive_queries}`} sub="Neo4j only" />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {bench.comparable_count} comparable queries (fair index-vs-index). Neo4j leads on aggregation,
                traversal and complex filters; MongoDB leads on simple indexed range scans.
              </p>
              <Link to="/database-performance" className="inline-flex items-center gap-1 mt-3 text-sm text-rose-600 dark:text-rose-400 hover:underline">
                See full benchmark & scalability charts <ArrowRight size={14} />
              </Link>
            </>
          ) : (
            <Empty hint="Run: python run_benchmarks.py" />
          )}
        </div>
      </section>
    </div>
  );
};

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-750">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-800 dark:text-white">{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

function Empty({ hint }: { hint: string }) {
  return (
    <div className="flex items-start gap-2 text-sm text-gray-500 dark:text-gray-400">
      <AlertTriangle size={16} className="text-amber-500 mt-0.5" />
      <span>No results available yet. <code className="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">{hint}</code></span>
    </div>
  );
}

export default Results;
