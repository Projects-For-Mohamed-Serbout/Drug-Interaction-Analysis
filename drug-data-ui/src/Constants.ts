import type { MenuItem } from "./interfaces";

export const MenuKey = {
  Dashboard: "dashboard",
  Medications: "medications",
  Interactions: "interactions",
  ActiveIngredients: "activeIngredients",
  Laboratories: "laboratories",
  DatabasePerformance: "databasePerformance",
  NlpAnalysis: "nlpAnalysis",
  Settings: "settings",
} as const;

export type MenuKey = typeof MenuKey[keyof typeof MenuKey];


export const MENU_ITEMS: MenuItem[] = [
  {
    key: MenuKey.Dashboard,
    path: "/",
    color: "#3B82F6",
    i18nKey: "dashboard.title",
  },
  {
    key: MenuKey.Medications,
    path: "/medications",
    color: "#10B981",
    i18nKey: "medications.title",
  },
  {
    key: MenuKey.Interactions,
    path: "/interactions",
    color: "#F59E0B",
    i18nKey: "interactions.title",
  },
  {
    key: MenuKey.ActiveIngredients,
    path: "/active-ingredients",
    color: "#8B5CF6",
    i18nKey: "activeIngredients.title",
  },
  {
    key: MenuKey.Laboratories,
    path: "/laboratories",
    color: "#EC4899",
    i18nKey: "laboratories.title",
  },
  {
    key: MenuKey.DatabasePerformance,
    path: "/database-performance",
    color: "#F43F5E",
    i18nKey: "databasePerformance.title",
  },
  {
    key: MenuKey.NlpAnalysis,
    path: "/nlp-analysis",
    color: "#0EA5E9",
    i18nKey: "nlpAnalysis.title",
  },
  {
    key: MenuKey.Settings,
    path: "/settings",
    color: "#6B7280",
    i18nKey: "settings.title",
  },
];

