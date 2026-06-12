import type { MenuItem } from "./interfaces";

export const MenuKey = {
  Dashboard: "dashboard",
  Presentation: "presentation",
  NlpAnalysis: "nlpAnalysis",
  DatabasePerformance: "databasePerformance",
  Interactions: "interactions",
  DataExplorer: "dataExplorer",
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
    key: MenuKey.Presentation,
    path: "/presentation",
    color: "#6366F1",
    i18nKey: "presentation.navTitle",
  },
  {
    key: MenuKey.NlpAnalysis,
    path: "/nlp-analysis",
    color: "#0EA5E9",
    i18nKey: "nlpAnalysis.title",
  },
  {
    key: MenuKey.DatabasePerformance,
    path: "/database-performance",
    color: "#F43F5E",
    i18nKey: "databasePerformance.title",
  },
  {
    key: MenuKey.Interactions,
    path: "/interactions",
    color: "#F59E0B",
    i18nKey: "interactions.title",
  },
  {
    key: MenuKey.DataExplorer,
    path: "/data-explorer",
    color: "#10B981",
    i18nKey: "dataExplorer.title",
  },
];

export const DASHBOARD_STATS_KEYS = [
  {
    key: "medications",
    i18nKey: "dashboard.totalMedications",
  },
  {
    key: "ingredients",
    i18nKey: "dashboard.activeIngredients",
  },
  {
    key: "interactions",
    i18nKey: "dashboard.detectedInteractions",
  },
] as const;

