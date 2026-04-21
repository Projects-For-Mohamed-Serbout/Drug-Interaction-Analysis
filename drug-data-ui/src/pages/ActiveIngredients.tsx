import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { FlaskConical, Search, ChevronLeft, ChevronRight, X } from "lucide-react";
import { toast } from "react-hot-toast";
import { getActiveIngredients } from "../api/activeIngredients";

interface Ingredient {
  _id: string;
  codigo: number;
  codigo_aemps: string;
  nombre: string;
  lista_psicotropo: string | null;
}

interface PaginatedData {
  items: Ingredient[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const ActiveIngredients = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<PaginatedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [activeSearch, setActiveSearch] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await getActiveIngredients(page, pageSize, activeSearch || undefined);
      setData(result);
    } catch {
      toast.error("Error loading active ingredients");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, activeSearch]);

  const handleSearch = () => {
    setPage(1);
    setActiveSearch(search);
  };

  const clearSearch = () => {
    setSearch("");
    setActiveSearch("");
    setPage(1);
  };

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FlaskConical className="text-purple-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("activeIngredients.title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data && `${data.total.toLocaleString()} ingredients`}
            {activeSearch && ` matching "${activeSearch}"`}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search by name..."
            className="w-full pl-10 pr-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
        <button onClick={handleSearch} className="px-4 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
          {t("search.searchButton")}
        </button>
        {activeSearch && (
          <button onClick={clearSearch} className="px-3 py-2.5 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300">
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
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 w-24">Code</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 w-28">AEMPS Code</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300">Name</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-300 w-36">Psychotropic</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" /></td>
                    ))}
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-gray-500 dark:text-gray-400">{t("search.noResults")}</td>
                </tr>
              ) : (
                data?.items.map((item) => (
                  <tr key={item._id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{item.codigo}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-gray-400">{item.codigo_aemps}</td>
                    <td className="px-4 py-3 font-medium text-gray-800 dark:text-gray-200">{item.nombre}</td>
                    <td className="px-4 py-3">
                      {item.lista_psicotropo ? (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                          {item.lista_psicotropo}
                        </span>
                      ) : (
                        <span className="text-gray-300 dark:text-gray-600">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Page {page} of {data.total_pages.toLocaleString()}
            </p>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(1)} disabled={page <= 1} className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300">1</button>
              <button onClick={() => setPage(page - 1)} disabled={page <= 1} className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"><ChevronLeft size={16} /></button>
              <span className="px-3 py-1 text-sm font-medium bg-purple-600 text-white rounded">{page}</span>
              <button onClick={() => setPage(page + 1)} disabled={page >= (data?.total_pages || 1)} className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"><ChevronRight size={16} /></button>
              <button onClick={() => setPage(data?.total_pages || 1)} disabled={page >= (data?.total_pages || 1)} className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300">{data?.total_pages}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveIngredients;
