# Schema Design Overview
## Drug Interaction Data Engineering and Analysis - TFM

**Author:** Mohamed Serbout
**University:** Universidad de Málaga
**Date:** December 2024

---

## Table of Contents

1. [Project Context](#project-context)
2. [Data Source](#data-source)
3. [Entity-Relationship Model](#entity-relationship-model)
4. [Database Strategy](#database-strategy)
5. [Schema Documents](#schema-documents)
6. [Implementation Roadmap](#implementation-roadmap)

---

## Project Context

This document presents the data schema design for the Master's Thesis project focused on:

1. Processing and storing Spanish medication data from CIMA
2. Extracting drug interactions using NLP techniques
3. Comparing MongoDB and Neo4J for pharmacological data management
4. Optimizing queries for clinical decision support

### Research Questions Addressed

| Question | Schema Design Impact |
|----------|---------------------|
| Which NLP techniques for extracting interactions? | Schema includes NLP-specific fields in interaction data |
| Optimal data structure for NoSQL databases? | Dual design: document (MongoDB) and graph (Neo4J) |
| How to optimize interaction queries? | Indexes and denormalized interaction collections |

---

## Data Source

**CIMA (Centro de Información de Medicamentos)**
Agencia Española de Medicamentos y Productos Sanitarios (AEMPS)

### Source Files Summary

| Category | Files | Description |
|----------|-------|-------------|
| Main Data | `Prescripcion.xml` | Complete medication data with interactions |
| Dictionaries | 13 XML files | Reference data (laboratories, ingredients, ATC codes, etc.) |

### Key Data Elements

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CIMA Data Structure                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Prescripcion.xml                                                        │
│  ├── Drug identification (cod_nacion, nombre, presentacion)             │
│  ├── SNOMED CT codes (DCSA, DCP, DCPF)                                   │
│  ├── Classification flags (generico, hospitalario, psicotropo...)       │
│  ├── Laboratory references                                               │
│  ├── Pharmaceutical forms                                                │
│  │   ├── Active ingredient composition (with dosage)                    │
│  │   ├── Excipients                                                      │
│  │   └── Administration routes                                           │
│  ├── ATC classification                                                  │
│  │   ├── ⭐ DRUG INTERACTIONS (efecto, recomendacion) - KEY FOR NLP     │
│  │   ├── Therapeutic duplicities                                         │
│  │   └── Geriatric warnings                                              │
│  ├── Biomarkers (pharmacogenomics)                                       │
│  └── Supply problems                                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Entity-Relationship Model

### Primary Entities

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    Drug     │────▶│ ActiveIngredient│     │  Laboratory │
│             │     │                 │     │             │
│ ~20,000+    │     │    ~3,000+      │     │   ~500+     │
└──────┬──────┘     └─────────────────┘     └─────────────┘
       │
       │            ┌─────────────────┐     ┌─────────────┐
       ├───────────▶│     ATCCode     │     │   Excipient │
       │            │                 │     │             │
       │            │    ~6,000+      │     │   ~300+     │
       │            └─────────────────┘     └─────────────┘
       │
       │            ┌─────────────────┐     ┌─────────────────┐
       ├───────────▶│PharmaceuticalForm│    │AdministrationRoute│
       │            │                 │     │                 │
       │            │    ~300+        │     │    ~60+         │
       │            └─────────────────┘     └─────────────────┘
       │
       ▼
┌─────────────┐
│ Interaction │ ◀─── Critical for NLP project
│             │
│  ~50,000+   │
└─────────────┘
```

### Key Relationship: Drug Interactions

```
                    INTERACTS_WITH
    ┌─────────┐ ─────────────────────▶ ┌─────────┐
    │  Drug A │                        │  Drug B │
    │         │ ◀───────────────────── │         │
    └─────────┘    Properties:         └─────────┘
                   - efecto (effect)
                   - recomendacion (recommendation)
                   - severidad (NLP: severity)
                   - tipo (NLP: type)
                   - mecanismo (NLP: mechanism)
```

---

## Database Strategy

### Dual Database Approach

We use BOTH MongoDB and Neo4J to leverage their respective strengths:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Data Flow Architecture                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐      ┌──────────┐      ┌──────────────────────────────┐ │
│   │   XML    │─────▶│  Python  │─────▶│         MongoDB              │ │
│   │  Files   │      │  ETL     │      │  - Complete drug documents   │ │
│   └──────────┘      │  Script  │      │  - Reference collections     │ │
│                     │          │      │  - Text search               │ │
│                     │          │      │  - NLP result storage        │ │
│                     │          │      └──────────────────────────────┘ │
│                     │          │                                        │
│                     │          │      ┌──────────────────────────────┐ │
│                     │          │─────▶│          Neo4J               │ │
│                     └──────────┘      │  - Drug interaction graph    │ │
│                                       │  - ATC hierarchy             │ │
│                                       │  - Relationship queries      │ │
│                                       │  - Network analysis          │ │
│                                       └──────────────────────────────┘ │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Use Case Distribution

| Use Case | MongoDB | Neo4J |
|----------|:-------:|:-----:|
| Store complete drug profiles | ✅ | - |
| Fast drug lookup by ID | ✅ | - |
| Text search in drug names | ✅ | - |
| Store NLP processing results | ✅ | - |
| Find drug interactions | - | ✅ |
| Interaction network analysis | - | ✅ |
| Find interaction chains | - | ✅ |
| ATC hierarchy queries | - | ✅ |
| Find therapeutic alternatives | - | ✅ |
| Detect polypharmacy risks | - | ✅ |
| Performance benchmarking | ✅ | ✅ |

---

## Schema Documents

### Document 1: [Data Analysis](01_data_analysis.md)
- Complete analysis of all 14 XML files
- Field mappings and data types
- Identified entities and relationships
- NLP opportunities in text fields

### Document 2: [MongoDB Schema](02_mongodb_schema.md)
- Collection designs with sample documents
- Index strategies
- Validation schemas
- Sample queries

### Document 3: [Neo4J Schema](03_neo4j_schema.md)
- Node labels and properties
- Relationship types with properties
- Constraints and indexes
- Cypher query examples

---

## Implementation Roadmap

### Phase 1: Data Extraction and Transformation
```
[ ] Parse all XML files using Python (xml.etree.ElementTree)
[ ] Create data validation functions
[ ] Build transformation pipeline
[ ] Handle encoding and special characters
```

### Phase 2: MongoDB Implementation
```
[ ] Create database and collections
[ ] Define validation schemas
[ ] Load reference data (dictionaries)
[ ] Load main drug data
[ ] Create indexes
[ ] Verify data integrity
```

### Phase 3: Neo4J Implementation
```
[ ] Create constraints and indexes
[ ] Load nodes (drugs, ingredients, ATC codes, etc.)
[ ] Create relationships
[ ] Build interaction graph
[ ] Verify graph connectivity
```

### Phase 4: NLP Processing
```
[ ] Extract interaction text data
[ ] Preprocess text (spaCy/NLTK)
[ ] Classify interaction severity
[ ] Extract interaction types
[ ] Categorize effects
[ ] Update both databases with NLP results
```

### Phase 5: Query Optimization and Benchmarking
```
[ ] Develop test query suite
[ ] Benchmark MongoDB queries
[ ] Benchmark Neo4J queries
[ ] Compare performance metrics
[ ] Document findings
```

---

## Key Design Decisions

### 1. Denormalization in MongoDB
- Laboratory names embedded in drug documents
- Reduces JOIN-like operations
- Faster read performance

### 2. Separate Interaction Collection in MongoDB
- `drug_interactions` collection for fast interaction queries
- Enables efficient NLP batch processing
- Supports text indexing on interaction fields

### 3. Bidirectional Interactions in Neo4J
- Interactions modeled as relationships in both directions
- Enables traversal from either drug
- Natural representation of drug-drug interactions

### 4. ATC Hierarchy in Neo4J
- Parent-child relationships between ATC levels
- Enables queries like "find all drugs in category J01C"
- Supports therapeutic class analysis

### 5. NLP Fields in Schema
- Reserved fields for NLP-extracted data
- `severidad`, `tipo`, `mecanismo`, `categoria_efecto`
- Enables filtering interactions by severity/type

---

## File Structure

```
design/
├── 00_schema_overview.md      # This document
├── 01_data_analysis.md        # XML data analysis
├── 02_mongodb_schema.md       # MongoDB schema design
├── 03_neo4j_schema.md         # Neo4J schema design
└── diagrams/                  # Visual diagrams (optional)
    ├── er_diagram.png
    ├── mongodb_collections.png
    └── neo4j_graph.png
```

---

## Next Steps

1. **Review schemas** with project supervisors
2. **Implement ETL pipeline** in Python
3. **Load data** into both databases
4. **Develop NLP models** for interaction classification
5. **Run performance benchmarks**
6. **Document comparative analysis**

---

## References

- CIMA AEMPS: https://cima.aemps.es/cima/publico/nomenclator.html
- MongoDB Documentation: https://docs.mongodb.com/
- Neo4J Documentation: https://neo4j.com/docs/
- ATC Classification: WHO Collaborating Centre for Drug Statistics Methodology
