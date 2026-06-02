# 🏥 Drug Interaction Data Engineering and Analysis

Master's Thesis (TFM) — *Ingeniería y Análisis de Datos de Interacciones Farmacológicas* — Universidad de Málaga.

An end-to-end pipeline that takes the Spanish **CIMA** pharmaceutical dataset (XML), loads it into two
NoSQL databases (**MongoDB** + **Neo4j**), enriches drug-interaction text with **NLP**, **benchmarks** the
two databases, and exposes everything through a **FastAPI** REST API and a **React** dashboard.

---

## 📦 What the project contains

| Part | Description | Entry point |
|------|-------------|-------------|
| **1. ETL** | Parse CIMA XML → MongoDB (documents) + Neo4j (graph) | `drug-data-engine/run_etl.py` |
| **2. NLP** | Classify each interaction's severity / type / mechanism (regex + spaCy) | `drug-data-engine/run_nlp.py` |
| **3. Benchmarks** | MongoDB vs Neo4j: speed (19 queries) + scalability | `drug-data-engine/run_benchmarks.py`, `run_scalability.py` |
| **4. REST API** | FastAPI service over both databases | `drug-data-engine/src/api/main.py` |
| **5. Dashboard** | React + TypeScript UI (incl. a Results overview) | `drug-data-ui/` |

---

## 📊 Data source

**CIMA — Nomenclátor de prescripción** (AEMPS): <https://cima.aemps.es/cima/publico/nomenclator.html>
~30,000 drugs · ~70,000 interactions · 13 reference dictionaries, in XML.

> The XML files are **not** included in the repository (they are large). They are only needed to
> **re-run the ETL from scratch** — see [Optional: rebuild the data](#-optional-rebuild-the-data-from-scratch).
> For normal use the cloud databases are already populated.

---

## 📋 Prerequisites

- **Python 3.10+** — <https://www.python.org/downloads/>
- **Node.js 18+** and **npm** — <https://nodejs.org/>
- **Git** — <https://git-scm.com/downloads>

> The project uses **MongoDB Atlas** and **Neo4j Aura** (cloud). You do **not** need to install any
> database locally. Connection details are in `drug-data-engine/.env`.

---

## 🚀 Quick start (clone → running app)

### 1) Clone

```bash
git clone https://github.com/<your-username>/Drug-Interaction-Analysis.git
cd Drug-Interaction-Analysis
```

### 2) Backend (drug-data-engine)

```bash
cd drug-data-engine

# create + activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

The `.env` file with the database credentials is included in `drug-data-engine/`. (If you use your own
databases instead, edit the values there — keys: `mongodb_uri`, `mongodb_db`, `neo4j_uri`, `neo4j_user`,
`neo4j_password`, `data_path`.)

Run the API server **from the `drug-data-engine/` folder**:

```bash
uvicorn src.api.main:app --reload
```

- API: <http://localhost:8000>
- Swagger docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

### 3) Frontend (drug-data-ui)

Open a **second terminal** (keep the backend running):

```bash
cd drug-data-ui
npm install
npm run dev
```

- Dashboard: <http://localhost:5173>  (it talks to the API at `http://localhost:8000`)

That's it — the dashboard pages (Dashboard, **Results**, Medications, Interactions, NLP Analysis,
Database Performance, …) are populated from the cloud databases and the result files in
`drug-data-engine/results/`.

---

## 🗂 Project structure

```
Drug-Interaction-Analysis/
├── data/                              # CIMA XML files (not in repo — download separately)
├── design/                            # Schema & architecture design documents
├── drug-data-engine/                  # Backend (Python)
│   ├── run_etl.py                     # ETL pipeline
│   ├── run_nlp.py                     # NLP processing
│   ├── run_benchmarks.py              # MongoDB vs Neo4j speed benchmark
│   ├── run_scalability.py             # Scalability benchmark
│   ├── requirements.txt
│   ├── .env                           # DB credentials
│   ├── src/
│   │   ├── api/                       # FastAPI app (main.py) + routes + schemas
│   │   ├── config/                    # Settings (.env loader)
│   │   ├── extractors/                # XML parsing
│   │   ├── transformers/              # Reshape data for each database
│   │   ├── loaders/                   # MongoDB + Neo4j loaders
│   │   ├── models/                    # Domain dataclasses
│   │   ├── nlp/                       # Regex NLP classifiers
│   │   ├── nlp_spacy/                 # spaCy + NLTK NLP classifiers
│   │   ├── benchmarks/                # Benchmark framework + queries
│   │   ├── services/                  # MongoDB / Neo4j query services
│   │   └── utils/
│   ├── scripts/                       # create_indexes, verify_data_integrity, evaluate_nlp, sync_nlp_to_neo4j, …
│   ├── notebooks/                     # Data exploration + NLP evaluation notebooks
│   ├── results/                       # Benchmark / scalability / NLP-eval / integrity outputs (JSON+CSV)
│   └── tests/                         # Unit tests
├── drug-data-ui/                      # Frontend (React + TypeScript + Vite)
│   └── src/
│       ├── api/                       # Axios clients (one per API route group)
│       ├── components/                # Layout, Sidebar, Navbar, …
│       └── pages/                     # Dashboard, Results, Interactions, NLPAnalysis, DBPerformance, …
└── README.md
```

---

## 🛠 Tech stack

- **Backend:** Python, FastAPI, `xml.etree.ElementTree`, PyMongo, Neo4j Python Driver
- **NLP:** spaCy (`es_core_news_md`) + NLTK, plus a rule/regex approach
- **Databases:** MongoDB Atlas (documents) + Neo4j Aura (graph)
- **Frontend:** React 19, TypeScript, Vite, TailwindCSS, i18n (es/en), dark mode


---

## 👤 Author

**Mohamed Serbout** — Máster Universitario en Ingeniería Informática, Universidad de Málaga.
Tutors: José Manuel García Nieto · Ismael Navas Delgado.
