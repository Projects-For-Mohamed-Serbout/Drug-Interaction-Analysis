import React from "react";

interface StatCardProps {
  value: number;
  label: string;
  icon?: React.ReactNode;
}

const StatCard: React.FC<StatCardProps> = ({ value, label, icon }) => {
  return (
    <div className="bg-surface-light dark:bg-gray-800 rounded-lg shadow-sm p-6 w-full flex items-center">
      {icon && <div className="mr-4 text-blue-600 dark:text-blue-400">{icon}</div>}
      <div>
        <div className="text-3xl font-bold text-gray-800 dark:text-white">
          {value.toLocaleString()}
        </div>
        <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {label}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
