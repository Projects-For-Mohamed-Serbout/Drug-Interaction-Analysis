import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';
import { MENU_ITEMS } from '../Constants';

const Sidebar = () => {
  const { t } = useTranslation();

  return (
    <aside className="h-full w-64 bg-sidebar-light dark:bg-sidebar-dark text-text-light dark:text-text-dark font-sans">
      <nav className="py-2">
        {MENU_ITEMS.map(({ key, path, icon: Icon, color, i18nKey }) => (
          <NavLink
            key={key}
            to={path}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-4 py-3 transition-colors duration-200',
                isActive
                  ? 'bg-sidebarActive-light dark:bg-sidebarActive-dark font-semibold'
                  : 'hover:bg-sidebarHover-light dark:hover:bg-sidebarHover-dark',
              ].join(' ')
            }
          >
            <Icon className="w-5 h-5" style={{ color }} />
            <span>{t(i18nKey)}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
