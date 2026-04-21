import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Activity, ChevronLeft, ChevronRight, Filter, X, AlertTriangle, Info } from "lucide-react";
import { toast } from "react-hot-toast";
import { getInteractions } from "../api/interactions";

interface Interaction {
  _id: string;
  medicamento_origen: {
    cod_nacion: string;
    nombre: string;
    atc: string;
  };
  medicamento_destino: {
    atc: string;
    nombre: string;
  };
  interaccion: {
    efecto: string;
    recomendacion: string;
    nlp?: {
      severidad?: string;
      severidad_confianza?: number;
      tipo?: string;
      categoria_efecto?: string;
      mecanismo?: string;
      enzimas?: string[];
      transportadores?: string[];
      confianza_general?: number;
    };
  };
}

interface PaginatedData {
  items: Interaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const SEVERITY_OPTIONS = [
  { value: "", label: "All Severities" },
  { value: "contraindicated", label: "Contraindicated" },
  { value: "severe", label: "Severe" },
  { value: "moderate", label: "Moderate" },
  { value: "mild", label: "Mild" },
  { value: "unknown", label: "Unknown" },
];

const TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "cardiac", label: "Cardiac" },
  { value: "metabolic", label: "Metabolic" },
  { value: "hemorrhagic", label: "Hemorrhagic" },
  { value: "gastrointestinal", label: "Gastrointestinal" },
  { value: "muscular", label: "Muscular" },
  { value: "toxicity", label: "Toxicity" },
  { value: "renal", label: "Renal" },
  { value: "cns", label: "CNS" },
  { value: "hepatic", label: "Hepatic" },
  { value: "efficacy_reduction", label: "Efficacy Reduction" },
  { value: "efficacy_increase", label: "Efficacy Increase" },
  { value: "other", label: "Other" },
];

const SEVERITY_COLORS: Record<string, string> = {
  contraindicated: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  severe: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  moderate: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  mild: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  unknown: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
};

const TYPE_COLORS: Record<string, string> = {
  cardiac: "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800",
  metabolic: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800",
  hemorrhagic: "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800",
  gastrointestinal: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
  muscular: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800",
  toxicity: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800",
  renal: "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-800",
  cns: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800",
  hepatic: "bg-lime-50 text-lime-700 border-lime-200 dark:bg-lime-900/30 dark:text-lime-300 dark:border-lime-800",
};

const Interactions = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<PaginatedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [severity, setSeverity] = useState("");
  const [type, setType] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await getInteractions(page, pageSize, severity || undefined, type || undefined);
      setData(result);
    } catch {
      toast.error("Error loading interactions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, severity, type]);

  const handleFilterChange = (filterType: "severity" | "type", value: string) => {
    setPage(1);
    if (filterType === "severity") setSeverity(value);
    else setType(value);
  };

  const clearFilters = () => {
    setSeverity("");
    setType("");
    setPage(1);
  };

  const hasFilters = severity || type;

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Activity className="text-amber-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
            {t("interactions.title")}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data && `${data.total.toLocaleString()} interactions`}
            {hasFilters && " (filtered)"}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border dark:border-gray-700">
        <Filter size={16} className="text-gray-400" />

        <select
          value={severity}
          onChange={(e) => handleFilterChange("severity", e.target.value)}
          className="px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          {SEVERITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        <select
          value={type}
          onChange={(e) => handleFilterChange("type", e.target.value)}
          className="px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
          >
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {/* Interaction Cards */}
      <div className="space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700">
              <div className="space-y-3">
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full" />
              </div>
            </div>
          ))
        ) : data?.items.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            No interactions found with these filters.
          </div>
        ) : (
          data?.items.map((interaction) => {
            const nlp = interaction.interaccion.nlp;
            const isExpanded = expandedId === interaction._id;

            return (
              <div
                key={interaction._id}
                className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden"
              >
                {/* Main Row */}
                <div
                  className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                  onClick={() => setExpandedId(isExpanded ? null : interaction._id)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* Drug Names */}
                      <div className="flex items-center gap-2 text-sm mb-1">
                        <span className="font-semibold text-blue-600 dark:text-blue-400 truncate">
                          {interaction.medicamento_origen.nombre}
                        </span>
                        <span className="text-gray-400 flex-shrink-0">→</span>
                        <span className="font-medium text-gray-700 dark:text-gray-300 truncate">
                          {interaction.medicamento_destino.nombre}
                        </span>
                      </div>

                      {/* Effect */}
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {interaction.interaccion.efecto}
                      </p>
                    </div>

                    {/* NLP Badges */}
                    <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                      {nlp?.severidad && (
                        <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${SEVERITY_COLORS[nlp.severidad] || SEVERITY_COLORS.unknown}`}>
                          {nlp.severidad.toUpperCase()}
                        </span>
                      )}
                      {nlp?.tipo && (
                        <span className={`px-2 py-0.5 text-xs font-medium rounded border ${TYPE_COLORS[nlp.tipo] || "bg-gray-50 text-gray-600 border-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600"}`}>
                          {nlp.tipo}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-850 p-4 space-y-4">
                    {/* Recommendation */}
                    {interaction.interaccion.recomendacion && (
                      <div className="flex items-start gap-2">
                        <AlertTriangle size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Recommendation</p>
                          <p className="text-sm text-gray-700 dark:text-gray-300">
                            {interaction.interaccion.recomendacion}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* NLP Analysis Detail */}
                    {nlp && (
                      <div className="flex items-start gap-2">
                        <Info size={16} className="text-blue-500 mt-0.5 flex-shrink-0" />
                        <div className="w-full">
                          <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            NLP Analysis
                          </p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <NlpField label="Severity" value={nlp.severidad} confidence={nlp.severidad_confianza} />
                            <NlpField label="Type" value={nlp.tipo} />
                            <NlpField label="Effect Category" value={nlp.categoria_efecto} />
                            <NlpField label="Mechanism" value={nlp.mecanismo} />
                          </div>

                          {/* Confidence Bar */}
                          {nlp.confianza_general != null && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                                <span>Overall Confidence</span>
                                <span className="font-medium">{(nlp.confianza_general * 100).toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all ${
                                    nlp.confianza_general >= 0.7
                                      ? "bg-green-500"
                                      : nlp.confianza_general >= 0.5
                                      ? "bg-yellow-500"
                                      : "bg-red-500"
                                  }`}
                                  style={{ width: `${nlp.confianza_general * 100}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {/* Enzymes & Transporters */}
                          {(nlp.enzimas?.length || nlp.transportadores?.length) ? (
                            <div className="mt-3 flex flex-wrap gap-1.5">
                              {nlp.enzimas?.map((e, i) => (
                                <span key={i} className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded">
                                  {e}
                                </span>
                              ))}
                              {nlp.transportadores?.map((t, i) => (
                                <span key={i} className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 rounded">
                                  {t}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    )}

                    {/* ATC Codes */}
                    <div className="flex gap-4 text-xs text-gray-400">
                      <span>Source ATC: <span className="font-mono">{interaction.medicamento_origen.atc}</span></span>
                      <span>Target ATC: <span className="font-mono">{interaction.medicamento_destino.atc}</span></span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white dark:bg-gray-800 px-4 py-3 rounded-lg border dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Page {data.page} of {data.total_pages.toLocaleString()}
            {" · "}{data.total.toLocaleString()} total
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(1)}
              disabled={page <= 1}
              className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
            >
              1
            </button>
            <button
              onClick={() => setPage(page - 1)}
              disabled={page <= 1}
              className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="px-3 py-1 text-sm font-medium bg-blue-600 text-white rounded">
              {page}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= (data?.total_pages || 1)}
              className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
            >
              <ChevronRight size={16} />
            </button>
            <button
              onClick={() => setPage(data?.total_pages || 1)}
              disabled={page >= (data?.total_pages || 1)}
              className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
            >
              {data?.total_pages}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const NlpField = ({
  label,
  value,
  confidence,
}: {
  label: string;
  value?: string;
  confidence?: number;
}) => (
  <div>
    <p className="text-xs text-gray-400 dark:text-gray-500">{label}</p>
    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
      {value || "—"}
      {confidence != null && (
        <span className="text-xs text-gray-400 ml-1">({(confidence * 100).toFixed(0)}%)</span>
      )}
    </p>
  </div>
);

export default Interactions;
