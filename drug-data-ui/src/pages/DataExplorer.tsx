import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Pill, FlaskConical, Building2 } from "lucide-react";
import Medications from "./Medications";
import ActiveIngredients from "./ActiveIngredients";
import Laboratories from "./Laboratories";

type TabKey = "medications" | "ingredients" | "laboratories";

const TABS: { key: TabKey; icon: typeof Pill; i18nKey: string }[] = [
  { key: "medications", icon: Pill, i18nKey: "medications.title" },
  { key: "ingredients", icon: FlaskConical, i18nKey: "activeIngredients.title" },
  { key: "laboratories", icon: Building2, i18nKey: "laboratories.title" },
];

/**
 * Data Explorer — collapses the three reference catalogues (medications,
 * active ingredients, laboratories) behind a single tabbed page so they no
 * longer compete with the headline pages in the main navigation.
 */
const DataExplorer = () => {
  const { t } = useTranslation();
  const [tab, setTab] = useState<TabKey>("medications");

  return (
    <div>
      <div className="px-6 pt-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">{t("dataExplorer.title")}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">{t("dataExplorer.description")}</p>

        {/* tab bar */}
        <div className="flex gap-1 mt-4 border-b border-gray-200 dark:border-gray-700">
          {TABS.map(({ key, icon: Icon, i18nKey }) => {
            const active = tab === key;
            return (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={[
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                  active
                    ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200",
                ].join(" ")}
              >
                <Icon size={16} />
                {t(i18nKey)}
              </button>
            );
          })}
        </div>
      </div>

      {/* active panel — each child renders its own padding/header */}
      {tab === "medications" && <Medications />}
      {tab === "ingredients" && <ActiveIngredients />}
      {tab === "laboratories" && <Laboratories />}
    </div>
  );
};

export default DataExplorer;
