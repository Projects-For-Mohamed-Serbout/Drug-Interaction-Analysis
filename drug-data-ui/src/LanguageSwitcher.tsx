import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { FiChevronDown, FiCheck } from 'react-icons/fi';
import clsx from 'clsx';
import 'flag-icons/css/flag-icons.min.css';

const languages = [
  { code: 'en', name: 'English', flag: 'us' },
  { code: 'es', name: 'Español', flag: 'es' },
];

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  const changeLanguage = (code: string) => {
    if (code !== i18n.language) i18n.changeLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(prev => !prev)}
        className={clsx(
          'flex items-center justify-between w-40 px-4 py-2 rounded-lg border shadow-sm transition',
          'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:shadow-md',
          'focus:outline-none focus:ring-2 focus:ring-primary-light dark:focus:ring-primary-dark'
        )}
      >
        <div className="flex items-center gap-2">
          <span className={`fi fi-${currentLang.flag} w-5 h-3 rounded-sm`} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
            {currentLang.name}
          </span>
        </div>
        <FiChevronDown
          className={clsx(
            'w-4 h-4 transition-transform',
            isOpen && 'rotate-180',
            'text-gray-500 dark:text-gray-400'
          )}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute z-10 mt-2 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden"
          >
            {languages.map(({ code, name, flag }) => {
              const isActive = code === i18n.language;
              return (
                <button
                  key={code}
                  onClick={() => changeLanguage(code)}
                  disabled={isActive}
                  className={clsx(
                    'w-full flex items-center gap-2 px-4 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-primary-light/20 dark:bg-primary-dark/30 text-primary-light dark:text-primary-dark cursor-default'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200',
                    'focus:outline-none'
                  )}
                >
                  <span className={`fi fi-${flag} w-5 h-3 rounded-sm`} />
                  <span>{name}</span>
                  {isActive && <FiCheck className="ml-auto text-primary-light dark:text-primary-dark" />}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default LanguageSwitcher;
