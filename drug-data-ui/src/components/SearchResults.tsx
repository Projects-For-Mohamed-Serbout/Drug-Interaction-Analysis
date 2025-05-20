import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Medication } from '../interfaces';

interface SearchResultsProps {
  results: Medication[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  currentPage,
  totalPages,
  onPageChange,
  loading = false
}) => {
  const { t } = useTranslation();

  const renderPagination = () => {
    return (
      <div className="flex justify-center mt-6">
        <nav className="flex items-center space-x-1">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={18} />
          </button>
          
          {Array.from({ length: Math.min(5, totalPages) }).map((_, idx) => {
            let pageNum = 1;
            
            if (totalPages <= 5) {
              pageNum = idx + 1;
            } else if (currentPage <= 3) {
              pageNum = idx + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + idx;
            } else {
              pageNum = currentPage - 2 + idx;
            }
            
            return (
              <button
                key={idx}
                onClick={() => onPageChange(pageNum)}
                className={`px-4 py-2 rounded-md ${
                  pageNum === currentPage
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {pageNum}
              </button>
            );
          })}
          
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight size={18} />
          </button>
        </nav>
      </div>
    );
  };

  return (
    <div className="bg-surface-light dark:bg-gray-800 p-6 rounded-lg shadow-sm mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">
        {t('search.resultsTitle', 'Resultados de la búsqueda')}
      </h2>

      {loading ? (
        <div className="flex justify-center p-8">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : results.length === 0 ? (
        <div className="text-center p-8 text-gray-500 dark:text-gray-400">
          {t('search.noResults', 'No se encontraron resultados')}
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {results.map((med, index) => (
              <div
                key={`${med.id}-${index}`}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                  {med.nombre}
                </h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('search.activeIngredient', 'Principio Activo')}
                    </p>
                    <p className="font-medium text-gray-900 dark:text-gray-200">
                      {med.principio_activo}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('search.nationalCode', 'Código Nacional')}
                    </p>
                    <p className="font-medium text-gray-900 dark:text-gray-200">
                      {med.codigo_nacional}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('search.laboratory', 'Laboratorio')}
                    </p>
                    <p className="font-medium text-gray-900 dark:text-gray-200">
                      {med.laboratorio}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('search.administrationRoute', 'Vía')}
                    </p>
                    <p className="font-medium text-gray-900 dark:text-gray-200">
                      {med.via_administracion}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {totalPages > 1 && renderPagination()}
        </>
      )}
    </div>
  );
};

export default SearchResults;