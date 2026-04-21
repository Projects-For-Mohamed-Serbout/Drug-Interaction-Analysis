# Neo4J Graph Schema Design

## Design Philosophy

Neo4J is ideal for:
- Modeling complex relationships between drugs, ingredients, and interactions
- Traversing drug interaction networks efficiently
- Finding paths between drugs through shared components
- Detecting interaction chains and therapeutic duplicities
- Answering relationship-based queries naturally

---

## Graph Model Overview

```
                                    ┌──────────────┐
                                    │  Laboratory  │
                                    └──────────────┘
                                           ▲
                                           │ MANUFACTURED_BY
                                           │ MARKETED_BY
                    ┌──────────────────────┴───────────────────────┐
                    │                                               │
              ┌─────┴─────┐                                   ┌─────┴─────┐
              │   Drug    │◄────── INTERACTS_WITH ────────────│   Drug    │
              └─────┬─────┘                                   └───────────┘
                    │
        ┌───────────┼───────────┬───────────────────┐
        │           │           │                   │
        ▼           ▼           ▼                   ▼
┌───────────┐ ┌───────────┐ ┌───────────┐   ┌───────────────┐
│ActiveIngr.│ │PharmForm  │ │ ATCCode   │   │AdminRoute     │
└───────────┘ └───────────┘ └───────────┘   └───────────────┘
                                  │
                                  │ PARENT_OF
                                  ▼
                            ┌───────────┐
                            │ ATCCode   │ (hierarchical)
                            └───────────┘
```

---

## Node Labels and Properties

### 1. Drug (Medicamento)

**Label:** `Drug`

```cypher
(:Drug {
  // Primary identifiers
  cod_nacion: "600000",           // Unique national code
  nro_definitivo: "66337",

  // Names
  nombre_comercial: "AMOXICILINA /ACIDO CLAVULANICO SALA 500/50 mg...",
  presentacion: "..., 100 viales",
  dosificacion: "500 mg/50 mg",

  // SNOMED codes
  cod_dcsa: "734844004",
  cod_dcp: "2431000140106",
  cod_dcpf: "2441000140100",

  // Package info
  contenido: 100,
  descripcion_contenido: "100 viales",

  // Classification flags
  es_psicotropo: false,
  es_estupefaciente: false,
  afecta_conduccion: false,
  triangulo_negro: false,
  requiere_receta: true,
  es_generico: true,
  es_sustituible: true,
  uso_hospitalario: true,
  diagnostico_hospitalario: false,
  es_huerfano: false,
  es_biosimilar: false,

  // Dates
  fecha_autorizacion: date("2004-09-16"),
  fecha_comercializacion: date("2012-01-02"),

  // Status
  comercializado: false,
  situacion_registro: "Suspenso",

  // URLs
  url_ficha_tecnica: "https://...",
  url_prospecto: "https://..."
})
```

### 2. ActiveIngredient (Principio Activo)

**Label:** `ActiveIngredient`

```cypher
(:ActiveIngredient {
  codigo: 160,
  codigo_aemps: "1A",
  nombre: "AMOXICILINA",
  lista_psicotropo: null   // or "Lista IV"
})
```

### 3. Laboratory (Laboratorio)

**Label:** `Laboratory`

```cypher
(:Laboratory {
  codigo: 2367,
  nombre: "LABORATORIOS SALA S.L.",
  direccion: "Calle Industrial, 10",
  codigo_postal: "28000",
  localidad: "Madrid",
  cif: "B12345678"
})
```

### 4. ATCCode (Clasificación ATC)

**Label:** `ATCCode`

```cypher
(:ATCCode {
  codigo: "J01CR02",
  descripcion: "Amoxicilina e inhibidor de la betalactamasa",
  nivel: 5
})
```

### 5. PharmaceuticalForm (Forma Farmacéutica)

**Label:** `PharmaceuticalForm`

```cypher
(:PharmaceuticalForm {
  codigo: 288,
  nombre: "POLVO PARA SOLUCION INYECTABLE Y PARA PERFUSION",
  codigo_simplificado: 34,
  nombre_simplificado: "INYECTABLE"
})
```

### 6. AdministrationRoute (Vía de Administración)

**Label:** `AdministrationRoute`

```cypher
(:AdministrationRoute {
  codigo: 49,
  nombre: "VÍA INTRAVENOSA"
})
```

### 7. Excipient (Excipiente)

**Label:** `Excipient`

```cypher
(:Excipient {
  codigo: 15305,
  nombre: "LACTOSA MONOHIDRATO"
})
```

### 8. PackageType (Tipo de Envase)

**Label:** `PackageType`

```cypher
(:PackageType {
  codigo: 45,
  nombre: "Vial"
})
```

### 9. Biomarker (Biomarcador)

**Label:** `Biomarker`

```cypher
(:Biomarker {
  nombre: "CYP2D6",
  clase: "Germinal"
})
```

---

## Relationship Types and Properties

### 1. CONTAINS (Drug → ActiveIngredient)

Drug contains active ingredient with dosage information.

```cypher
(drug:Drug)-[:CONTAINS {
  orden: 1,
  dosis: 500.0,
  unidad_dosis: "mg",
  dosis_composicion: 1,
  unidad_composicion: "vial para inyección",
  dosis_prescripcion: "500/50",
  unidad_prescripcion: "mg/mg"
}]->(ingredient:ActiveIngredient)
```

### 2. MANUFACTURED_BY (Drug → Laboratory)

Marketing authorization holder.

```cypher
(drug:Drug)-[:MANUFACTURED_BY]->(lab:Laboratory)
```

### 3. MARKETED_BY (Drug → Laboratory)

Commercializing laboratory.

```cypher
(drug:Drug)-[:MARKETED_BY]->(lab:Laboratory)
```

### 4. HAS_FORM (Drug → PharmaceuticalForm)

```cypher
(drug:Drug)-[:HAS_FORM]->(form:PharmaceuticalForm)
```

### 5. ADMINISTERED_VIA (Drug → AdministrationRoute)

```cypher
(drug:Drug)-[:ADMINISTERED_VIA]->(route:AdministrationRoute)
```

### 6. CLASSIFIED_AS (Drug → ATCCode)

```cypher
(drug:Drug)-[:CLASSIFIED_AS {
  teratogenia: "D - Medicamento desaconsejado..."  // Optional warning
}]->(atc:ATCCode)
```

### 7. CONTAINS_EXCIPIENT (Drug → Excipient)

```cypher
(drug:Drug)-[:CONTAINS_EXCIPIENT]->(excipient:Excipient)
```

### 8. PACKAGED_IN (Drug → PackageType)

```cypher
(drug:Drug)-[:PACKAGED_IN]->(package:PackageType)
```

### 9. INTERACTS_WITH (Drug ↔ Drug or Drug → ATCCode) ⭐ CRITICAL

**This is the most important relationship for the project!**

```cypher
(drug1:Drug)-[:INTERACTS_WITH {
  // Original text data
  efecto: "Aumento del riesgo de arritmias ventriculares.",
  recomendacion: "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",

  // NLP-extracted properties (to be added during processing)
  severidad: "alta",              // alta, media, baja
  tipo: "contraindicada",         // contraindicada, precaucion, monitorizar
  mecanismo: "prolongacion_qt",
  categoria_efecto: "cardiovascular",

  // Metadata
  procesado_nlp: true,
  confianza_nlp: 0.95,
  fecha_procesado: date("2024-12-16")
}]->(drug2:Drug)

// OR interaction with ATC code (when specific drug not known)
(drug:Drug)-[:INTERACTS_WITH_ATC {
  atc_interaccion: "A03FA03",
  medicamento_nombre: "domperidona",
  efecto: "...",
  recomendacion: "...",
  severidad: "alta",
  tipo: "contraindicada"
}]->(atc:ATCCode)
```

### 10. DUPLICATES_WITH (Drug → ATCCode)

Therapeutic duplicity warning.

```cypher
(drug:Drug)-[:DUPLICATES_WITH {
  descripcion: "ANTIBACTERIANOS BETALACTÁMICOS, PENICILINAS",
  efecto: "Prescripción de dos o más medicamentos con el mismo principio activo...",
  recomendacion: "Suspender el principio(s) activo(s) con la misma actividad farmacológica."
}]->(atc:ATCCode)
```

### 11. PARENT_OF (ATCCode → ATCCode)

ATC hierarchical relationship.

```cypher
(parent:ATCCode)-[:PARENT_OF]->(child:ATCCode)

// Example: J01 → J01C → J01CR → J01CR02
(:ATCCode {codigo: "J01"})-[:PARENT_OF]->(:ATCCode {codigo: "J01C"})
```

### 12. HAS_GERIATRIC_WARNING (Drug → GeriatricWarning)

```cypher
(drug:Drug)-[:HAS_GERIATRIC_WARNING {
  alerta: "Pacientes con hiponatremia no iatrogénica (< 130 mmol/l)",
  riesgo: "Riesgo de hiponatremia severa.",
  recomendacion: "Evitar su utilización..."
}]->(warning)
```

### 13. HAS_BIOMARKER (Drug → Biomarker)

```cypher
(drug:Drug)-[:HAS_BIOMARKER {
  genotipo_fenotipo: "Metabolizadores ultrarrápidos",
  secciones_ft: "4.5 Interacción con otros medicamentos...",
  descripcion: "Ver NOTAS para ampliar información",
  notas: "De acuerdo con las indicaciones de la guía clínica CPIC...",
  inclusion_sns: true
}]->(biomarker:Biomarker)
```

---

## Complete Graph Schema Visualization

```
                                    ┌─────────────────┐
                                    │   Laboratory    │
                                    │  codigo: 2367   │
                                    │  nombre: "..."  │
                                    └────────▲────────┘
                                             │
                              MANUFACTURED_BY│MARKETED_BY
                                             │
┌─────────────────┐                ┌─────────┴─────────┐                ┌─────────────────┐
│ ActiveIngredient│◄──CONTAINS────│       Drug        │────INTERACTS───▶│      Drug       │
│  codigo: 160    │               │ cod_nacion: "..." │    _WITH        │ cod_nacion: "..." │
│  nombre: "..."  │               │ nombre: "..."     │                 │ nombre: "..."   │
└─────────────────┘               └────────┬──────────┘                 └─────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
          ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
          │PharmaceuticalForm│    │    ATCCode      │    │AdministrationRoute│
          │  codigo: 288    │    │ codigo: "J01CR02"│    │  codigo: 49     │
          │  nombre: "..."  │    │ descripcion: ... │    │  nombre: "..."  │
          └─────────────────┘    └────────┬────────┘    └─────────────────┘
                                          │
                                   PARENT_OF
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │    ATCCode      │
                                 │ codigo: "J01CR" │
                                 └────────┬────────┘
                                          │
                                   PARENT_OF
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │    ATCCode      │
                                 │  codigo: "J01C" │
                                 └─────────────────┘
```

---

## Indexes and Constraints

### Unique Constraints

```cypher
// Drug unique constraint
CREATE CONSTRAINT drug_cod_nacion IF NOT EXISTS
FOR (d:Drug) REQUIRE d.cod_nacion IS UNIQUE;

// Active ingredient unique constraint
CREATE CONSTRAINT ingredient_codigo IF NOT EXISTS
FOR (a:ActiveIngredient) REQUIRE a.codigo IS UNIQUE;

// Laboratory unique constraint
CREATE CONSTRAINT lab_codigo IF NOT EXISTS
FOR (l:Laboratory) REQUIRE l.codigo IS UNIQUE;

// ATC code unique constraint
CREATE CONSTRAINT atc_codigo IF NOT EXISTS
FOR (a:ATCCode) REQUIRE a.codigo IS UNIQUE;

// Pharmaceutical form unique constraint
CREATE CONSTRAINT form_codigo IF NOT EXISTS
FOR (p:PharmaceuticalForm) REQUIRE p.codigo IS UNIQUE;

// Administration route unique constraint
CREATE CONSTRAINT route_codigo IF NOT EXISTS
FOR (r:AdministrationRoute) REQUIRE r.codigo IS UNIQUE;

// Excipient unique constraint
CREATE CONSTRAINT excipient_codigo IF NOT EXISTS
FOR (e:Excipient) REQUIRE e.codigo IS UNIQUE;

// Package type unique constraint
CREATE CONSTRAINT package_codigo IF NOT EXISTS
FOR (p:PackageType) REQUIRE p.codigo IS UNIQUE;
```

### Performance Indexes

```cypher
// Drug indexes
CREATE INDEX drug_nombre IF NOT EXISTS FOR (d:Drug) ON (d.nombre_comercial);
CREATE INDEX drug_generico IF NOT EXISTS FOR (d:Drug) ON (d.es_generico);
CREATE INDEX drug_comercializado IF NOT EXISTS FOR (d:Drug) ON (d.comercializado);
CREATE INDEX drug_uso_hospitalario IF NOT EXISTS FOR (d:Drug) ON (d.uso_hospitalario);

// Full-text search index
CREATE FULLTEXT INDEX drug_search IF NOT EXISTS
FOR (d:Drug) ON EACH [d.nombre_comercial, d.presentacion];

// Active ingredient name search
CREATE INDEX ingredient_nombre IF NOT EXISTS FOR (a:ActiveIngredient) ON (a.nombre);

// ATC description search
CREATE INDEX atc_descripcion IF NOT EXISTS FOR (a:ATCCode) ON (a.descripcion);
```

---

## Sample Cypher Queries

### Query 1: Find all interactions for a specific drug

```cypher
MATCH (d:Drug {cod_nacion: "600023"})-[r:INTERACTS_WITH]->(other:Drug)
RETURN d.nombre_comercial AS medicamento,
       other.nombre_comercial AS interactua_con,
       r.efecto AS efecto,
       r.recomendacion AS recomendacion,
       r.severidad AS severidad
```

### Query 2: Find interaction chain (drugs that interact with drugs that interact with X)

```cypher
MATCH path = (d:Drug {cod_nacion: "600023"})-[:INTERACTS_WITH*1..2]-(other:Drug)
RETURN path
```

### Query 3: Find drugs with common active ingredient

```cypher
MATCH (d1:Drug)-[:CONTAINS]->(a:ActiveIngredient)<-[:CONTAINS]-(d2:Drug)
WHERE d1.cod_nacion = "600023" AND d1 <> d2
RETURN d2.nombre_comercial AS medicamento_similar,
       a.nombre AS principio_activo_comun
```

### Query 4: Find all high-severity interactions

```cypher
MATCH (d1:Drug)-[r:INTERACTS_WITH {severidad: "alta"}]->(d2:Drug)
RETURN d1.nombre_comercial AS medicamento1,
       d2.nombre_comercial AS medicamento2,
       r.efecto AS efecto,
       r.tipo AS tipo
ORDER BY d1.nombre_comercial
```

### Query 5: Find drugs by ATC classification (including child codes)

```cypher
MATCH (parent:ATCCode {codigo: "J01C"})-[:PARENT_OF*0..]->(child:ATCCode)<-[:CLASSIFIED_AS]-(d:Drug)
RETURN d.nombre_comercial, child.codigo AS atc
```

### Query 6: Find potential drug-drug interactions in a patient's medication list

```cypher
// Given a list of drug codes for a patient
WITH ["600023", "600000", "600017"] AS patient_drugs
MATCH (d1:Drug)-[r:INTERACTS_WITH]->(d2:Drug)
WHERE d1.cod_nacion IN patient_drugs AND d2.cod_nacion IN patient_drugs
RETURN d1.nombre_comercial AS drug1,
       d2.nombre_comercial AS drug2,
       r.severidad AS severidad,
       r.efecto AS efecto
```

### Query 7: Find all drugs manufactured by a specific laboratory

```cypher
MATCH (d:Drug)-[:MANUFACTURED_BY]->(l:Laboratory {codigo: 2367})
RETURN d.nombre_comercial, d.comercializado
ORDER BY d.nombre_comercial
```

### Query 8: Find generic alternatives for a drug

```cypher
MATCH (d:Drug {cod_nacion: "600023"})-[:CONTAINS]->(a:ActiveIngredient)
WITH d, COLLECT(a) AS ingredients
MATCH (alt:Drug)-[:CONTAINS]->(ai:ActiveIngredient)
WHERE alt <> d AND alt.es_generico = true AND ai IN ingredients
WITH d, alt, COUNT(ai) AS shared_ingredients, SIZE(ingredients) AS total_ingredients
WHERE shared_ingredients = total_ingredients
RETURN alt.nombre_comercial AS alternativa_generica,
       alt.cod_nacion
```

### Query 9: Network analysis - most connected drugs (interaction hubs)

```cypher
MATCH (d:Drug)-[r:INTERACTS_WITH]-()
WITH d, COUNT(r) AS num_interactions
ORDER BY num_interactions DESC
LIMIT 20
RETURN d.nombre_comercial, d.cod_nacion, num_interactions
```

### Query 10: Find contraindicated combinations for cardiovascular patients

```cypher
MATCH (d1:Drug)-[r:INTERACTS_WITH]->(d2:Drug)
WHERE r.tipo = "contraindicada"
  AND r.categoria_efecto = "cardiovascular"
RETURN d1.nombre_comercial, d2.nombre_comercial, r.efecto
```

---

## Graph Data Model Advantages for This Project

### 1. Natural Relationship Modeling
- Drug interactions are naturally bidirectional relationships
- ATC hierarchy is naturally a tree structure
- Drug composition is a natural graph of components

### 2. Efficient Traversal Queries
- Find interaction chains: `(Drug)-[:INTERACTS_WITH*1..3]-(Drug)`
- Find therapeutic alternatives: drugs sharing ingredients
- Network analysis for identifying critical interaction hubs

### 3. Pattern Matching
- Identify clusters of interacting drugs
- Find common interaction patterns
- Detect potential polypharmacy risks

### 4. Scalability for Complex Queries
- No expensive JOINs needed
- Relationship-based queries are native
- Index-free adjacency for fast traversal

---

## Neo4J Connection Configuration

```python
# Python configuration example
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "your_password",
    "database": "drug_interactions"
}
```

---

## Comparison: When to Use Neo4J vs MongoDB

| Use Case | Best Choice | Reason |
|----------|-------------|--------|
| Full drug profile retrieval | MongoDB | Document-oriented, single read |
| Find all interactions for a drug | Neo4J | Graph traversal is native |
| Text search in drug names | MongoDB | Better text indexing |
| Interaction network analysis | Neo4J | Path algorithms, centrality |
| Find alternative drugs | Neo4J | Pattern matching on ingredients |
| Bulk data export | MongoDB | Better for document streaming |
| Find interaction chains | Neo4J | Variable-length path queries |
| NLP-processed text storage | MongoDB | Flexible schema for NLP results |
| Therapeutic duplicity detection | Neo4J | ATC hierarchy traversal |
| Simple CRUD operations | MongoDB | Simpler queries |
