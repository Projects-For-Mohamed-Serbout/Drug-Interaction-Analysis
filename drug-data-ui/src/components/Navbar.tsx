import React from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '../LanguageSwitcher';
import ThemeToggle from './ThemeToggle';

const Navbar: React.FC = () => {
  const { t } = useTranslation();

  return (
    <header className="h-navbar bg-navbar-light dark:bg-navbar-dark text-text-light dark:text-text-dark px-4 py-3 flex justify-between items-center shadow">
      <div className="flex items-center gap-3 max-w-full overflow-hidden">
        <img
          src="/logo.png"
          alt="App Logo"
          className="h-12 w-auto max-h-14 object-contain"
        />
        <h1 className="text-xl font-semibold leading-tight truncate">
          {t('app.systemTitle')}
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Navbar;
