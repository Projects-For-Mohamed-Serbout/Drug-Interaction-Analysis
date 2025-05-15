import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import StatCard from "../components/StatCard";
import SkeletonLoader from "../components/SkeletonLoader";
import { getDashboardStats } from "../api/dashboard";
import { Pill, FlaskConical, Activity } from "lucide-react";
import { DASHBOARD_STATS_KEYS } from "../Constants";
import { toast } from "react-hot-toast";

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState({ medications: 0, ingredients: 0, interactions: 0 });
  const [loading, setLoading] = useState(true);
  const hasShownError = useRef(false);

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
          toast.error(t("dashboard.error.fetchStats"));
          hasShownError.current = true;
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [t]);

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

  return (
    <div className="p-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {statsConfig.map(({ key, label, icon }) =>
        loading ? (
          <SkeletonLoader key={key} className="h-28 w-full max-w-sm" />
        ) : (
          <StatCard key={key} value={stats[key as keyof typeof stats]} label={label} icon={icon} />
        )
      )}
    </div>
  );
};

export default Dashboard;
