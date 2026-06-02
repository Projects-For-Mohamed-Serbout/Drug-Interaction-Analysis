# Project Overview — Drug Interaction Data Engineering and Analysis (TFM)

> A from-scratch guide to understanding what this project is, what was built, why each piece exists, and how to talk about it.

---

## 1. The problem you are solving

Pharmacological data — drug names, active ingredients, ATC classifications, manufacturers, and especially **drug-drug interactions** — are critical for patient safety. In Spain this data is published by **AEMPS** (Agencia Española de Medicamentos y Productos Sanitarios) through the **CIMA** portal. The data ships as a large set of **XML files**: one main `Prescripcion.xml` plus ~13 reference dictionaries.

Three real difficulties make this dataset hard to use directly:

1. **Format**: XML is not queryable by clinicians or applications. It must be ETL-ed into structured storage.
2. **Free text**: each interaction has Spanish-language fields describing the *effect* and *recommendation* — there is no machine-readable severity, no mechanism, no clinical category. To filter "show me all severe cardiac interactions" you need NLP.
3. **Storage trade-off**: drug records are document-like (nested forms, ingredients, packaging) but interactions are graph-like (drug-to-drug edges). No single database is obviously best, so the project compares two.

The TFM addresses all three: **ETL into NoSQL → NLP enrichment → benchmark comparison → REST API and React UI.**

---

## 2. High-level architecture

```
CIMA XML files
      │
      ▼
[1] ETL pipeline (Python)
      ├──► MongoDB Atlas  (document store)
      └──► Neo4j Aura     (graph store)
                │
                ▼
[2] NLP enrichment (regex + spaCy, run on interaction text)
                │
                ▼
[3] Benchmark suite (19 queries × 30 iterations, both DBs)
                │
                ▼
[4] FastAPI REST API
                │
                ▼
[5] React + TypeScript dashboard (i18n, dark mode)
```

Each of the five blocks is a self-contained chapter of the thesis. The repo splits them into two top-level packages:

- [drug-data-engine/](drug-data-engine/) — Python backend (ETL, NLP, benchmarks, API)
- [drug-data-ui/](drug-data-ui/) — React + Vite + TypeScript frontend

The supporting folders are [data/](data/) (raw XML), [design/](design/) (schema and architecture notes), [documents/](documents/) (anteproyecto PDF, state of the art), and [drug-data-engine/results/](drug-data-engine/results/) (benchmark CSV/JSON and NLP evaluation JSON).

---

## 3. The data (block 0)

Source: [CIMA Nomenclator](https://cima.aemps.es/cima/publico/nomenclator.html).

**One main file:**
- `Prescripcion.xml` — ~30,000 drug records (`cod_nacion` is the national identifier). Each record nests pharmaceutical forms, dosages, ATC classifications, and an `interacciones_atc` block with ~70,000 interactions in total.

**Thirteen reference dictionaries** — Active Ingredients, Laboratories, ATC codes, Pharmaceutical Forms (full + simplified), Administration Routes, Excipients, Package Types, Content Units, Registration Status, DCSA / DCP / DCPF (SNOMED-style codes).

When the professor asks "what's your dataset?" the headline numbers are: **~30K drugs, ~70K drug-drug interactions, 14 XML files**.

---

## 4. Block 1 — The ETL pipeline

Entry point: [drug-data-engine/run_etl.py](drug-data-engine/run_etl.py).

It runs three phases:

### 4.1 Extract — [src/extractors/](drug-data-engine/src/extractors/)
- [xml_extractor.py](drug-data-engine/src/extractors/xml_extractor.py) is a small base class that wraps `xml.etree.ElementTree` and provides typed helpers (`get_text`, `get_int`, `get_bool`).
- [dictionary_extractor.py](drug-data-engine/src/extractors/dictionary_extractor.py) parses all 13 reference XMLs into typed lists.
- [prescription_extractor.py](drug-data-engine/src/extractors/prescription_extractor.py) parses `Prescripcion.xml` with `xml.etree.ElementTree` and exposes a generator (`extract_drugs()`) that yields one `Drug` object per `<prescription>`. (Note: the file is parsed fully into a DOM tree by `ET.parse`, and `run_etl.py` materialises the drugs into a list — it is not memory-streaming. For a 187 MB file this is fine on a normal machine.) The key method `_extract_interactions()` pulls `atc_interaccion`, `descripcion_atc_interaccion`, `efecto_interaccion`, and `recomendacion_interaccion` from each `<interacciones_atc>` node. **This is the raw text that NLP later classifies.**

### 4.2 Transform — [src/transformers/data_transformer.py](drug-data-engine/src/transformers/data_transformer.py)
The transformer builds in-memory lookup dicts from reference data (e.g. `lab_code → lab_name`) and uses them to **denormalize** drugs for MongoDB. For Neo4j it produces node and relationship lists. It also extracts each interaction as a standalone document for the `drug_interactions` collection. Metadata fields (`fecha_carga`, `procesado_nlp=false`) flag interactions for later NLP processing.

### 4.3 Load — [src/loaders/](drug-data-engine/src/loaders/)

- **MongoDB** ([mongodb_loader.py](drug-data-engine/src/loaders/mongodb_loader.py)) creates 14 collections, sets text indexes on names, unique indexes on codes, and compound indexes on common query patterns (e.g. `atc.codigo + comercializado`). Bulk insert uses `insert_many` with unordered writes.
- **Neo4j** ([neo4j_loader.py](drug-data-engine/src/loaders/neo4j_loader.py)) declares uniqueness constraints, creates indexes, then uses `UNWIND + MERGE` (batch upsert) for nodes and relationships. The graph schema:
  - Nodes: `Drug`, `ActiveIngredient`, `Laboratory`, `ATCCode`, `PharmaceuticalForm`, `AdministrationRoute`, `Excipient`, `PackageType`, `Biomarker`
  - Relationships: `MANUFACTURED_BY`, `MARKETED_BY` (Drug→Laboratory), `CLASSIFIED_AS` (Drug→ATCCode), `CONTAINS` (Drug→ActiveIngredient), `HAS_FORM`, `ADMINISTERED_VIA`, `PACKAGED_IN`, `CONTAINS_EXCIPIENT`, `HAS_BIOMARKER`, `PARENT_OF` (ATCCode→ATCCode hierarchy), and `INTERACTS_WITH_ATC` (**Drug→ATCCode**, carrying `efecto`, `recomendacion`, and later the NLP fields). Interactions point to an **ATC code, not another drug**, because CIMA defines interactions at the substance/ATC level (`atc_interaccion` is an ATC code, never a `cod_nacion`). Drug-to-drug interaction is recovered on demand via the traversal `(d1)-[:INTERACTS_WITH_ATC]->(atc)<-[:CLASSIFIED_AS]-(d2)`. Note: therapeutic duplicities, geriatric warnings and supply problems are stored **only in MongoDB** (embedded in each drug), not in the graph.

### 4.4 Domain model — [src/models/drug.py](drug-data-engine/src/models/drug.py)
Plain Python `@dataclass`es (no Pydantic overhead here) for every CIMA entity, plus a `DrugInteraction` class with placeholders for the NLP results that get filled in by block 2.

### 4.5 Configuration
[src/config/](drug-data-engine/src/config/) loads `.env` via `python-dotenv` and exposes a `Settings` singleton with XML paths, MongoDB URI/DB, and Neo4j URI/user/password. `validate()` checks credentials and file existence before the pipeline runs.

**How to run it:**
```bash
python run_etl.py --clear           # wipe both DBs and reload everything
python run_etl.py --mongodb-only    # MongoDB only
python run_etl.py --test            # extract only, no DB writes
```

**Verifying the load (anteproyecto "data integrity" requirement):**
```bash
python -m scripts.verify_data_integrity        # reconcile XML <-> MongoDB <-> Neo4j
python -m scripts.verify_data_integrity --skip-xml   # DB-only, fast
```
This reconciles drug/interaction/reference counts across the source XML and both
databases, explains the MongoDB-vs-Neo4j interaction count difference (duplicate
`(drug, ATC)` rows collapsed by Neo4j `MERGE`), checks referential integrity, and
writes `results/integrity_report_<timestamp>.json`.

---

## 5. Block 2 — NLP enrichment (two parallel approaches)

After ETL, every interaction in MongoDB has `effect` and `recommendation` text in Spanish but **no structured severity, type, or mechanism**. Block 2 fills those in. Two implementations exist on purpose, so the thesis can compare them.

Entry point: [drug-data-engine/run_nlp.py](drug-data-engine/run_nlp.py) (options: `--reprocess`, `--sample N`, `--stats`).

### 5.1 The three classifications

For every interaction the pipeline produces:

| Task | Output | Classes |
|---|---|---|
| **Severity** | one of 5 levels | `contraindicated`, `severe`, `moderate`, `mild`, `unknown` |
| **Type** | clinical effect category | `cardiac`, `cns`, `hemorrhagic`, `metabolic`, `renal`, `hepatic`, `respiratory`, `gi`, `muscular`, `hematologic`, `efficacy_increase`, `efficacy_reduction`, `toxicity`, `other` |
| **Mechanism** | pharmacological mechanism | `pharmacokinetic` (CYP enzymes, P-gp, OATP…), `pharmacodynamic` (receptors, ion channels), `unknown` |

Each classifier also returns a **confidence score** and the pipeline aggregates an overall confidence — see [src/nlp/nlp_pipeline.py](drug-data-engine/src/nlp/nlp_pipeline.py) and the `NLPAnalysisResult` dataclass.

### 5.2 Approach A — Regex ([src/nlp/](drug-data-engine/src/nlp/))
- `severity_classifier.py` — weighted Spanish regex patterns. Examples: "contraindicado", "no debe administrarse" → CONTRAINDICATED; "muerte", "paro cardíaco", "síndrome serotoninérgico" → SEVERE; "monitorizar", "ajustar dosis" → MODERATE.
- `interaction_type_classifier.py` — ~100 domain terms grouped by category (e.g. "arritmia", "QT", "fibrilación" → CARDIAC; "hemorragia", "INR" → HEMORRHAGIC).
- `mechanism_extractor.py` — patterns for specific CYP enzymes, transporters, receptors, ion channels.

Fast, transparent, easy to debug; brittle on phrasing it has not seen.

### 5.3 Approach B — spaCy ([src/nlp_spacy/](drug-data-engine/src/nlp_spacy/))
Same three classifiers reimplemented on top of the **Spanish spaCy model `es_core_news_md`**. Uses lemmatization (matches inflected forms), dependency parsing (catches negation like "no contraindicado"), and `spacy.pipe()` batching.

Slower, but linguistically more robust.

### 5.4 Evaluation — what the numbers actually say

Manually-labelled ground truth on **44 interaction samples** — see [drug-data-engine/results/nlp_evaluation_20260418_203930.json](drug-data-engine/results/nlp_evaluation_20260418_203930.json). Macro-F1 results:

| Task | Regex | spaCy | Winner |
|---|---|---|---|
| Severity | **0.714** | 0.680 | Regex |
| Type | **0.767** | 0.718 | Regex |
| Mechanism | 0.406 | **0.483** | spaCy |

Honest reading for the meeting: **regex wins on severity and type** because the vocabulary is small and highly conventional in Spanish prescribing text. **spaCy wins on mechanism** because mechanisms appear in more varied syntax where lemmatization helps. Both are weak on mechanism in absolute terms — that is the most defensible "future work" item.

44 samples is small. Be ready for the professor to push on this: state the sample size up front, present F1 with the caveat, and propose expanding the gold set as next-step work.

After NLP, [scripts/sync_nlp_to_neo4j.py](drug-data-engine/scripts/sync_nlp_to_neo4j.py) copies the results into the `INTERACTS_WITH_ATC` relationship properties in Neo4j so both DBs stay consistent.

---

## 6. Block 3 — Benchmarking MongoDB vs Neo4j

Entry point: [drug-data-engine/run_benchmarks.py](drug-data-engine/run_benchmarks.py). Framework in [src/benchmarks/](drug-data-engine/src/benchmarks/).

**Methodology**: 19 queries × 30 iterations per database, with warmup runs discarded. For each query the suite records min, max, mean, median, **p95**, std dev, and coefficient of variation. The winner per query is the database with the lower p95.

**Queries cover eight categories**: Point Lookup, Relationship Traversal, Range Scan, Text Search, Aggregation, Complex Filter, Multi-hop Traversal, Pattern Matching.

**Where the file lives:** [drug-data-engine/results/benchmark_results_20260418_181255.csv](drug-data-engine/results/benchmark_results_20260418_181255.csv).

**Headline findings** (which you should commit to memory before the meeting):

| Category | Winner | Reason |
|---|---|---|
| Point lookup (Q01) | Tie | Both use indexed lookups |
| Relationship traversal (Q02) | **Neo4j (~2×)** | Native edge model |
| Range scan / large filter (Q03, Q04) | **MongoDB (~1.3×)** | Optimized collection scans |
| Text search (Q05, Q15) | Tie | Both fine |
| Aggregation (Q06, Q11, Q13) | **Neo4j (~2.4×)** | Cypher aggregation on properties is fast |
| Complex filter (Q08, Q12) | **Neo4j (1.4–2.5×)** | Traversal + filter is graph-native |
| Multi-hop (Q16–Q19) | **Neo4j only** | Not practical in MongoDB |

The thesis story is therefore not "one wins" but **"the right database depends on the query shape"** — a real engineering result, not a sales pitch. Use it as your headline.

---

## 7. Block 4 — REST API (FastAPI)

Entry point: [drug-data-engine/src/api/main.py](drug-data-engine/src/api/main.py). Run with `uvicorn src.api.main:app --reload` (the README still says `app.main:app` from the previous structure — update it before submission).

The app uses an `asynccontextmanager` lifespan to open/close both DB connections, CORS to allow the Vite dev server (`localhost:5173`), and seven router groups:

| Router | Path | Purpose |
|---|---|---|
| dashboard | `/dashboard/stats` | Total drug / ingredient / interaction counts |
| medications | `/medications`, `/medications/search` | Search, list, detail |
| interactions | `/interactions`, `/interactions/drug/{cod}` | List with severity & type filters |
| ingredients | `/active-ingredients` | Paginated catalog |
| laboratories | `/laboratories` | Manufacturer directory |
| nlp | `/nlp-analysis` | NLP stats and distributions |
| benchmarks | `/database-performance` | Benchmark results for the UI |

Business logic sits in [src/services/mongodb_service.py](drug-data-engine/src/services/mongodb_service.py) and [src/services/neo4j_service.py](drug-data-engine/src/services/neo4j_service.py). Response shapes are Pydantic models in [src/api/schemas/responses.py](drug-data-engine/src/api/schemas/responses.py). FastAPI auto-generates Swagger docs at `/docs`.

---

## 8. Block 5 — Frontend dashboard

Stack ([drug-data-ui/package.json](drug-data-ui/package.json)): **React 19 + TypeScript + Vite + TailwindCSS**, with React Router 7, react-i18next (Spanish + English with browser detection + localStorage), Framer Motion, Lucide icons, react-hot-toast, Axios.

### 8.1 Routes — [src/App.tsx](drug-data-ui/src/App.tsx)
- `/` Dashboard — three [StatCard](drug-data-ui/src/components/StatCard.tsx)s + global search
- `/medications` — paginated drug table with search
- `/interactions` — paginated interactions, filter by severity and clinical type
- `/active-ingredients` — paginated ingredient catalog
- `/laboratories` — manufacturer directory
- `/nlp-analysis` — distribution charts from the NLP processing
- `/database-performance` — benchmark visualization

### 8.2 Components — [src/components/](drug-data-ui/src/components/)
Layout (sidebar + navbar shell), Navbar (logo, language switcher, [ThemeToggle](drug-data-ui/src/components/ThemeToggle.tsx)), Sidebar (route links), SearchBar (≥2-char validation), SearchResults (paginated), [SkeletonLoader](drug-data-ui/src/components/SkeletonLoader.tsx) (loading placeholders), StatCard.

### 8.3 API client — [src/api/](drug-data-ui/src/api/)
One Axios module per backend router. Base URL `http://localhost:8000`, 20s timeout. Each file mirrors a FastAPI route group.

---

## 9. Supporting pieces

### 9.1 Scripts — [drug-data-engine/scripts/](drug-data-engine/scripts/)
- `create_indexes.py` — explicit index creation
- `evaluate_nlp.py` — runs the gold-set evaluation that produced the NLP results JSON
- `compare_nlp_approaches.py` — runs both NLP pipelines side by side
- `sync_nlp_to_neo4j.py` — copies NLP fields from Mongo into the `INTERACTS_WITH` edges
- `backfill_biomarker_nodes.py`, `backfill_excipient_relationships.py` — retroactive graph enrichment
- `check_db_status.py` — connection / count health check
- `verify_data_integrity.py` — reconciles XML ↔ MongoDB ↔ Neo4j counts, checks referential integrity, writes a JSON report to `results/` (the ETL "data integrity" deliverable)

### 9.2 Tests — [drug-data-engine/tests/](drug-data-engine/tests/)
`test_extractors.py`, `test_nlp.py`, `test_api.py` — small unit suite over XML parsing, classifier behaviour, and key API endpoints. Realistic to call this "smoke coverage" rather than full coverage.

### 9.3 Notebooks — [drug-data-engine/notebooks/](drug-data-engine/notebooks/)
- `01_data_exploration.ipynb` — dataset overview, distributions across laboratories, ATC codes, ingredients
- `02_nlp_evaluation.ipynb` — comparison of regex vs spaCy with confusion matrices and per-class metrics (this is the notebook currently open in your IDE — it backs the table in section 5.4)

### 9.4 Design docs — [design/](design/)
`00_schema_overview.md`, `01_data_analysis.md`, `02_mongodb_schema.md`, `03_neo4j_schema.md`, `04_visual_diagrams.md`. These were written before implementation and are exactly what a thesis defence wants to see.

---

## 10. How to explain the project in 60 seconds (script for the professor)

> "The project is an end-to-end pipeline for Spanish pharmaceutical data. I take the official CIMA XML dataset — about thirty thousand drugs and seventy thousand interactions — parse it, and load it into two NoSQL databases at the same time: MongoDB for the document side, and Neo4j for the interaction graph. Then I enrich every interaction with NLP, classifying severity, clinical type, and pharmacological mechanism. I built two NLP implementations — one based on regex patterns over Spanish medical vocabulary, and one based on spaCy with the Spanish model — and I evaluate them against forty-four manually-labelled samples. On severity and clinical type, regex wins; on mechanism, spaCy wins. I also benchmark both databases across nineteen queries with thirty iterations each: Neo4j is roughly twice as fast on relationship traversals and aggregations, MongoDB is about thirty percent faster on large range scans, and they tie on point lookups. On top of that I built a FastAPI service that exposes everything, and a React-TypeScript dashboard with i18n and dark mode that visualises the data and the benchmark results."

---

## 11. Honest list of weak spots — get ahead of these in the meeting

1. **NLP gold set is only 44 samples.** Defensible for a TFM proof-of-concept, but you should propose growing it (target ≥200, stratified by severity) as future work.
2. **Mechanism extraction F1 is below 0.5 in both approaches.** Be honest about this. Causes: small training/eval set, no transformer-based model, no medical-domain Spanish model (BioBERT-es / clinical-NER).
3. **No automated CI right now.** The most recent commit (`Temporarily disable CI during v2 review`) acknowledges this. Re-enable before submission.
4. **README setup instructions reference the old `app/` package.** Update to `uvicorn src.api.main:app --reload`. This is a five-minute fix that prevents the professor from getting a confusing error.
5. **Test coverage is shallow.** Frame it as "smoke tests"; do not oversell.
6. **The 44-sample NLP eval was last run on 2026-04-18.** Re-run after any classifier change so the numbers in the thesis match the code.

---

## 12. What you can present as concrete contributions

1. A complete ETL from CIMA XML → MongoDB + Neo4j with reference data denormalisation and a graph schema (`INTERACTS_WITH_ATC` edges, Drug→ATCCode, carrying NLP attributes), plus an automated integrity-verification step that reconciles XML ↔ MongoDB ↔ Neo4j.
2. **Two comparable NLP pipelines** for Spanish drug-interaction text with a measured, per-class F1 comparison.
3. A reproducible **NoSQL benchmark** across 19 representative queries, with a clear per-category recommendation rather than a single winner.
4. A working REST API and a React dashboard that turn the analysis into something a clinician or researcher can actually click through.
5. Design documentation written **before** the code (in `design/`) — useful evidence of methodology.

---

## 13. Useful entry points (open these first)

- ETL: [drug-data-engine/run_etl.py](drug-data-engine/run_etl.py)
- NLP: [drug-data-engine/run_nlp.py](drug-data-engine/run_nlp.py), [src/nlp/nlp_pipeline.py](drug-data-engine/src/nlp/nlp_pipeline.py), [src/nlp_spacy/nlp_pipeline_spacy.py](drug-data-engine/src/nlp_spacy/nlp_pipeline_spacy.py)
- Benchmarks: [drug-data-engine/run_benchmarks.py](drug-data-engine/run_benchmarks.py), results in [drug-data-engine/results/](drug-data-engine/results/)
- API: [drug-data-engine/src/api/main.py](drug-data-engine/src/api/main.py)
- UI: [drug-data-ui/src/App.tsx](drug-data-ui/src/App.tsx)
- Design: [design/00_schema_overview.md](design/00_schema_overview.md)
- Evaluation notebook (currently open): [drug-data-engine/notebooks/02_nlp_evaluation.ipynb](drug-data-engine/notebooks/02_nlp_evaluation.ipynb)
