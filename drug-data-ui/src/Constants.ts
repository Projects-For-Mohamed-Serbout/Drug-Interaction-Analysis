import {
  Home,
  Pill,
  Workflow,
  FlaskConical,
  Building2,
  BarChart3,
  BrainCog,
  Settings,
} from "lucide-react";

export const MENU_ITEMS = [
  {
    key: "dashboard",
    path: "/",
    icon: Home,
    i18nKey: "dashboard.title",
  },
  {
    key: "medications",
    path: "/medications",
    icon: Pill,
    i18nKey: "medications.title",
  },
  {
    key: "interactions",
    path: "/interactions",
    icon: Workflow,
    i18nKey: "interactions.title",
  },
  {
    key: "activeIngredients",
    path: "/active-ingredients",
    icon: FlaskConical,
    i18nKey: "activeIngredients.title",
  },
  {
    key: "laboratories",
    path: "/laboratories",
    icon: Building2,
    i18nKey: "laboratories.title",
  },
  {
    key: "databasePerformance",
    path: "/database-performance",
    icon: BarChart3,
    i18nKey: "databasePerformance.title",
  },
  {
    key: "nlpAnalysis",
    path: "/nlp-analysis",
    icon: BrainCog,
    i18nKey: "nlpAnalysis.title",
  },
  {
    key: "settings",
    path: "/settings",
    icon: Settings,
    i18nKey: "settings.title",
  },
];
