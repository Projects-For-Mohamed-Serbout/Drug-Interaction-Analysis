import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Search, X, Loader2, Pill } from "lucide-react";
import { searchMedications } from "../../api/medications";
import { getInteractionsForDrug } from "../../api/interactions";
import EgoGraph from "./EgoGraph";

const SEV_COLOR: Record<string, string> = {
  contraindicated: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  severe: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  moderate: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  mild: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  unknown: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};
const SEV_DOT: Record<string, string> = {
  contraindicated: "#ef4444", severe: "#f97316", moderate: "#eab308", mild: "#22c55e", unknown: "#9ca3af",
};
const SEV_ORDER = ["contraindicated", "severe", "moderate", "mild", "unknown"];

interface Med { codigo_nacional: string; nombre: string; principio_activo?: string; }
interface RawInteraction {
  medicamento_destino?: { nombre?: string };
  interaccion?: { efecto?: string; nlp?: { severidad?: string; tipo?: string } };
}
interface Hit { name: string; severity: string; type?: string; effect?: string; }

/**
 * Live interaction lookup — type a medicine, pick it from the CIMA catalogue,
 * and instantly see its documented interactions ranked by severity.
 * Wires the existing medication-search and per-drug-interactions endpoints together.
 */
const InteractionLookup = () => {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Med[]>([]);
  const [searching, setSearching] = useState(false);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Med | null>(null);
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [loadingHits, setLoadingHits] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // debounced typeahead
  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (query.trim().length < 2 || selected?.nombre === query) {
      setSuggestions([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    timer.current = setTimeout(async () => {
      try {
        const res = (await searchMedications(query.trim())) as Med[];
        setSuggestions(res.slice(0, 8));
        setOpen(true);
      } catch {
        setSuggestions([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [query, selected]);

  const pick = async (med: Med) => {
    setSelected(med);
    setQuery(med.nombre);
    setOpen(false);
    setSuggestions([]);
    setLoadingHits(true);
    setHits(null);
    try {
      const all = ((await getInteractionsForDrug(med.codigo_nacional)) ?? []) as RawInteraction[];
      const mapped: Hit[] = all
        .map((it) => ({
          name: it.medicamento_destino?.nombre ?? "",
          severity: it.interaccion?.nlp?.severidad ?? "unknown",
          type: it.interaccion?.nlp?.tipo,
          effect: it.interaccion?.efecto,
        }))
        .filter((h) => h.name)
        .sort((a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity));
      setHits(mapped);
    } catch {
      setHits([]);
    } finally {
      setLoadingHits(false);
    }
  };

  const reset = () => {
    setQuery("");
    setSelected(null);
    setHits(null);
    setSuggestions([]);
    setOpen(false);
  };

  return (
    <div className="rounded-xl border dark:border-gray-700 p-5">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{t("presentation.lookup.hint")}</p>

      {/* search box */}
      <div className="relative">
        <div className="flex items-center gap-2 rounded-lg border dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2.5 focus-within:ring-2 ring-indigo-400">
          <Search size={18} className="text-gray-400 shrink-0" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (selected) setSelected(null);
            }}
            onFocus={() => suggestions.length && setOpen(true)}
            placeholder={t("presentation.lookup.placeholder")}
            className="flex-1 bg-transparent outline-none text-sm text-gray-800 dark:text-gray-100 placeholder:text-gray-400"
          />
          {searching && <Loader2 size={16} className="text-gray-400 animate-spin shrink-0" />}
          {query && !searching && (
            <button onClick={reset} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 shrink-0">
              <X size={16} />
            </button>
          )}
        </div>

        {/* suggestions dropdown */}
        {open && suggestions.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full max-h-64 overflow-auto rounded-lg border dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg">
            {suggestions.map((m) => (
              <li key={m.codigo_nacional}>
                <button
                  onClick={() => pick(m)}
                  className="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700/60 flex items-start gap-2"
                >
                  <Pill size={15} className="text-indigo-400 mt-0.5 shrink-0" />
                  <span>
                    <span className="block text-sm text-gray-800 dark:text-gray-100">{m.nombre}</span>
                    {m.principio_activo && (
                      <span className="block text-xs text-gray-400">{m.principio_activo}</span>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* results */}
      <div className="mt-4">
        {loadingHits && (
          <div className="flex items-center gap-2 text-sm text-gray-400 py-6 justify-center">
            <Loader2 size={16} className="animate-spin" /> {t("presentation.lookup.searching")}
          </div>
        )}

        {!loadingHits && selected && hits && hits.length === 0 && (
          <p className="text-sm text-gray-400 py-4 text-center">{t("presentation.lookup.noInteractions")}</p>
        )}

        {!loadingHits && selected && hits && hits.length > 0 && (
          <>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
              {t("presentation.lookup.selected", { count: hits.length, drug: selected.nombre })}
            </p>

            {/* live ego-network of the searched drug */}
            <div className="mb-4">
              <EgoGraph center={selected.nombre} targets={hits} total={hits.length} />
            </div>

            <ul className="max-h-72 overflow-auto divide-y dark:divide-gray-700 rounded-lg border dark:border-gray-700">
              {hits.map((h, i) => (
                <li key={i} className="flex items-center gap-3 px-3 py-2">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: SEV_DOT[h.severity] || SEV_DOT.unknown }} />
                  <span className="flex-1 text-sm text-gray-700 dark:text-gray-200 truncate">{h.name}</span>
                  <span className={`px-2 py-0.5 text-[11px] font-semibold rounded-full shrink-0 ${SEV_COLOR[h.severity] || SEV_COLOR.unknown}`}>
                    {h.severity}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
};

export default InteractionLookup;
