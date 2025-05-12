import { useEffect, useState } from 'react';

type ThemeOption = 'light' | 'dark' | 'system';

const ThemeToggle = () => {
  const [theme, setTheme] = useState<ThemeOption>(() => {
    return (localStorage.getItem('theme') as ThemeOption) || 'system';
  });

  useEffect(() => {
    const root = window.document.documentElement;

    const applyTheme = (mode: ThemeOption) => {
      if (mode === 'dark' || (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    applyTheme(theme);
    localStorage.setItem('theme', theme);

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') applyTheme('system');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  return (
    <select
      value={theme}
      onChange={(e) => setTheme(e.target.value as ThemeOption)}
      className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 text-sm text-black dark:text-white"
    >
      <option value="system">🌐 System</option>
      <option value="light">☀️ Light</option>
      <option value="dark">🌙 Dark</option>
    </select>
  );
};

export default ThemeToggle;
