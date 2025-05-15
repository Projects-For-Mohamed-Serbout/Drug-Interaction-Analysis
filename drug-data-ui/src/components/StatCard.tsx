import React from "react";

interface StatCardProps {
  value: number;
  label: string;
  icon?: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ value, label, icon }) => {
  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-2xl shadow p-6 w-full max-w-sm flex items-center">
      {icon && <div className="mr-4">{icon}</div>}
      <div>
        <div className="text-3xl font-bold text-text-light dark:text-text-dark">
          {value.toLocaleString()}
        </div>
        <div className="mt-2 text-sm text-muted-light dark:text-muted-dark">
          {label}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
