import React, { useState, type ReactNode } from 'react';
import Sidebar from '../components/Sidebar';
import LanguageSwitcher from '../LanguageSwitcher';
import { useTranslation } from 'react-i18next';
import { Menu, X } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

interface LayoutProps {
  children: ReactNode;
}

const MobileSidebar: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 md:hidden">
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
        aria-hidden="true"
      />
      <aside className="relative w-full max-w-xs bg-sidebar-light dark:bg-sidebar-dark h-full shadow text-text-light dark:text-text-dark">
        <div className="absolute top-0 right-0 p-2">
          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-border-light dark:focus:ring-border-dark"
          >
            <span className="sr-only">{t('sidebar.close')}</span>
            <X className="h-6 w-6 text-text-light dark:text-text-dark" aria-hidden="true" />
          </button>
        </div>
        <Sidebar />
      </aside>
    </div>
  );
};

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { t } = useTranslation();

  return (
    <div className="flex flex-col h-screen bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark transition-colors duration-300">
      <header className="bg-navbar-light dark:bg-navbar-dark text-text-light dark:text-text-dark px-4 py-3 flex justify-between items-center shadow">
        <h1 className="text-lg font-semibold">{t('app.systemTitle')}</h1>
        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden md:block bg-sidebar-light dark:bg-sidebar-dark border-r border-border-light dark:border-border-dark text-text-light dark:text-text-dark">
          <Sidebar />
        </aside>

        <MobileSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        <div className="flex flex-col flex-1 w-0 overflow-hidden">
          <div className="md:hidden p-2">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="h-10 w-10 inline-flex items-center justify-center rounded-md text-text-light dark:text-text-dark hover:text-primary-light dark:hover:text-primary-dark focus:outline-none focus:ring-2 focus:ring-inset focus:ring-border-light dark:focus:ring-border-dark"
            >
              <span className="sr-only">{t('sidebar.open')}</span>
              <Menu className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          <main className="flex-1 overflow-y-auto focus:outline-none p-4">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;
