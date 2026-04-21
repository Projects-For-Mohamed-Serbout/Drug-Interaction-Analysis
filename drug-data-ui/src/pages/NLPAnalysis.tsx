import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Brain, CheckCircle, Clock, BarChart3, Target, Layers, Cog } from "lucide-react";
import { toast } from "react-hot-toast";
import { getNlpStatistics } from "../api/nlpAnalysis";

interface DistributionItem {
  label: string;
  count: number;
}

interface NlpStats {
  total_interactions: number;
  processed: number;
  unprocessed: number;
  processing_rate: number;
  severity_distribution: DistributionItem[];
  type_distribution: DistributionItem[];
  effect_category_distribution: DistributionItem[];
  mechanism_distribution: DistributionItem[];
  average_confidence: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  contraindicated: "#EF4444",
  severe: "#F97316",
  moderate: "#EAB308",
  mild: "#22C55E",
  unknown: "#9CA3AF",
};

const TYPE_COLORS: Record<string, string> = {
  cardiac: "#EF4444",
  metabolic: "#8B5CF6",
  hemorrhagic: "#F43F5E",
  gastrointestinal: "#F59E0B",
  muscular: "#6366F1",
  toxicity: "#EA580C",
  renal: "#14B8A6",
  cns: "#3B82F6",
  hepatic: "#84CC16",
  efficacy_reduction: "#64748B",
  efficacy_increase: "#10B981",
  other: "#9CA3AF",
};

const EFFECT_COLORS: Record<string, string> = {
  Cardiovascular: "#EF4444",
  Metabolic: "#8B5CF6",
  Gastrointestinal: "#F59E0B",
  Pharmacological: "#3B82F6",
  Musculoskeletal: "#6366F1",
  Toxicological: "#EA580C",
  Hematological: "#F43F5E",
  Renal: "#14B8A6",
  Neurological: "#0EA5E9",
  Hepatic: "#84CC16",
  Unclassified: "#9CA3AF",
};

const MECHANISM_COLORS: Record<string, string> = {
  pharmacodynamic: "#3B82F6",
  pharmacokinetic: "#8B5CF6",
  mixed: "#F59E0B",
  unknown: "#9CA3AF",
};

const AnalisisNLP = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState<NlpStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getNlpStatistics();
        setStats(data);
      } catch {
        toast.error("Error loading NLP statistics");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="flex items-center gap-3 mb-6">
          <Brain className="text-cyan-500" size={28} />
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("nlpAnalysis.title")}</h1>
        </div>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-48 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const confidencePercent = (stats.average_confidence * 100).toFixed(1);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Brain className="text-cyan-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("nlpAnalysis.title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("nlpAnalysis.description")}</p>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatBox
          icon={<BarChart3 size={20} />}
          label="Total Interactions"
          value={stats.total_interactions.toLocaleString()}
          color="text-blue-500"
        />
        <StatBox
          icon={<CheckCircle size={20} />}
          label="Processed"
          value={`${stats.processed.toLocaleString()} (${stats.processing_rate}%)`}
          color="text-green-500"
        />
        <StatBox
          icon={<Clock size={20} />}
          label="Unprocessed"
          value={stats.unprocessed.toLocaleString()}
          color="text-orange-500"
        />
        <StatBox
          icon={<Target size={20} />}
          label="Avg. Confidence"
          value={`${confidencePercent}%`}
          color="text-cyan-500"
          extra={
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  stats.average_confidence >= 0.7
                    ? "bg-green-500"
                    : stats.average_confidence >= 0.5
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${stats.average_confidence * 100}%` }}
              />
            </div>
          }
        />
      </div>

      {/* Processing Progress */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 shadow-sm">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Processing Progress</h3>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
          <div
            className="h-4 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all flex items-center justify-center"
            style={{ width: `${stats.processing_rate}%` }}
          >
            <span className="text-[10px] font-bold text-white">{stats.processing_rate}%</span>
          </div>
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>0</span>
          <span>{stats.total_interactions.toLocaleString()}</span>
        </div>
      </div>

      {/* Distribution Grids */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity */}
        <DistributionCard
          title="Severity Distribution"
          icon={<Layers size={18} />}
          items={stats.severity_distribution}
          total={stats.processed}
          colorMap={SEVERITY_COLORS}
        />

        {/* Interaction Type */}
        <DistributionCard
          title="Interaction Type Distribution"
          icon={<BarChart3 size={18} />}
          items={stats.type_distribution}
          total={stats.processed}
          colorMap={TYPE_COLORS}
        />

        {/* Effect Category */}
        <DistributionCard
          title="Effect Category Distribution"
          icon={<Target size={18} />}
          items={stats.effect_category_distribution}
          total={stats.processed}
          colorMap={EFFECT_COLORS}
        />

        {/* Mechanism */}
        <DistributionCard
          title="Mechanism Distribution"
          icon={<Cog size={18} />}
          items={stats.mechanism_distribution}
          total={stats.processed}
          colorMap={MECHANISM_COLORS}
        />
      </div>
    </div>
  );
};

/* ============================================================
   Reusable Components
   ============================================================ */

const StatBox = ({
  icon,
  label,
  value,
  color,
  extra,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  extra?: React.ReactNode;
}) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border dark:border-gray-700 shadow-sm">
    <div className="flex items-center gap-2 mb-2">
      <span className={color}>{icon}</span>
      <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{label}</span>
    </div>
    <p className="text-xl font-bold text-gray-800 dark:text-white">{value}</p>
    {extra}
  </div>
);

const DistributionCard = ({
  title,
  icon,
  items,
  total,
  colorMap,
}: {
  title: string;
  icon: React.ReactNode;
  items: DistributionItem[];
  total: number;
  colorMap: Record<string, string>;
}) => {
  const maxCount = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <span className="text-gray-500">{icon}</span>
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">{title}</h3>
      </div>
      <div className="p-4 space-y-2.5">
        {items.map((item) => {
          const pct = total > 0 ? ((item.count / total) * 100).toFixed(1) : "0";
          const barWidth = (item.count / maxCount) * 100;
          const color = colorMap[item.label] || "#9CA3AF";

          return (
            <div key={item.label} className="group">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                  <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {item.label.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-gray-500 dark:text-gray-400">{item.count.toLocaleString()}</span>
                  <span className="font-medium text-gray-700 dark:text-gray-300 w-14 text-right">{pct}%</span>
                </div>
              </div>
              <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{ width: `${barWidth}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AnalisisNLP;
