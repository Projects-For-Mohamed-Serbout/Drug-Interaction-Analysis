// src/pages/Dashboard.tsx
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import StatCard from "../components/StatCard";
import { getDashboardStats } from "../api/dashboard"

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  const [stats, setStats] = useState({
    medications: 0,
    ingredients: 0,
    interactions: 0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="p-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard value={stats.medications} label={t("dashboard.totalMedications")} />
      <StatCard value={stats.ingredients} label={t("dashboard.activeIngredients")} />
      <StatCard value={stats.interactions} label={t("dashboard.detectedInteractions")} />
    </div>
  );
};

export default Dashboard;
