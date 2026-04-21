import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pill, Search, ChevronLeft, ChevronRight, ArrowUpDown, Eye, X } from "lucide-react";
import { toast } from "react-hot-toast";
import { getMedications, getMedicationById } from "../api/medicationDetail";
import { searchMedications } from "../api/medications";
import type { Medication } from "../interfaces";

interface PaginatedData {
  items: Medication[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const Medications = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<PaginatedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState(false);
  const [searchResults, setSearchResults] = useState<Medication[]>([]);
  const [detail, setDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await getMedications(page, pageSize, "nombre_comercial", sortOrder);
      setData(result);
    } catch {
      toast.error(t("medications.error", "Error loading medications"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!searchMode) fetchData();
  }, [page, sortOrder, searchMode]);

  const handleSearch = async () => {
    if (searchQuery.trim().length < 2) return;
    setSearchMode(true);
    setLoading(true);
    try {
      const results = await searchMedications(searchQuery);
      setSearchResults(results);
      toast.success(`${results.length} results found`);
    } catch {
      toast.error("Search failed");
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchMode(false);
    setSearchResults([]);
    setPage(1);
  };

  const openDetail = async (codNacion: string) => {
    setDetailLoading(true);
    try {
      const drug = await getMedicationById(codNacion);
      setDetail(drug);
    } catch {
      toast.error("Failed to load medication detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const displayItems = searchMode ? searchResults : (data?.items || []);
  const totalPages = searchMode ? 1 : (data?.total_pages || 1);

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Pill className="text-green-500" size={28} />
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
              {t("medications.title")}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {data && !searchMode && `${data.total.toLocaleString()} ${t("medications.title").toLowerCase()}`}
              {searchMode && `${searchResults.length} results for "${searchQuery}"`}
            </p>
          </div>
        </div>

        <button
          onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
          className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300"
        >
          <ArrowUpDown size={14} />
          {sortOrder === "asc" ? "A → Z" : "Z → A"}
        </button>
      </div>

      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder={t("search.searchPlaceholder")}
            className="w-full pl-10 pr-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {t("search.searchButton")}
        </button>
        {searchMode && (
          <button
            onClick={clearSearch}
            className="px-3 py-2.5 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">
                  {t("search.nationalCode")}
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">
                  {t("medications.table.name")}
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden md:table-cell">
                  {t("search.activeIngredient")}
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden lg:table-cell">
                  {t("search.laboratory")}
                </th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 hidden lg:table-cell">
                  {t("search.administrationRoute")}
                </th>
                <th className="px-4 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : displayItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500 dark:text-gray-400">
                    {t("search.noResults")}
                  </td>
                </tr>
              ) : (
                displayItems.map((med) => (
                  <tr
                    key={med.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">
                      {med.codigo_nacional}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200 max-w-xs truncate">
                      {med.nombre}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 hidden md:table-cell">
                      {med.principio_activo}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 hidden lg:table-cell max-w-[200px] truncate">
                      {med.laboratorio}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 hidden lg:table-cell">
                      {med.via_administracion}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => openDetail(med.codigo_nacional)}
                        className="text-blue-500 hover:text-blue-700"
                        title="View detail"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!searchMode && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Page {page} of {totalPages.toLocaleString()}
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
                disabled={page >= totalPages}
                className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
              >
                <ChevronRight size={16} />
              </button>
              <button
                onClick={() => setPage(totalPages)}
                disabled={page >= totalPages}
                className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"
              >
                {totalPages}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {(detail || detailLoading) && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-800 dark:text-white">
                {detailLoading ? "Loading..." : detail?.nombre_comercial}
              </h2>
              <button
                onClick={() => setDetail(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>
            {detailLoading ? (
              <div className="flex justify-center p-12">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : detail && (
              <div className="p-5 space-y-4">
                {/* Basic Info */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <DetailField label={t("search.nationalCode")} value={detail.cod_nacion} />
                  <DetailField label="NRO Definitivo" value={detail.nro_definitivo} />
                  <DetailField label="Dosificacion" value={detail.dosificacion} />
                  <DetailField label={t("search.laboratory")} value={detail.laboratorio_titular?.nombre} />
                  <DetailField label="ATC" value={detail.atc?.codigo} />
                  <DetailField label="ATC Description" value={detail.atc?.descripcion} />
                </div>

                {/* Classification */}
                {detail.clasificacion && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Classification</h3>
                    <div className="flex flex-wrap gap-2">
                      {detail.clasificacion.generico && <Badge text="Generic" color="blue" />}
                      {detail.clasificacion.biosimilar && <Badge text="Biosimilar" color="purple" />}
                      {detail.clasificacion.requiere_receta && <Badge text="Prescription" color="red" />}
                      {detail.clasificacion.uso_hospitalario && <Badge text="Hospital Use" color="orange" />}
                      {detail.clasificacion.afecta_conduccion && <Badge text="Affects Driving" color="yellow" />}
                      {detail.clasificacion.psicotropo && <Badge text="Psychotropic" color="pink" />}
                      {detail.clasificacion.estupefaciente && <Badge text="Narcotic" color="red" />}
                      {detail.comercializado && <Badge text="Commercialized" color="green" />}
                    </div>
                  </div>
                )}

                {/* Pharmaceutical Forms */}
                {detail.formas_farmaceuticas?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Composition
                    </h3>
                    {detail.formas_farmaceuticas[0].composicion?.map((comp: any, i: number) => (
                      <div key={i} className="text-sm text-gray-600 dark:text-gray-400">
                        {comp.principio_activo?.nombre}
                        {comp.dosis ? ` — ${comp.dosis} ${comp.unidad_dosis || ""}` : ""}
                      </div>
                    ))}
                  </div>
                )}

                {/* Interactions count */}
                {detail.atc?.interacciones?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Interactions
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {detail.atc.interacciones.length} registered interactions
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const DetailField = ({ label, value }: { label: string; value?: string }) => (
  <div>
    <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
    <p className="font-medium text-gray-800 dark:text-gray-200 text-sm">{value || "—"}</p>
  </div>
);

const Badge = ({ text, color }: { text: string; color: string }) => {
  const colors: Record<string, string> = {
    blue: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
    green: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
    red: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
    orange: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
    yellow: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
    purple: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
    pink: "bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300",
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[color] || colors.blue}`}>
      {text}
    </span>
  );
};

export default Medications;
