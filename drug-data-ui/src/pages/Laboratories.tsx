import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Building2, Search, ChevronLeft, ChevronRight, X, MapPin } from "lucide-react";
import { toast } from "react-hot-toast";
import { getLaboratories } from "../api/laboratories";

interface Laboratory {
  _id: string;
  codigo: number;
  nombre: string;
  direccion: string | null;
  codigo_postal: string | null;
  localidad: string | null;
  cif: string | null;
}

interface PaginatedData {
  items: Laboratory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const Laboratories = () => {
  const { t } = useTranslation();
  const [data, setData] = useState<PaginatedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState("");
  const [activeSearch, setActiveSearch] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await getLaboratories(page, pageSize, activeSearch || undefined);
      setData(result);
    } catch {
      toast.error("Error loading laboratories");
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
        <Building2 className="text-pink-500" size={28} />
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("laboratories.title")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data && `${data.total.toLocaleString()} laboratories`}
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
            placeholder="Search by laboratory name..."
            className="w-full pl-10 pr-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
        <button onClick={handleSearch} className="px-4 py-2.5 bg-pink-600 text-white rounded-lg hover:bg-pink-700">
          {t("search.searchButton")}
        </button>
        {activeSearch && (
          <button onClick={clearSearch} className="px-3 py-2.5 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:border-gray-600 dark:text-gray-300">
            <X size={18} />
          </button>
        )}
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700">
              <div className="space-y-3">
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full" />
              </div>
            </div>
          ))
        ) : data?.items.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
            {t("search.noResults")}
          </div>
        ) : (
          data?.items.map((lab) => (
            <div
              key={lab._id}
              className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm leading-tight">
                  {lab.nombre}
                </h3>
                <span className="text-xs font-mono text-gray-400 dark:text-gray-500 flex-shrink-0 ml-2">
                  #{lab.codigo}
                </span>
              </div>

              {(lab.direccion || lab.localidad) && (
                <div className="flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400 mb-2">
                  <MapPin size={12} className="mt-0.5 flex-shrink-0" />
                  <span>
                    {[lab.direccion, lab.codigo_postal, lab.localidad].filter(Boolean).join(", ")}
                  </span>
                </div>
              )}

              {lab.cif && (
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  CIF: <span className="font-mono">{lab.cif}</span>
                </p>
              )}
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white dark:bg-gray-800 px-4 py-3 rounded-lg border dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Page {page} of {data.total_pages.toLocaleString()}
          </p>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage(1)} disabled={page <= 1} className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300">1</button>
            <button onClick={() => setPage(page - 1)} disabled={page <= 1} className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"><ChevronLeft size={16} /></button>
            <span className="px-3 py-1 text-sm font-medium bg-pink-600 text-white rounded">{page}</span>
            <button onClick={() => setPage(page + 1)} disabled={page >= (data?.total_pages || 1)} className="p-1 rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300"><ChevronRight size={16} /></button>
            <button onClick={() => setPage(data?.total_pages || 1)} disabled={page >= (data?.total_pages || 1)} className="px-2 py-1 text-sm rounded border dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-300">{data?.total_pages}</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Laboratories;
