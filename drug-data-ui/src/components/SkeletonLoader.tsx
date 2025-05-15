import React from 'react';

interface SkeletonLoaderProps {
  className?: string;
}

const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ className }) => {
  return (
    <div
      className={`animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700 ${className}`}
    />
  );
};

export default SkeletonLoader;
