import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import StatCard from "../components/StatCard";
import SkeletonLoader from "../components/SkeletonLoader";
import SearchResults from "../components/SearchResults";
import { getDashboardStats } from "../api/dashboard";
import { searchMedications } from "../api/medications";
import { Pill, FlaskConical, Activity } from "lucide-react";
import { DASHBOARD_STATS_KEYS } from "../Constants";
import { toast } from "react-hot-toast";
import SearchBar from "../components/SearchBar";
import type { Medication } from "../interfaces";

const Dashboard: React.FC = () => {
  const PAGE_SIZE = 3;
  const { t } = useTranslation();
  const hasShownError = useRef(false);

  const [stats, setStats] = useState({ medications: 0, ingredients: 0, interactions: 0 });
  const [loading, setLoading] = useState(true);
  const [showResults, setShowResults] = useState(false);
  const [searchResults, setSearchResults] = useState<Medication[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);


  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const data = await getDashboardStats();
        setStats(data);
        hasShownError.current = false;
      } catch (error) {
        if (!hasShownError.current) {
          console.error("Dashboard stats fetch failed:", error);
          toast.error("Failed to load dashboard stats");
          hasShownError.current = true;
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const iconMap = {
    medications: <Pill size={32} />,
    ingredients: <FlaskConical size={32} />,
    interactions: <Activity size={32} />,
  };

  const statsConfig = DASHBOARD_STATS_KEYS.map(({ key, i18nKey }) => ({
    key,
    label: t(i18nKey),
    icon: iconMap[key as keyof typeof iconMap],
  }));

  const fetchMedications = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.trim().length < 2) {
      toast.error(t("search.error.shortSearchTerm", "Término de búsqueda demasiado corto"));
      return;
    }

    setSearchLoading(true);
    setShowResults(true);

    try {
      const allResults = await searchMedications(searchTerm);
      console.log("Fetched medications:", allResults);

      setCurrentPage(1);
      setTotalPages(Math.ceil(allResults.length / PAGE_SIZE));
      
      setSearchResults(allResults);

      if (allResults.length === 0) {
        toast.error(t("search.noResultsFound", "No se encontraron resultados"));
      } else {
        toast.success(
          t("search.resultsFound", "{{count}} resultados encontrados", {
            count: allResults.length,
          })
        );
      }
    } catch (error) {
      console.error("Error searching medications:", error);
      toast.error(t("search.error.searchFailed", "Error al buscar medicamentos"));
      setSearchResults([]);
      setTotalPages(0);
    } finally {
      setSearchLoading(false);
    }
  };


  const handleSearch = (searchTerm: string) => {
    fetchMedications(searchTerm);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };


  const paginatedResults = searchResults.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );


  return (
    <div className="space-y-6">
      <div className="p-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {statsConfig.map(({ key, label, icon }) =>
          loading ? (
            <SkeletonLoader key={key} className="h-28 w-full max-w-sm" />
          ) : (
            <StatCard key={key} value={stats[key as keyof typeof stats]} label={label} icon={icon} />
          )
        )}
      </div>

      <div className="px-6">
        <SearchBar onSearch={handleSearch} />

        {showResults && (
          <SearchResults 
            results={paginatedResults}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            loading={searchLoading}
          />
        )}
      </div>
    </div>
  );
};

export default Dashboard;