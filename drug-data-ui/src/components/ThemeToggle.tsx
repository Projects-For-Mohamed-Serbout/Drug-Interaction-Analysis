import React, { useEffect, useState, useCallback } from 'react';
import { Moon, Sun, Monitor } from 'lucide-react';

type ThemeOption = 'light' | 'dark' | 'system';

const themeOptions: { value: ThemeOption; icon: React.ElementType; label: string }[] = [
  { value: 'system', icon: Monitor, label: 'System' },
  { value: 'light', icon: Sun, label: 'Light' },
  { value: 'dark', icon: Moon, label: 'Dark' },
];

const applyTheme = (mode: ThemeOption) => {
  const root = document.documentElement;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  const isDark = mode === 'dark' || (mode === 'system' && prefersDark);
  root.classList.toggle('dark', isDark);
  root.classList.toggle('light', !isDark);
};

const ThemeToggle: React.FC = () => {
  const [theme, setTheme] = useState<ThemeOption>(
    () => (localStorage.getItem('theme') as ThemeOption) || 'system'
  );

  const handleSystemChange = useCallback(() => {
    if (theme === 'system') applyTheme('system');
  }, [theme]);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem('theme', theme);

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener?.('change', handleSystemChange);

    return () => {
      mediaQuery.removeEventListener?.('change', handleSystemChange);
    };
  }, [theme, handleSystemChange]);

  return (
    <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-full p-1 space-x-1">
      {themeOptions.map(({ value, icon: Icon, label }) => {
        const isActive = theme === value;
        return (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={`flex items-center justify-center w-10 h-10 rounded-full transition-all 
              ${isActive ? 'bg-white dark:bg-gray-600 shadow-md' : 'hover:bg-gray-200 dark:hover:bg-gray-700'}
              text-gray-600 dark:text-gray-300`}
            aria-label={`Switch to ${label} mode`}
          >
            <Icon className={`w-5 h-5 ${isActive ? 'text-black dark:text-white' : 'text-gray-500 dark:text-gray-400'}`} />
          </button>
        );
      })}
    </div>
  );
};

export default ThemeToggle;
