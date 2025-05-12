import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { MENU_ITEMS } from "../Constants";

const Sidebar = () => {
  const { t } = useTranslation();

  return (
    <div className="h-full bg-sidebar-light dark:bg-sidebar-dark text-text-light dark:text-text-dark w-64 font-sans">
      <div className="p-4">
        <h2 className="text-xl font-bold">{t("app.title")}</h2>
      </div>
      <nav className="mt-6">
        {MENU_ITEMS.map((item, index) => (
          <NavLink
            key={index}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 transition-colors duration-200 ${
                isActive
                  ? "bg-sidebarActive-light dark:bg-sidebarActive-dark"
                  : "hover:bg-sidebarHover-light dark:hover:bg-sidebarHover-dark"
              }`
            }
          >
            <item.icon className="w-5 h-5 mr-3" />
            <span>{t(item.i18nKey)}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;
