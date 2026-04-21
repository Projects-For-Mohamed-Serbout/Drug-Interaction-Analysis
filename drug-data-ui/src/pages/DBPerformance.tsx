import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Database, Trophy, Zap, Clock, Server, Layers, AlertTriangle } from "lucide-react";
import { toast } from "react-hot-toast";
import { getBenchmarkResults } from "../api/dbPerformance";

interface BenchmarkQuery {
  query: string;
  description: string | null;
  category: string | null;
  mongodb_ms: number | null;
  neo4j_ms: number | null;
  mongodb_p95_ms: number | null;
  neo4j_p95_ms: number | null;
  winner: string;
  speedup: string | null;
  row_count_match: boolean | null;
}

interface CategoryBreakdown {
  category: string;
  mongodb_wins: number;
  neo4j_wins: number;
  comparable: number;
}

interface BenchmarkSummary {
  queries: BenchmarkQuery[];
  mongodb_wins: number;
  neo4j_wins: number;
  comparable_count: number;
  mongodb_avg_ms: number;
  neo4j_avg_ms: number;
  overall_winner: string;
  speedup_factor: number;
  graph_exclusive_queries: number;
  category_breakdown: CategoryBreakdown[];
  iterations: number | null;
  row_count_mismatches: number;
}

const WINNER_STYLES: Record<string, string> = {
  MongoDB: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  "Neo4J": "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  "Neo4j": "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  Comparable: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
  "Neo4J only": "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300",
  "MongoDB only": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300",
};

const DBPerformance = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<BenchmarkSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getBenchmarkResults();
        setData(result);
      } catch {
        toast.error("Error loading benchmark results");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Database className="text-rose-500" size={28} />
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("databasePerformance.title")}</h1>
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-40 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const totalQueries = data.queries.length;
  const comparableQueries = data.queries.filter((q) => q.mongodb_ms != null && q.neo4j_ms != null);
  const graphOnlyQueries = data.queries.filter((q) => q.mongodb_ms == null);
  const maxTime = Math.max(
    ...data.queries.map((q) => Math.max(q.mongodb_ms || 0, q.neo4j_ms || 0)),
    1
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Database className="text-rose-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("databasePerformance.title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            MongoDB vs Neo4j — {totalQueries} queries benchmarked
            {data.iterations && ` (${data.iterations} iterations each)`}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Winner */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700 shadow-sm col-span-2 lg:col-span-1">
          <div className="flex items-center gap-2 mb-2">
            <Trophy size={18} className="text-yellow-500" />
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Overall Winner</span>
          </div>
          <p className={`text-2xl font-bold ${
            data.overall_winner === "Neo4j" ? "text-blue-600" :
            data.overall_winner === "MongoDB" ? "text-green-600" :
            "text-gray-600"
          }`}>
            {data.overall_winner}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.overall_winner === "Comparable"
              ? "Within 10% margin"
              : `${data.speedup_factor}x faster`}
          </p>
        </div>

        {/* MongoDB */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Server size={18} className="text-green-600" />
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">MongoDB</span>
          </div>
          <p className="text-2xl font-bold text-gray-800 dark:text-white">{data.mongodb_wins}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            wins · median {data.mongodb_avg_ms.toFixed(1)}ms
          </p>
        </div>

        {/* Neo4j */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={18} className="text-blue-500" />
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Neo4j</span>
          </div>
          <p className="text-2xl font-bold text-gray-800 dark:text-white">{data.neo4j_wins}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            wins · median {data.neo4j_avg_ms.toFixed(1)}ms
          </p>
        </div>

        {/* Query Breakdown */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={18} className="text-purple-500" />
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Queries</span>
          </div>
          <p className="text-2xl font-bold text-gray-800 dark:text-white">{totalQueries}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {comparableQueries.length} comparable · {graphOnlyQueries.length} graph-only
          </p>
        </div>
      </div>

      {/* Category Breakdown */}
      {data.category_breakdown && data.category_breakdown.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750 flex items-center gap-2">
            <Layers size={16} className="text-gray-500" />
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">Performance by Query Category</h3>
          </div>
          <div className="p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {data.category_breakdown.map((cat) => {
              const total = cat.mongodb_wins + cat.neo4j_wins + cat.comparable;
              return (
                <div key={cat.category} className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-750">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 truncate" title={cat.category}>
                    {cat.category}
                  </p>
                  <div className="flex justify-center gap-2 text-xs font-bold">
                    <span className="text-green-600" title="MongoDB wins">{cat.mongodb_wins}M</span>
                    <span className="text-blue-600" title="Neo4j wins">{cat.neo4j_wins}N</span>
                    {cat.comparable > 0 && (
                      <span className="text-gray-400" title="Comparable">~{cat.comparable}</span>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1">{total} queries</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">Query-by-Query Comparison</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Query</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 hidden lg:table-cell">Category</th>
                <th className="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 w-28">
                  <span className="flex items-center justify-end gap-1">
                    <Server size={14} className="text-green-600" /> MongoDB
                  </span>
                </th>
                <th className="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 w-28">
                  <span className="flex items-center justify-end gap-1">
                    <Zap size={14} className="text-blue-500" /> Neo4j
                  </span>
                </th>
                <th className="text-center px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 w-28">Winner</th>
                <th className="text-center px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 w-20">Speedup</th>
                <th className="px-4 py-3 w-48 hidden md:table-cell">
                  <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">Visual</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {data.queries.map((q) => {
                const mongoBar = q.mongodb_ms ? (q.mongodb_ms / maxTime) * 100 : 0;
                const neo4jBar = q.neo4j_ms ? (q.neo4j_ms / maxTime) * 100 : 0;
                const isMongoWinner = q.winner === "MongoDB";
                const isNeo4jWinner = q.winner === "Neo4J" || q.winner === "Neo4j";
                const winnerStyle = WINNER_STYLES[q.winner] || WINNER_STYLES["Comparable"];

                return (
                  <tr key={q.query} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                    <td className="px-4 py-3">
                      <span className="font-medium text-gray-800 dark:text-gray-200">
                        {formatQueryName(q.query)}
                      </span>
                      {q.description && (
                        <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 hidden xl:block">
                          {q.description}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      {q.category && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">{q.category}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {q.mongodb_ms != null ? (
                        <span className={isMongoWinner ? "text-green-600 font-bold" : "text-gray-600 dark:text-gray-400"}>
                          {q.mongodb_ms.toFixed(1)}ms
                        </span>
                      ) : (
                        <span className="text-gray-300 dark:text-gray-600">---</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {q.neo4j_ms != null ? (
                        <span className={isNeo4jWinner ? "text-blue-600 font-bold" : "text-gray-600 dark:text-gray-400"}>
                          {q.neo4j_ms.toFixed(1)}ms
                        </span>
                      ) : (
                        <span className="text-gray-300 dark:text-gray-600">---</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${winnerStyle}`}>
                        {q.winner}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-sm font-medium text-gray-600 dark:text-gray-400">
                      {q.speedup || "---"}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <div className="space-y-1">
                        {q.mongodb_ms != null && (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] w-4 text-right text-gray-400">M</span>
                            <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="h-2 rounded-full bg-green-500 transition-all"
                                style={{ width: `${mongoBar}%` }}
                              />
                            </div>
                          </div>
                        )}
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] w-4 text-right text-gray-400">N</span>
                          <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="h-2 rounded-full bg-blue-500 transition-all"
                              style={{ width: `${neo4jBar}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data Validation */}
      {data.row_count_mismatches > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border border-amber-200 dark:border-amber-800 flex items-start gap-3">
          <AlertTriangle size={18} className="text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-amber-800 dark:text-amber-300 text-sm">
              Row Count Mismatches: {data.row_count_mismatches}
            </p>
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              Some queries returned different row counts between databases. This may indicate query non-equivalency.
            </p>
          </div>
        </div>
      )}

      {/* Conclusion */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/20 dark:to-green-900/20 rounded-lg p-5 border border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Key Findings</h3>
        <ul className="space-y-1.5 text-sm text-gray-700 dark:text-gray-300">
          <li>
            <strong>MongoDB</strong> excels at range scans on indexed NLP fields
            ({data.mongodb_wins} wins, median {data.mongodb_avg_ms.toFixed(1)}ms).
          </li>
          <li>
            <strong>Neo4j</strong> excels at aggregations, relationship traversal, and complex multi-filter queries
            ({data.neo4j_wins} wins, median {data.neo4j_avg_ms.toFixed(1)}ms).
          </li>
          <li>
            <strong>{data.graph_exclusive_queries} graph-exclusive queries</strong> (multi-hop traversal, pattern matching, network analysis)
            demonstrate capabilities only possible in Neo4j.
          </li>
          <li>
            <strong>Recommendation:</strong> A hybrid approach using MongoDB for document lookups and range scans, and Neo4j for
            relationship-heavy analytics and graph traversals.
          </li>
        </ul>
      </div>
    </div>
  );
};

function formatQueryName(name: string): string {
  return name
    .replace(/^Q\d+_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default DBPerformance;
