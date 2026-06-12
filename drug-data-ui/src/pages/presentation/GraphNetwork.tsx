import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Network } from "lucide-react";
import { getInteractions, getInteractionsForDrug } from "../../api/interactions";
import EgoGraph, { type Target } from "./EgoGraph";

const SEV_ORDER = ["contraindicated", "severe", "moderate", "mild", "unknown"];

interface RawInteraction {
  medicamento_origen?: { nombre?: string; cod_nacion?: string };
  medicamento_destino?: { nombre?: string };
  interaccion?: { nlp?: { severidad?: string } };
}
interface EgoNet {
  center: string;
  total: number;
  targets: Target[];
}

/**
 * Self-contained static ego-network: discovers a well-connected drug from the
 * contraindicated interactions, fetches its full network and renders it with
 * the shared <EgoGraph>. Anchors the graph-database story in Part 3.
 */
const GraphNetwork = () => {
  const { t } = useTranslation();
  const [net, setNet] = useState<EgoNet | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        // Step 1 — discover a richly-connected centre drug.
        const page = await getInteractions(1, 60, "contraindicated");
        const items: RawInteraction[] = page?.items ?? [];
        const freq = new Map<string, { cod: string; name: string; n: number }>();
        for (const it of items) {
          const cod = it.medicamento_origen?.cod_nacion;
          const name = it.medicamento_origen?.nombre;
          if (!cod || !name) continue;
          const cur = freq.get(cod) ?? { cod, name, n: 0 };
          cur.n += 1;
          freq.set(cod, cur);
        }
        const best = [...freq.values()].sort((a, b) => b.n - a.n)[0];
        if (!best) {
          setLoading(false);
          return;
        }

        // Step 2 — fetch that drug's full interaction network.
        const all: RawInteraction[] = (await getInteractionsForDrug(best.cod)) ?? [];
        const targets: Target[] = all
          .map((it) => ({
            name: it.medicamento_destino?.nombre ?? "",
            severity: it.interaccion?.nlp?.severidad ?? "unknown",
          }))
          .filter((x) => x.name)
          .sort((a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity));

        setNet({ center: best.name, total: targets.length, targets });
      } catch {
        setNet(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border dark:border-gray-700 p-5">
        <div className="h-72 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center text-sm text-gray-400">
          {t("presentation.graph.loading")}
        </div>
      </div>
    );
  }

  if (!net || net.targets.length === 0) {
    return (
      <div className="rounded-xl border dark:border-gray-700 p-5 text-sm text-gray-400">
        {t("presentation.graph.empty")}
      </div>
    );
  }

  return (
    <div className="rounded-xl border dark:border-gray-700 p-5">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
        <Network size={16} className="text-indigo-500" /> {t("presentation.graph.title")}
      </p>
      <p className="text-xs text-gray-400 mb-3">
        {t("presentation.graph.subtitle", { count: net.total, drug: net.center })}
      </p>

      <EgoGraph center={net.center} targets={net.targets} total={net.total} />

      <p className="mt-4 text-sm text-gray-600 dark:text-gray-400 border-l-4 border-indigo-400 pl-3">
        <strong className="text-gray-700 dark:text-gray-300">{t("presentation.takeawayLabel")} </strong>
        {t("presentation.graph.takeaway")}
      </p>
    </div>
  );
};

export default GraphNetwork;
