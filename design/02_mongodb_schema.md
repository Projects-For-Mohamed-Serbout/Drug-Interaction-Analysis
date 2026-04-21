# MongoDB Schema Design

## Design Philosophy

MongoDB is ideal for:
- Storing complete drug documents with all nested information
- Fast retrieval of full drug profiles
- Flexible schema for varying drug attributes
- Efficient text search for NLP-processed fields

## Collections Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        MongoDB Collections                       │
├─────────────────────────────────────────────────────────────────┤
│  drugs              │ Main collection - complete drug documents │
│  active_ingredients │ Reference collection - principios activos │
│  laboratories       │ Reference collection - laboratorios       │
│  atc_codes          │ Reference collection - ATC classification │
│  pharmaceutical_forms│ Reference collection - formas farmacéuticas│
│  administration_routes│ Reference collection - vías administración│
│  excipients         │ Reference collection - excipientes        │
│  package_types      │ Reference collection - envases            │
│  content_units      │ Reference collection - unidades contenido │
│  registration_statuses│ Reference collection - situaciones registro│
│  drug_interactions  │ Denormalized interactions for fast queries│
└─────────────────────────────────────────────────────────────────┘
```

---

## Collection 1: `drugs` (Main Collection)

```javascript
{
  // Primary identifiers
  "_id": ObjectId("..."),
  "cod_nacion": "600000",           // National code (indexed, unique)
  "nro_definitivo": "66337",        // Definitive number

  // Names and descriptions
  "nombre_comercial": "AMOXICILINA /ACIDO CLAVULANICO SALA 500/50 mg POLVO PARA SOLUCION INYECTABLE Y PARA PERFUSION EFG",
  "presentacion": "AMOXICILINA /ACIDO CLAVULANICO SALA 500/50 mg..., 100 viales",
  "dosificacion": "500 mg/50 mg",

  // SNOMED CT codes
  "snomed": {
    "dcsa": "734844004",            // Substance code
    "dcp": "2431000140106",         // Clinical drug code
    "dcpf": "2441000140100"         // Clinical drug + form code
  },

  // Package information
  "envase": {
    "codigo": 45,
    "tipo": "Vial",                 // Denormalized for faster queries
    "contenido": 100,
    "unidad_contenido_codigo": 34,
    "unidad_contenido": "viales",   // Denormalized
    "descripcion": "100 viales"
  },

  // Classification flags
  "clasificacion": {
    "psicotropo": false,
    "estupefaciente": false,
    "afecta_conduccion": false,
    "triangulo_negro": false,
    "requiere_receta": true,
    "generico": true,
    "sustituible": true,
    "envase_clinico": true,
    "uso_hospitalario": true,
    "diagnostico_hospitalario": false,
    "tratamiento_larga_duracion": false,
    "control_medico_especial": false,
    "huerfano": false,
    "base_plantas": false,
    "biosimilar": false,
    "importacion_paralela": false,
    "radiofarmaco": false,
    "serializacion": true
  },

  // Laboratory references (embedded for denormalization)
  "laboratorio_titular": {
    "codigo": 2367,
    "nombre": "LABORATORIOS SALA S.L."  // Denormalized
  },
  "laboratorio_comercializador": {
    "codigo": 2367,
    "nombre": "LABORATORIOS SALA S.L."  // Denormalized
  },

  // Dates and status
  "fechas": {
    "autorizacion": ISODate("2004-09-16"),
    "comercializacion": ISODate("2012-01-02"),
    "situacion_registro": ISODate("2020-08-11")
  },
  "comercializado": false,
  "situacion_registro": {
    "codigo": 4,
    "descripcion": "Suspenso"       // Denormalized
  },

  // URLs
  "documentos": {
    "ficha_tecnica": "https://cima.aemps.es/cima/pdfs/es/ft/66337/66337_ft.pdf",
    "prospecto": "https://cima.aemps.es/cima/pdfs/es/p/66337/66337_p.pdf"
  },

  // Pharmaceutical forms (embedded array)
  "formas_farmaceuticas": [
    {
      "codigo": 288,
      "nombre": "POLVO PARA SOLUCION INYECTABLE Y PARA PERFUSION",
      "codigo_simplificado": 34,
      "nombre_simplificado": "INYECTABLE",
      "numero_principios_activos": 2,

      // Active ingredients composition
      "composicion": [
        {
          "principio_activo": {
            "codigo": 160,
            "nombre": "AMOXICILINA"
          },
          "orden": 1,
          "dosis": {
            "cantidad": 500,
            "unidad": "mg"
          },
          "composicion": {
            "cantidad": 1,
            "unidad": "vial para inyección"
          },
          "administracion": {
            "cantidad": 1,
            "unidad": "vial para inyección"
          },
          "prescripcion": {
            "dosis": "500/50",
            "unidad": "mg/mg"
          }
        },
        {
          "principio_activo": {
            "codigo": 5418,
            "nombre": "ACIDO CLAVULANICO"
          },
          "orden": 2,
          "dosis": {
            "cantidad": 50,
            "unidad": "mg"
          },
          "composicion": {
            "cantidad": 1,
            "unidad": "vial para inyección"
          },
          "administracion": {
            "cantidad": 1,
            "unidad": "vial para inyección"
          },
          "prescripcion": {
            "dosis": "500/50",
            "unidad": "mg/mg"
          }
        }
      ],

      // Excipients
      "excipientes": [],

      // Administration routes
      "vias_administracion": [
        {
          "codigo": 49,
          "nombre": "VÍA INTRAVENOSA"
        }
      ]
    }
  ],

  // ATC Classification (embedded)
  "atc": {
    "codigo": "J01CR02",
    "descripcion": "Amoxicilina e inhibidor de la betalactamasa",
    "teratogenia": null,

    // Drug interactions - CRITICAL FOR NLP
    "interacciones": [
      {
        "atc_interaccion": "A03FA03",
        "medicamento": "domperidona",
        "efecto": "Aumento del riesgo de arritmias ventriculares.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        // NLP-extracted fields (to be added later)
        "nlp": {
          "severidad": null,          // To be filled by NLP: "alta", "media", "baja"
          "tipo_accion": null,        // To be filled by NLP: "contraindicada", "precaucion", "monitorizar"
          "mecanismo": null,          // To be filled by NLP
          "categoria_efecto": null    // To be filled by NLP: "cardiovascular", "neurologico", etc.
        }
      }
    ],

    // Therapeutic duplicities
    "duplicidades": [
      {
        "atc_duplicidad": "J01C",
        "descripcion": "ANTIBACTERIANOS BETALACTÁMICOS, PENICILINAS",
        "efecto": "Prescripción de dos o más medicamentos con el mismo principio activo o la misma actividad farmacológica.",
        "recomendacion": "Suspender el principio(s) activo(s) con la misma actividad farmacológica."
      }
    ],

    // Geriatric warnings
    "alertas_geriatria": []
  },

  // Biomarkers
  "biomarcadores": [
    {
      "clase": "Germinal",
      "marcador": "CYP2D6",
      "genotipo_fenotipo": "Metabolizadores ultrarrápidos",
      "secciones_ficha_tecnica": ["4.5 Interacción con otros medicamentos", "5.2 Propiedades farmacocinéticas"],
      "descripcion": "Ver NOTAS para ampliar información",
      "inclusion_sns": true,
      "notas": "De acuerdo con las indicaciones de la guía clínica CPIC..."
    }
  ],

  // Supply problems
  "problemas_suministro": [
    {
      "fecha_inicio": ISODate("2017-06-01"),
      "fecha_fin": null,
      "observaciones": "Existe/n otro/s medicamento/s con los mismos principios activos..."
    }
  ],

  // Metadata
  "metadata": {
    "fecha_carga": ISODate("2024-12-16"),
    "version_datos": "2024-12-16",
    "procesado_nlp": false
  }
}
```

---

## Collection 2: `active_ingredients` (Reference)

```javascript
{
  "_id": ObjectId("..."),
  "codigo": 160,                          // nroprincipioactivo
  "codigo_aemps": "1A",                   // codigoprincipioactivo
  "nombre": "AMOXICILINA",                // principioactivo
  "lista_psicotropo": null,               // Optional: "Lista IV"

  // Aggregated data (updated periodically)
  "estadisticas": {
    "total_medicamentos": 450,
    "medicamentos_comercializados": 320
  }
}
```

**Indexes:**
```javascript
db.active_ingredients.createIndex({ "codigo": 1 }, { unique: true })
db.active_ingredients.createIndex({ "nombre": "text" })
```

---

## Collection 3: `laboratories` (Reference)

```javascript
{
  "_id": ObjectId("..."),
  "codigo": 2367,
  "nombre": "LABORATORIOS SALA S.L.",
  "direccion": "Calle Industrial, 10",
  "codigo_postal": "28000",
  "localidad": "Madrid",
  "cif": "B12345678",

  // Aggregated data
  "estadisticas": {
    "total_medicamentos_titular": 25,
    "total_medicamentos_comercializador": 25
  }
}
```

**Indexes:**
```javascript
db.laboratories.createIndex({ "codigo": 1 }, { unique: true })
db.laboratories.createIndex({ "nombre": "text" })
```

---

## Collection 4: `atc_codes` (Reference)

```javascript
{
  "_id": ObjectId("..."),
  "codigo": "J01CR02",                    // ATC code
  "descripcion": "Amoxicilina e inhibidor de la betalactamasa",
  "nivel": 5,                             // Level in ATC hierarchy (1-5)
  "jerarquia": {
    "nivel1": { "codigo": "J", "descripcion": "ANTIINFECCIOSOS PARA USO SISTÉMICO" },
    "nivel2": { "codigo": "J01", "descripcion": "ANTIBACTERIANOS PARA USO SISTÉMICO" },
    "nivel3": { "codigo": "J01C", "descripcion": "ANTIBACTERIANOS BETALACTÁMICOS, PENICILINAS" },
    "nivel4": { "codigo": "J01CR", "descripcion": "Combinaciones de penicilinas incl. inhibidores betalactamasa" },
    "nivel5": { "codigo": "J01CR02", "descripcion": "Amoxicilina e inhibidor de la betalactamasa" }
  }
}
```

**Indexes:**
```javascript
db.atc_codes.createIndex({ "codigo": 1 }, { unique: true })
db.atc_codes.createIndex({ "descripcion": "text" })
db.atc_codes.createIndex({ "jerarquia.nivel1.codigo": 1 })
```

---

## Collection 5: `drug_interactions` (Denormalized for Fast Queries)

This collection stores flattened interaction data for efficient querying and analysis.

```javascript
{
  "_id": ObjectId("..."),

  // Source drug
  "medicamento_origen": {
    "cod_nacion": "600023",
    "nombre": "CITALVIR 20 mg COMPRIMIDOS",
    "atc": "N06AB04"
  },

  // Target drug/ATC
  "medicamento_destino": {
    "atc": "A03FA03",
    "nombre": "domperidona"
  },

  // Interaction details
  "interaccion": {
    "efecto": "Aumento del riesgo de arritmias ventriculares.",
    "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",

    // NLP-processed fields
    "nlp": {
      "severidad": "alta",
      "tipo": "contraindicada",
      "categoria_efecto": "cardiovascular",
      "mecanismo": "prolongacion_qt",
      "procesado": true,
      "fecha_procesado": ISODate("2024-12-16"),
      "confianza": 0.95
    }
  },

  // Bidirectional flag
  "bidireccional": true
}
```

**Indexes:**
```javascript
db.drug_interactions.createIndex({ "medicamento_origen.cod_nacion": 1 })
db.drug_interactions.createIndex({ "medicamento_origen.atc": 1 })
db.drug_interactions.createIndex({ "medicamento_destino.atc": 1 })
db.drug_interactions.createIndex({ "interaccion.nlp.severidad": 1 })
db.drug_interactions.createIndex({ "interaccion.nlp.tipo": 1 })
db.drug_interactions.createIndex({ "interaccion.efecto": "text", "interaccion.recomendacion": "text" })
```

---

## Other Reference Collections

### `pharmaceutical_forms`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 288,
  "nombre": "POLVO PARA SOLUCION INYECTABLE Y PARA PERFUSION",
  "codigo_simplificado": 34
}
```

### `administration_routes`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 49,
  "nombre": "VÍA INTRAVENOSA"
}
```

### `excipients`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 15305,
  "nombre": "LACTOSA MONOHIDRATO"
}
```

### `package_types`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 45,
  "nombre": "Vial"
}
```

### `content_units`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 34,
  "nombre": "viales"
}
```

### `registration_statuses`
```javascript
{
  "_id": ObjectId("..."),
  "codigo": 1,
  "descripcion": "Autorizado"
}
```

---

## Indexes Strategy

### Primary Indexes for `drugs` Collection

```javascript
// Unique identifier
db.drugs.createIndex({ "cod_nacion": 1 }, { unique: true })

// Common query patterns
db.drugs.createIndex({ "nro_definitivo": 1 })
db.drugs.createIndex({ "atc.codigo": 1 })
db.drugs.createIndex({ "laboratorio_titular.codigo": 1 })
db.drugs.createIndex({ "laboratorio_comercializador.codigo": 1 })
db.drugs.createIndex({ "formas_farmaceuticas.composicion.principio_activo.codigo": 1 })
db.drugs.createIndex({ "situacion_registro.codigo": 1 })
db.drugs.createIndex({ "comercializado": 1 })

// Text search for drug names
db.drugs.createIndex({
  "nombre_comercial": "text",
  "presentacion": "text"
})

// Compound indexes for common queries
db.drugs.createIndex({
  "clasificacion.uso_hospitalario": 1,
  "comercializado": 1
})

db.drugs.createIndex({
  "atc.codigo": 1,
  "comercializado": 1
})

// For interaction queries
db.drugs.createIndex({ "atc.interacciones.atc_interaccion": 1 })
```

---

## Sample Queries

### Query 1: Find all drugs with a specific active ingredient
```javascript
db.drugs.find({
  "formas_farmaceuticas.composicion.principio_activo.codigo": 160
})
```

### Query 2: Find all interactions for a specific drug
```javascript
db.drugs.aggregate([
  { $match: { "cod_nacion": "600023" } },
  { $unwind: "$atc.interacciones" },
  { $project: {
    nombre: "$nombre_comercial",
    interaccion: "$atc.interacciones"
  }}
])
```

### Query 3: Find high-severity interactions (after NLP processing)
```javascript
db.drug_interactions.find({
  "interaccion.nlp.severidad": "alta",
  "interaccion.nlp.tipo": "contraindicada"
})
```

### Query 4: Full-text search for drug names
```javascript
db.drugs.find({
  $text: { $search: "amoxicilina clavulanico" }
})
```

### Query 5: Find all drugs from a laboratory
```javascript
db.drugs.find({
  "laboratorio_titular.codigo": 2367,
  "comercializado": true
})
```

---

## Data Validation Schema

```javascript
db.createCollection("drugs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cod_nacion", "nombre_comercial"],
      properties: {
        cod_nacion: {
          bsonType: "string",
          description: "National code - required and unique"
        },
        nombre_comercial: {
          bsonType: "string",
          description: "Commercial name - required"
        },
        atc: {
          bsonType: "object",
          properties: {
            codigo: { bsonType: "string" },
            interacciones: {
              bsonType: "array",
              items: {
                bsonType: "object",
                required: ["atc_interaccion", "efecto"],
                properties: {
                  atc_interaccion: { bsonType: "string" },
                  efecto: { bsonType: "string" },
                  recomendacion: { bsonType: "string" }
                }
              }
            }
          }
        }
      }
    }
  }
})
```

---

## MongoDB Connection Configuration

```python
# Python configuration example
MONGODB_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "drug_interactions_db",
    "collections": {
        "drugs": "drugs",
        "active_ingredients": "active_ingredients",
        "laboratories": "laboratories",
        "atc_codes": "atc_codes",
        "pharmaceutical_forms": "pharmaceutical_forms",
        "administration_routes": "administration_routes",
        "excipients": "excipients",
        "package_types": "package_types",
        "content_units": "content_units",
        "registration_statuses": "registration_statuses",
        "drug_interactions": "drug_interactions"
    }
}
```
