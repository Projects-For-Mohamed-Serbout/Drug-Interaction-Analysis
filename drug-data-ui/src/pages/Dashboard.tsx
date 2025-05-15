import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import StatCard from "../components/StatCard";
import SkeletonLoader from "../components/SkeletonLoader";
import { getDashboardStats } from "../api/dashboard";
import { Pill, FlaskConical, Activity } from "lucide-react";

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  const [stats, setStats] = useState({
    medications: 0,
    ingredients: 0,
    interactions: 0,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statsConfig = [
    {
      key: "medications",
      label: t("dashboard.totalMedications"),
      icon: <Pill size={32} />,
    },
    {
      key: "ingredients",
      label: t("dashboard.activeIngredients"),
      icon: <FlaskConical size={32} />,
    },
    {
      key: "interactions",
      label: t("dashboard.detectedInteractions"),
      icon: <Activity size={32} />,
    },
  ];

  return (
    <div className="p-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {statsConfig.map(({ key, label, icon }) => (
        loading ? (
          <SkeletonLoader key={key} className="h-28 w-full max-w-sm" />
        ) : (
          <StatCard
            key={key}
            value={stats[key as keyof typeof stats]}
            label={label}
            icon={icon}
          />
        )
      ))}
    </div>
  );
};

export default Dashboard;
