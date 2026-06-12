import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  FlaskConical, Database, Brain, BarChart3, CheckCircle2, Trophy, ArrowRight,
  Pill, Network, Server, Zap, GitBranch, FileCode2, Gauge,
} from "lucide-react";
import { getDashboardStats, getIntegrityReport } from "../../api/dashboard";
import { getNlpStatistics, getNlpEvaluation } from "../../api/nlpAnalysis";
import { getBenchmarkResults, getScalabilityResults } from "../../api/dbPerformance";
import { getInteractions } from "../../api/interactions";
import GraphNetwork from "./GraphNetwork";
import InteractionLookup from "./InteractionLookup";

/* ----------------------------- types ----------------------------- */
interface Stats { medications: number; ingredients: number; interactions: number; laboratories: number; atc_codes: number; }
interface Integrity { summary: { pass: number; warn: number; fail: number }; headline: { drugs: number | null; interactions_raw: number | null; interactions_neo4j: number | null; reference_dictionaries: number | null }; }
interface NlpApproach { accuracy: number | null; macro_f1: number | null; weighted_f1: number | null; }
interface NlpTask { task: string; regex_f1: number | null; spacy_f1: number | null; best: string | null; regex?: NlpApproach; spacy?: NlpApproach; }
interface NlpEval { samples: number | null; model: string | null; tasks: NlpTask[]; }
interface Dist { label: string; count: number; }
interface NlpStats { processed: number; processing_rate: number; average_confidence: number; severity_distribution: Dist[]; type_distribution: Dist[]; }
interface Bench { overall_winner: string; speedup_factor: number; mongodb_wins: number; neo4j_wins: number; comparable_count: number; graph_exclusive_queries: number; mongodb_avg_ms: number; neo4j_avg_ms: number; }
interface ScaleQ { query: string; label: string; scaling: { mongodb: number | null; neo4j: number | null }; }
interface Scale { queries: ScaleQ[]; }
interface Interaction { medicamento_origen: { nombre: string; atc: string }; medicamento_destino: { nombre: string; atc: string }; interaccion: { efecto: string; recomendacion: string; nlp?: { severidad?: string; tipo?: string; mecanismo?: string } }; }

const SEV_COLOR: Record<string, string> = {
  contraindicated: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  severe: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  moderate: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  mild: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  unknown: "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300",
};
const SEV_BAR: Record<string, string> = {
  contraindicated: "#ef4444", severe: "#f97316", moderate: "#eab308", mild: "#22c55e", unknown: "#9ca3af",
};
const num = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString());

const Presentation = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState<Stats | null>(null);
  const [integ, setInteg] = useState<Integrity | null>(null);
  const [nlpEval, setNlpEval] = useState<NlpEval | null>(null);
  const [nlpStats, setNlpStats] = useState<NlpStats | null>(null);
  const [bench, setBench] = useState<Bench | null>(null);
  const [scale, setScale] = useState<Scale | null>(null);
  const [example, setExample] = useState<Interaction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [s, ig, ev, ns, bm, sc, ix] = await Promise.allSettled([
        getDashboardStats(), getIntegrityReport(), getNlpEvaluation(),
        getNlpStatistics(), getBenchmarkResults(), getScalabilityResults(),
        getInteractions(1, 8, "contraindicated", "cardiac"),
      ]);
      if (s.status === "fulfilled") setStats(s.value);
      if (ig.status === "fulfilled") setInteg(ig.value);
      if (ev.status === "fulfilled") setNlpEval(ev.value);
      if (ns.status === "fulfilled") setNlpStats(ns.value);
      if (bm.status === "fulfilled") setBench(bm.value);
      if (sc.status === "fulfilled") setScale(sc.value);
      if (ix.status === "fulfilled") {
        const items: Interaction[] = ix.value?.items ?? [];
        const pick = items.find((i) => i.interaccion?.nlp?.severidad && i.interaccion?.efecto) ?? items[0];
        setExample(pick ?? null);
      }
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-52 bg-gray-200 dark:bg-gray-800 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-5 py-8 space-y-10">

      {/* ====================== HERO ====================== */}
      <section className="rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-emerald-600 text-white p-8 shadow-lg">
        <div className="flex items-center gap-2 text-white/80 text-sm font-medium mb-3">
          <FlaskConical size={18} /> {t("presentation.kicker")}
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold leading-tight">
          {t("presentation.title")}
        </h1>
        <p className="mt-3 text-white/90 max-w-3xl">
          {t("presentation.subtitle")}
        </p>

        {/* big numbers */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {[
            { icon: <Pill size={20} />, value: num(stats?.medications), label: t("presentation.metrics.medicines") },
            { icon: <Network size={20} />, value: num(stats?.interactions), label: t("presentation.metrics.interactions") },
            { icon: <Brain size={20} />, value: "100%", label: t("presentation.metrics.nlpEnriched") },
            { icon: <Database size={20} />, value: "2", label: t("presentation.metrics.databases") },
          ].map((m, i) => (
            <div key={i} className="bg-white/15 backdrop-blur rounded-xl p-4">
              <div className="flex items-center gap-2 text-white/80 mb-1">{m.icon}<span className="text-xs uppercase tracking-wide">{m.label}</span></div>
              <div className="text-2xl font-bold">{m.value}</div>
            </div>
          ))}
        </div>

        {/* architecture flow */}
        <div className="flex flex-wrap items-center gap-2 mt-6 text-sm">
          {["CIMA XML", "ETL", "MongoDB + Neo4j", "NLP", "REST API", "Dashboard"].map((step, i, arr) => (
            <span key={step} className="flex items-center gap-2">
              <span className="bg-white/20 rounded-lg px-3 py-1 font-medium">{step}</span>
              {i < arr.length - 1 && <ArrowRight size={14} className="text-white/70" />}
            </span>
          ))}
        </div>
      </section>

      {/* ====================== PART 1 — ETL ====================== */}
      <Section icon={<Database className="text-emerald-500" />} kicker={t("presentation.etl.kicker")}
        title={t("presentation.etl.title")}>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="md:col-span-1 rounded-xl border dark:border-gray-700 p-5 flex flex-col items-center justify-center text-center bg-emerald-50 dark:bg-emerald-900/20">
            <CheckCircle2 size={36} className="text-emerald-500 mb-2" />
            <div className="text-3xl font-extrabold text-gray-800 dark:text-white">
              {integ ? `${integ.summary.pass}/${integ.summary.pass + integ.summary.warn + integ.summary.fail}` : "—"}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{t("presentation.etl.checksPassed")}</div>
          </div>
          <div className="md:col-span-2 grid grid-cols-2 gap-3">
            <Metric label={t("presentation.etl.drugs")} value={num(integ?.headline.drugs)} />
            <Metric label={t("presentation.etl.interactionsMongo")} value={num(integ?.headline.interactions_raw)} />
            <Metric label={t("presentation.etl.edgesNeo4j")} value={num(integ?.headline.interactions_neo4j)} />
            <Metric label={t("presentation.etl.refDicts")} value={num(integ?.headline.reference_dictionaries)} />
          </div>
        </div>
        <Takeaway label={t("presentation.takeawayLabel")}>{t("presentation.etl.takeaway")}</Takeaway>
      </Section>

      {/* ====================== PART 2 — NLP ====================== */}
      <Section icon={<Brain className="text-sky-500" />} kicker={t("presentation.nlp.kicker")}
        title={t("presentation.nlp.title")}>

        {/* before -> after */}
        {example && (
          <div className="rounded-xl border dark:border-gray-700 overflow-hidden mb-5">
            <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
              {t("presentation.nlp.liveExample")} — {example.medicamento_origen?.nombre} → {example.medicamento_destino?.nombre}
            </div>
            <div className="grid md:grid-cols-2 gap-0">
              <div className="p-4 border-r dark:border-gray-700">
                <p className="text-[11px] font-semibold text-gray-400 uppercase mb-1">{t("presentation.nlp.rawText")}</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 italic">“{example.interaccion?.efecto} {example.interaccion?.recomendacion}”</p>
              </div>
              <div className="p-4 flex flex-col justify-center gap-2 bg-gray-50/50 dark:bg-gray-800/40">
                <p className="text-[11px] font-semibold text-gray-400 uppercase mb-1">{t("presentation.nlp.extracted")}</p>
                <div className="flex flex-wrap gap-2">
                  {example.interaccion?.nlp?.severidad && (
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${SEV_COLOR[example.interaccion.nlp.severidad] || SEV_COLOR.unknown}`}>
                      {t("presentation.nlp.severity")}: {example.interaccion.nlp.severidad}
                    </span>
                  )}
                  {example.interaccion?.nlp?.tipo && (
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">{t("presentation.nlp.type")}: {example.interaccion.nlp.tipo}</span>
                  )}
                  {example.interaccion?.nlp?.mecanismo && (
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">{t("presentation.nlp.mechanism")}: {example.interaccion.nlp.mecanismo}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-5">
          {/* F1 comparison */}
          <div className="rounded-xl border dark:border-gray-700 p-5">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><GitBranch size={16} /> {t("presentation.nlp.f1Title")}</p>
            <div className="space-y-3">
              {(nlpEval?.tasks ?? []).map((task) => (
                <div key={task.task}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="capitalize text-gray-600 dark:text-gray-300">{task.task}</span>
                    {task.best && <span className="text-gray-400">{t("presentation.nlp.best")}: <strong className={task.best === "regex" ? "text-green-600" : "text-blue-600"}>{task.best}</strong></span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <BarPair label="R" value={task.regex?.accuracy ?? task.regex_f1} color="#16a34a" best={task.best === "regex"} />
                    <BarPair label="S" value={task.spacy?.accuracy ?? task.spacy_f1} color="#3b82f6" best={task.best === "spacy"} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-gray-400 mt-3">{t("presentation.nlp.evaluatedOn", { count: nlpEval?.samples ?? 0 })}</p>
          </div>

          {/* severity distribution */}
          <div className="rounded-xl border dark:border-gray-700 p-5">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2"><Gauge size={16} /> {t("presentation.nlp.severityDistTitle")}</p>
            <div className="space-y-2.5">
              {(nlpStats?.severity_distribution ?? []).map((d) => {
                const total = nlpStats?.processed || 1;
                const pct = (d.count / total) * 100;
                return (
                  <div key={d.label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="capitalize text-gray-600 dark:text-gray-300">{d.label}</span>
                      <span className="text-gray-400">{d.count.toLocaleString()} ({pct.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                      <div className="h-2 rounded-full" style={{ width: `${pct}%`, backgroundColor: SEV_BAR[d.label] || "#9ca3af" }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        <Takeaway label={t("presentation.takeawayLabel")}>{t("presentation.nlp.takeaway", { total: num(stats?.interactions) })}</Takeaway>
      </Section>

      {/* ====================== PART 3 — DATABASES ====================== */}
      <Section icon={<BarChart3 className="text-rose-500" />} kicker={t("presentation.db.kicker")}
        title={t("presentation.db.title")}>

        {/* graph visualisation — justifies the graph database in one glance */}
        <div className="mb-5">
          <GraphNetwork />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="rounded-xl border dark:border-gray-700 p-4 bg-blue-50 dark:bg-blue-900/20">
            <div className="flex items-center gap-1.5 mb-1"><Trophy size={15} className="text-yellow-500" /><span className="text-xs uppercase text-gray-500 dark:text-gray-400">{t("presentation.db.overall")}</span></div>
            <div className="text-xl font-bold text-blue-600">{bench?.overall_winner ?? "—"}</div>
            <div className="text-xs text-gray-400">{bench ? t("presentation.db.faster", { factor: bench.speedup_factor }) : ""}</div>
          </div>
          <Metric icon={<Server size={15} className="text-green-600" />} label={t("presentation.db.mongoWins")} value={`${bench?.mongodb_wins ?? "—"}`} sub={bench ? t("presentation.db.medianMs", { ms: bench.mongodb_avg_ms.toFixed(0) }) : ""} />
          <Metric icon={<Zap size={15} className="text-blue-500" />} label={t("presentation.db.neo4jWins")} value={`${bench?.neo4j_wins ?? "—"}`} sub={bench ? t("presentation.db.medianMs", { ms: bench.neo4j_avg_ms.toFixed(0) }) : ""} />
          <Metric icon={<Network size={15} className="text-indigo-500" />} label={t("presentation.db.graphOnly")} value={`${bench?.graph_exclusive_queries ?? "—"}`} sub={t("presentation.db.neo4jOnly")} />
        </div>

        {/* scalability scaling factors */}
        {scale && scale.queries.length > 0 && (
          <div className="rounded-xl border dark:border-gray-700 p-5">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{t("presentation.db.scalabilityTitle")}</p>
            <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
              {scale.queries.map((q) => (
                <div key={q.query} className="flex justify-between border-b dark:border-gray-700 py-1">
                  <span className="text-gray-600 dark:text-gray-300 truncate pr-2">{q.label}</span>
                  <span className="font-mono whitespace-nowrap">
                    <span className="text-green-600">M {q.scaling.mongodb ?? "—"}×</span>{" · "}
                    <span className="text-blue-600">N {q.scaling.neo4j ?? "—"}×</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        <Takeaway label={t("presentation.takeawayLabel")}>{t("presentation.db.takeaway")}</Takeaway>
      </Section>

      {/* ====================== USEFULNESS — LIVE LOOKUP ====================== */}
      <Section icon={<Pill className="text-indigo-500" />} kicker={t("presentation.lookup.kicker")}
        title={t("presentation.lookup.title")}>
        <InteractionLookup />
        <Takeaway label={t("presentation.takeawayLabel")}>{t("presentation.lookup.takeaway")}</Takeaway>
      </Section>

      {/* ====================== CLOSING ====================== */}
      <section className="rounded-2xl border dark:border-gray-700 p-6 bg-gray-50 dark:bg-gray-800/50">
        <h3 className="font-bold text-gray-800 dark:text-white mb-2 flex items-center gap-2"><FileCode2 size={18} className="text-indigo-500" /> {t("presentation.closing.title")}</h3>
        <p className="text-gray-700 dark:text-gray-300">
          {t("presentation.closing.text")}
        </p>
        <div className="flex flex-wrap gap-3 mt-4 text-sm">
          <Link to="/nlp-analysis" className="inline-flex items-center gap-1 text-sky-600 dark:text-sky-400 hover:underline">{t("presentation.closing.exploreNlp")} <ArrowRight size={14} /></Link>
          <Link to="/database-performance" className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 hover:underline">{t("presentation.closing.exploreDb")} <ArrowRight size={14} /></Link>
          <Link to="/interactions" className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400 hover:underline">{t("presentation.closing.browseInteractions")} <ArrowRight size={14} /></Link>
        </div>
      </section>
    </div>
  );
};

/* --------------------------- helpers --------------------------- */
function Section({ icon, kicker, title, children }: { icon: React.ReactNode; kicker: string; title: string; children: React.ReactNode }) {
  return (
    <section>
      <div className="mb-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">{icon}{kicker}</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-white mt-1">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ icon, label, value, sub }: { icon?: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
      <div className="flex items-center gap-1.5 mb-1 text-gray-500 dark:text-gray-400">{icon}<span className="text-xs">{label}</span></div>
      <div className="text-xl font-bold text-gray-800 dark:text-white">{value}</div>
      {sub && <div className="text-xs text-gray-400">{sub}</div>}
    </div>
  );
}

function BarPair({ label, value, color, best }: { label: string; value: number | null; color: string; best: boolean }) {
  const pct = value != null ? value * 100 : 0;
  return (
    <div className="flex-1 flex items-center gap-1.5">
      <span className="text-[10px] w-3 text-gray-400">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3 relative">
        <div className="h-3 rounded-full" style={{ width: `${pct}%`, backgroundColor: color, opacity: best ? 1 : 0.55 }} />
      </div>
      <span className={`text-[11px] font-mono w-9 text-right ${best ? "font-bold" : "text-gray-400"}`}>{value != null ? value.toFixed(2) : "—"}</span>
    </div>
  );
}

function Takeaway({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <p className="mt-4 text-sm text-gray-600 dark:text-gray-400 border-l-4 border-indigo-400 pl-3">
      <strong className="text-gray-700 dark:text-gray-300">{label} </strong>{children}
    </p>
  );
}

export default Presentation;
