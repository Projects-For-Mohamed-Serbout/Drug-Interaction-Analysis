import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div className="flex space-x-2">
      <button
        onClick={() => changeLanguage('en')}
        className={`px-3 py-1 rounded ${
          i18n.language === 'en' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => changeLanguage('es')}
        className={`px-3 py-1 rounded ${
          i18n.language === 'es' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
        }`}
      >
        ES
      </button>
    </div>
  );
};

export default LanguageSwitcher;