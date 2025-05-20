import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch?: (searchTerm: string) => void;
  minSearchLength?: number;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch,
  minSearchLength = 2
}) => {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const validateAndSearch = () => {
    if (!searchTerm || searchTerm.trim().length < minSearchLength) {
      setError(t(
        'search.error.shortSearchTerm',
        'El término de búsqueda debe tener al menos {{minLength}} caracteres',
        { minLength: minSearchLength }
      ));
      return;
    }

    setError(null);
    onSearch?.(searchTerm);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      validateAndSearch();
    } else {
      if (error) setError(null);
    }
  };

  return (
    <div className="bg-surface-light dark:bg-gray-800 p-6 rounded-lg shadow-sm mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">
        {t('search.medicationsSearch', 'Búsqueda de Medicamentos')}
      </h2>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-grow relative">
          <input
            type="text"
            className={`w-full rounded-lg border ${
              error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
            } p-3 pl-4 pr-10 text-gray-700 dark:text-gray-200 dark:bg-gray-700 focus:outline-none focus:ring-2`}
            placeholder={t('search.searchPlaceholder', 'Buscar por nombre, principio activo o código nacional...')}
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              if (error) setError(null);
            }}
            onKeyPress={handleKeyPress}
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <Search size={20} />
          </div>
        </div>

        <button
          onClick={validateAndSearch}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
        >
          {t('search.searchButton', 'Buscar')}
        </button>
      </div>

      {error && (
        <div className="mt-2 text-red-500 text-sm">
          {error}
        </div>
      )}
    </div>
  );
};

export default SearchBar;