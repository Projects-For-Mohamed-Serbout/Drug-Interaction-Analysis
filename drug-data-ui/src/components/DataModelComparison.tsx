import { useEffect, useState } from "react";
import { FileJson, Share2 } from "lucide-react";
import { getInteractions } from "../api/interactions";

interface Interaction {
  medicamento_origen?: { nombre?: string; cod_nacion?: string; atc?: string };
  medicamento_destino?: { nombre?: string; atc?: string };
  interaccion?: {
    efecto?: string;
    recomendacion?: string;
    nlp?: { severidad?: string; tipo?: string; mecanismo?: string };
  };
}

const trunc = (s: string, n = 24) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

/**
 * RQ2 — "optimal data structure". Shows the SAME interaction modelled as a
 * MongoDB embedded document vs a Neo4j subgraph, and links the structure to the
 * measured performance. Fetches one real interaction for authenticity.
 */
const DataModelComparison = () => {
  const [ix, setIx] = useState<Interaction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await getInteractions(1, 1, "contraindicated");
        const items: Interaction[] = res?.items ?? [];
        setIx(items[0] ?? null);
      } catch {
        setIx(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="h-72 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />;
  if (!ix) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border dark:border-gray-700 text-sm text-gray-400">
        No interaction available to illustrate the data models.
      </div>
    );
  }

  const o = ix.medicamento_origen ?? {};
  const d = ix.medicamento_destino ?? {};
  const nlp = ix.interaccion?.nlp ?? {};

  // trimmed document mirroring the real MongoDB structure
  const doc = {
    medicamento_origen: { cod_nacion: o.cod_nacion, nombre: o.nombre, atc: o.atc },
    medicamento_destino: { atc: d.atc, nombre: d.nombre },
    interaccion: {
      efecto: ix.interaccion?.efecto,
      recomendacion: ix.interaccion?.recomendacion,
      nlp: { severidad: nlp.severidad, tipo: nlp.tipo, mecanismo: nlp.mecanismo },
    },
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <Share2 size={18} className="text-indigo-500" />
        <h3 className="font-semibold text-gray-700 dark:text-gray-300 text-sm">
          How the data is modelled — document vs graph (RQ2)
        </h3>
      </div>

      <div className="p-5 grid lg:grid-cols-2 gap-5">
        {/* ---------- MongoDB document ---------- */}
        <div className="rounded-xl border dark:border-gray-700 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 border-b dark:border-gray-700">
            <FileJson size={15} className="text-emerald-600" />
            <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">MongoDB — embedded document</span>
          </div>
          <pre className="text-[11px] leading-relaxed p-4 overflow-x-auto text-gray-700 dark:text-gray-300 font-mono">
{JSON.stringify(doc, null, 2)}
          </pre>
          <p className="text-xs text-gray-500 dark:text-gray-400 px-4 pb-4">
            One self-contained document per drug→target pair — everything embedded, so a single
            <strong> indexed read returns the whole interaction</strong>. Trade-off: the same
            interaction is duplicated across every drug in the ATC class (70,682 records, but only
            91 distinct texts).
          </p>
        </div>

        {/* ---------- Neo4j graph ---------- */}
        <div className="rounded-xl border dark:border-gray-700 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-b dark:border-gray-700">
            <Share2 size={15} className="text-blue-600" />
            <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">Neo4j — graph relationship</span>
          </div>

          <svg viewBox="0 0 440 230" className="w-full h-auto px-2 pt-3">
            {/* edge: Drug -> ATCCode (interaction) */}
            <defs>
              <marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
                <path d="M0,0 L7,3 L0,6 Z" className="fill-blue-400" />
              </marker>
            </defs>
            <line x1="150" y1="55" x2="290" y2="55" className="stroke-blue-400" strokeWidth={2} markerEnd="url(#arrow)" />
            <text x="220" y="42" textAnchor="middle" className="fill-blue-500" style={{ fontSize: 10, fontWeight: 600 }}>
              INTERACTS_WITH_ATC
            </text>
            {/* property box on the edge */}
            <rect x="168" y="62" width="104" height="34" rx="5" className="fill-blue-50 dark:fill-blue-900/30 stroke-blue-200 dark:stroke-blue-800" />
            <text x="220" y="75" textAnchor="middle" className="fill-gray-600 dark:fill-gray-300" style={{ fontSize: 9 }}>
              severidad: {nlp.severidad ?? "—"}
            </text>
            <text x="220" y="88" textAnchor="middle" className="fill-gray-600 dark:fill-gray-300" style={{ fontSize: 9 }}>
              tipo: {nlp.tipo ?? "—"}
            </text>

            {/* Drug node */}
            <circle cx="80" cy="55" r="46" className="fill-indigo-500" />
            <text x="80" y="50" textAnchor="middle" className="fill-white" style={{ fontSize: 9, fontWeight: 700 }}>:Drug</text>
            <text x="80" y="64" textAnchor="middle" className="fill-white" style={{ fontSize: 8 }}>{trunc(o.nombre ?? "", 12)}</text>

            {/* ATCCode node (target) */}
            <circle cx="350" cy="55" r="42" className="fill-teal-500" />
            <text x="350" y="50" textAnchor="middle" className="fill-white" style={{ fontSize: 9, fontWeight: 700 }}>:ATCCode</text>
            <text x="350" y="64" textAnchor="middle" className="fill-white" style={{ fontSize: 8 }}>{d.atc ?? trunc(d.nombre ?? "", 10)}</text>

            {/* CLASSIFIED_AS edge to origin's own ATC (shows multiple rel types) */}
            <line x1="70" y1="98" x2="70" y2="160" className="stroke-gray-300 dark:stroke-gray-600" strokeWidth={1.5} markerEnd="url(#arrow)" />
            <text x="78" y="132" className="fill-gray-400" style={{ fontSize: 8.5 }}>CLASSIFIED_AS</text>
            <circle cx="70" cy="185" r="34" className="fill-teal-400/80" />
            <text x="70" y="182" textAnchor="middle" className="fill-white" style={{ fontSize: 8, fontWeight: 700 }}>:ATCCode</text>
            <text x="70" y="194" textAnchor="middle" className="fill-white" style={{ fontSize: 8 }}>{o.atc ?? "—"}</text>

            <text x="250" y="160" className="fill-gray-400" style={{ fontSize: 9 }}>+ CONTAINS, MANUFACTURED_BY,</text>
            <text x="250" y="173" className="fill-gray-400" style={{ fontSize: 9 }}>  PARENT_OF (ATC hierarchy)…</text>
          </svg>

          <p className="text-xs text-gray-500 dark:text-gray-400 px-4 pb-4 pt-1">
            Drugs and ATC classes are <strong>nodes</strong>; the interaction is a
            <strong> first-class relationship</strong> carrying severity/type. Shared ATC targets
            aren't duplicated, so relationships are cheap to <strong>traverse and aggregate</strong>.
          </p>
        </div>
      </div>

      <div className="px-5 pb-5">
        <p className="text-sm text-gray-600 dark:text-gray-400 border-l-4 border-indigo-400 pl-3">
          <strong className="text-gray-700 dark:text-gray-300">The structure explains the speed — </strong>
          the embedded document makes MongoDB's indexed point/filter reads fast (one document, few
          docs examined); first-class relationships make Neo4j's aggregation and multi-hop traversal
          fast. RQ2 isn't "which is faster" but "which structure fits the workload" — and the
          benchmark above shows exactly that split.
        </p>
      </div>
    </div>
  );
};

export default DataModelComparison;
