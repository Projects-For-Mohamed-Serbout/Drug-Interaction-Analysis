import React from "react";

interface StatCardProps {
  value: number;
  label: string;
}

const StatCard: React.FC<StatCardProps> = ({ value, label }) => {
  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-2xl shadow p-6 w-full max-w-sm">
      <div className="text-3xl font-bold text-text-light dark:text-text-dark">
        {value.toLocaleString()}
      </div>
      <div className="mt-2 text-sm text-muted-light dark:text-muted-dark">
        {label}
      </div>
    </div>
  );
};

export default StatCard;
