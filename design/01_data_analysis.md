# Data Analysis - CIMA Drug Dataset

## Overview

This document analyzes the XML data from CIMA (Centro de Información de Medicamentos) provided by AEMPS (Agencia Española de Medicamentos y Productos Sanitarios).

## Source Files

| File | Description | Key Fields |
|------|-------------|------------|
| `Prescripcion.xml` | Main prescription data with drugs, compositions, interactions | cod_nacion, nro_definitivo, des_nomco, etc. |
| `DICCIONARIO_PRINCIPIOS_ACTIVOS.xml` | Active ingredients dictionary | nroprincipioactivo, codigoprincipioactivo, principioactivo |
| `DICCIONARIO_LABORATORIOS.xml` | Laboratories/manufacturers | codigolaboratorio, laboratorio, direccion, cif |
| `DICCIONARIO_ATC.xml` | ATC classification codes | nroatc, codigoatc, descatc |
| `DICCIONARIO_FORMA_FARMACEUTICA.xml` | Pharmaceutical forms | codigoformafarmaceutica, formafarmaceutica |
| `DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.xml` | Simplified pharmaceutical forms | codigoformafarmaceuticasimplificada, formafarmaceuticasimplificada |
| `DICCIONARIO_VIAS_ADMINISTRACION.xml` | Administration routes | codigoviaadministracion, viaadministracion |
| `DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.xml` | Mandatory declaration excipients | codigoedo, edo |
| `DICCIONARIO_ENVASES.xml` | Package types | codigoenvase, envase |
| `DICCIONARIO_SITUACION_REGISTRO.xml` | Registration status | codigosituacionregistro, situacionregistro |
| `DICCIONARIO_DCSA.xml` | SNOMED CT substance codes | codigodcsa, nombredcsa |
| `DICCIONARIO_DCP.xml` | SNOMED CT clinical drug codes | codigodcp, nombredcp, codigodcsa |
| `DICCIONARIO_DCPF.xml` | SNOMED CT clinical drug + form codes | codigodcpf, nombredcpf, codigodcp |
| `DICCIONARIO_UNIDAD_CONTENIDO.xml` | Content units | codigounidadcontenido, unidadcontenido |

---

## Main Entity: Prescription (Drug/Medication)

### Basic Information
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `cod_nacion` | String | National code (unique identifier) | "600000" |
| `nro_definitivo` | String | Definitive number | "66337" |
| `des_nomco` | String | Commercial name | "AMOXICILINA /ACIDO CLAVULANICO SALA 500/50 mg..." |
| `des_prese` | String | Presentation description | "AMOXICILINA /ACIDO CLAVULANICO SALA..., 100 viales" |
| `des_dosific` | String | Dosage description | "500 mg/50 mg" |

### SNOMED CT Codes
| Field | Type | Description |
|-------|------|-------------|
| `cod_dcsa` | String | SNOMED CT Substance Code |
| `cod_dcp` | String | SNOMED CT Clinical Drug Code |
| `cod_dcpf` | String | SNOMED CT Clinical Drug + Form Code |

### Package Information
| Field | Type | Description |
|-------|------|-------------|
| `cod_envase` | Integer | Package type code (FK to DICCIONARIO_ENVASES) |
| `contenido` | Integer | Content quantity |
| `unid_contenido` | Integer | Content unit code (FK to DICCIONARIO_UNIDAD_CONTENIDO) |
| `nro_conte` | String | Content description |

### Drug Classification Flags (Boolean: 0/1)
| Field | Description |
|-------|-------------|
| `sw_psicotropo` | Psychotropic substance |
| `sw_estupefaciente` | Narcotic substance |
| `sw_afecta_conduccion` | Affects driving ability |
| `sw_triangulo_negro` | Black triangle (additional monitoring) |
| `sw_receta` | Requires prescription |
| `sw_generico` | Generic drug |
| `sw_sustituible` | Substitutable |
| `sw_envase_clinico` | Clinical packaging |
| `sw_uso_hospitalario` | Hospital use only |
| `sw_diagnostico_hospitalario` | Hospital diagnosis required |
| `sw_tld` | Long-term treatment |
| `sw_especial_control_medico` | Special medical control |
| `sw_huerfano` | Orphan drug |
| `sw_base_a_plantas` | Plant-based |
| `biosimilar` | Biosimilar drug |
| `importacion_paralela` | Parallel import |
| `radiofarmaco` | Radiopharmaceutical |
| `serializacion` | Serialization required |

### Laboratory References
| Field | Type | Description |
|-------|------|-------------|
| `laboratorio_titular` | Integer | Marketing authorization holder (FK to DICCIONARIO_LABORATORIOS) |
| `laboratorio_comercializador` | Integer | Marketer (FK to DICCIONARIO_LABORATORIOS) |

### Dates and Status
| Field | Type | Description |
|-------|------|-------------|
| `fecha_autorizacion` | Date | Authorization date |
| `sw_comercializado` | Boolean | Is marketed |
| `fec_comer` | Date | Marketing date |
| `cod_sitreg` | Integer | Registration status (FK to DICCIONARIO_SITUACION_REGISTRO) |
| `cod_sitreg_presen` | Integer | Presentation registration status |
| `fecha_situacion_registro` | Date | Registration status date |
| `fec_sitreg_presen` | Date | Presentation registration status date |

### URLs
| Field | Description |
|-------|-------------|
| `url_fictec` | Technical datasheet URL |
| `url_prosp` | Prospect/leaflet URL |

---

## Nested Structures in Prescription

### 1. Pharmaceutical Forms (`formasfarmaceuticas`)
```xml
<formasfarmaceuticas>
  <cod_forfar>288</cod_forfar>                    <!-- FK to DICCIONARIO_FORMA_FARMACEUTICA -->
  <cod_forfar_simplificada>34</cod_forfar_simplificada>  <!-- FK to simplified forms -->
  <nro_pactiv>2</nro_pactiv>                      <!-- Number of active ingredients -->
  <composicion_pa>...</composicion_pa>            <!-- Active ingredient composition (1..N) -->
  <excipientes>...</excipientes>                  <!-- Excipients (0..N) -->
  <viasadministracion>...</viasadministracion>    <!-- Administration routes (1..N) -->
</formasfarmaceuticas>
```

### 2. Active Ingredient Composition (`composicion_pa`)
```xml
<composicion_pa>
  <cod_principio_activo>160</cod_principio_activo>  <!-- FK to DICCIONARIO_PRINCIPIOS_ACTIVOS -->
  <orden_colacion>1</orden_colacion>
  <dosis_pa>500</dosis_pa>
  <unidad_dosis_pa>mg</unidad_dosis_pa>
  <dosis_composicion>1</dosis_composicion>
  <unidad_composicion>vial para inyección</unidad_composicion>
  <dosis_administracion>1</dosis_administracion>
  <unidad_administracion>vial para inyección</unidad_administracion>
  <dosis_prescripcion>500/50</dosis_prescripcion>
  <unidad_prescripcion>mg/mg</unidad_prescripcion>
  <!-- Optional for liquid forms -->
  <cantidad_volumen_unidad_administracion>2</cantidad_volumen_unidad_administracion>
  <unidad_volumen_unidad_administracion>ml</unidad_volumen_unidad_administracion>
</composicion_pa>
```

### 3. ATC Classification (`atc`)
```xml
<atc>
  <cod_atc>J01CR02</cod_atc>                       <!-- ATC code -->
  <teratogenia>D - Medicamento desaconsejado...</teratogenia>  <!-- Teratogenicity warning -->
  <interacciones_atc>...</interacciones_atc>      <!-- Drug interactions (0..N) - CRITICAL! -->
  <duplicidades>...</duplicidades>                 <!-- Duplicity warnings (0..N) -->
  <desaconsejados_geriatria>...</desaconsejados_geriatria>  <!-- Geriatric warnings (0..N) -->
</atc>
```

### 4. Drug Interactions (`interacciones_atc`) - KEY FOR NLP PROJECT
```xml
<interacciones_atc>
  <atc_interaccion>A03FA03</atc_interaccion>       <!-- ATC code of interacting drug -->
  <descripcion_atc_interaccion>domperidona</descripcion_atc_interaccion>  <!-- Drug name -->
  <efecto_interaccion>Aumento del riesgo de arritmias ventriculares.</efecto_interaccion>  <!-- Effect -->
  <recomendacion_interaccion>Asociación contraindicada. Se recomienda suspender...</recomendacion_interaccion>  <!-- Recommendation -->
</interacciones_atc>
```

### 5. Duplicities (`duplicidades`)
```xml
<duplicidades>
  <atc_duplicidad>J01C</atc_duplicidad>
  <descripcion_atc_duplicidad>ANTIBACTERIANOS BETALACTÁMICOS, PENICILINAS</descripcion_atc_duplicidad>
  <efecto_duplicidad>Prescripción de dos o más medicamentos con el mismo principio activo...</efecto_duplicidad>
  <recomendacion_duplicidad>Suspender el principio(s) activo(s) con la misma actividad farmacológica.</recomendacion_duplicidad>
</duplicidades>
```

### 6. Geriatric Warnings (`desaconsejados_geriatria`)
```xml
<desaconsejados_geriatria>
  <alerta_geriatria>Pacientes con hiponatremia no iatrogénica (< 130 mmol/l)</alerta_geriatria>
  <riesgo_pacience_geriatria>Riesgo de hiponatremia severa.</riesgo_pacience_geriatria>
  <recomendacion_geriatria>Evitar su utilización. En caso de necesitar un antidepresivo...</recomendacion_geriatria>
</desaconsejados_geriatria>
```

### 7. Biomarkers (`biomarcadores`)
```xml
<biomarcadores>
  <clase>Germinal</clase>
  <biomarcador>CYP2D6</biomarcador>
  <genotipo_fenotipo>Metabolizadores lentos</genotipo_fenotipo>
  <secciones_ft>4.5 Interacción con otros medicamentos...</secciones_ft>
  <descripcion>Ver NOTAS para ampliar información</descripcion>
  <inclusion_cartera_sns>SÍ</inclusion_cartera_sns>
  <notas>De acuerdo con las indicaciones de la guía clínica CPIC...</notas>
</biomarcadores>
```

### 8. Supply Problems (`problemassuministro`)
```xml
<problemassuministro>
  <fecha_inicio>2017-06-01</fecha_inicio>
  <observaciones>Existe/n otro/s medicamento/s con los mismos principios activos...</observaciones>
</problemassuministro>
```

---

## Identified Entities (for Schema Design)

### Primary Entities
1. **Drug** (Prescription) - Main entity
2. **ActiveIngredient** (Principio Activo)
3. **Laboratory** (Laboratorio)
4. **ATCCode** (Clasificación ATC)
5. **PharmaceuticalForm** (Forma Farmacéutica)
6. **AdministrationRoute** (Vía de Administración)
7. **Excipient** (Excipiente)
8. **PackageType** (Envase)
9. **ContentUnit** (Unidad de Contenido)
10. **RegistrationStatus** (Situación de Registro)

### Derived/Embedded Entities
11. **DrugInteraction** - Relationship between drugs
12. **Duplicity** - Therapeutic duplicity warning
13. **GeriatricWarning** - Warning for elderly patients
14. **Biomarker** - Pharmacogenomic marker
15. **SupplyProblem** - Supply chain issues
16. **DrugComposition** - Link between Drug and ActiveIngredient with dosage

---

## Key Relationships

```
Drug ──────────────── MANUFACTURED_BY ──────────────── Laboratory
  │
  ├── HAS_PHARMACEUTICAL_FORM ─────────────────────── PharmaceuticalForm
  │
  ├── CONTAINS_ACTIVE_INGREDIENT ──────────────────── ActiveIngredient
  │   (with dosage properties)
  │
  ├── ADMINISTERED_VIA ────────────────────────────── AdministrationRoute
  │
  ├── CLASSIFIED_AS ───────────────────────────────── ATCCode
  │
  ├── CONTAINS_EXCIPIENT ──────────────────────────── Excipient
  │
  ├── INTERACTS_WITH ──────────────────────────────── Drug/ATCCode
  │   (with effect, recommendation properties)      *** CRITICAL RELATIONSHIP ***
  │
  ├── DUPLICATES_WITH ─────────────────────────────── ATCCode
  │   (therapeutic duplicity)
  │
  ├── HAS_BIOMARKER ───────────────────────────────── Biomarker
  │
  └── HAS_GERIATRIC_WARNING ───────────────────────── GeriatricWarning
```

---

## Data Volume Estimates

Based on CIMA data characteristics:
- **Drugs**: ~20,000+ medications
- **Active Ingredients**: ~3,000+ substances
- **Laboratories**: ~500+ manufacturers
- **ATC Codes**: ~6,000+ classification codes
- **Drug Interactions**: ~50,000+ interaction pairs (estimated)
- **Pharmaceutical Forms**: ~300+ forms

---

## NLP Opportunities

The following text fields are candidates for NLP extraction:

1. **`efecto_interaccion`** - Effect of drug interaction
   - Example: "Aumento del riesgo de arritmias ventriculares"
   - NLP Task: Classify severity (low/medium/high/contraindicated)

2. **`recomendacion_interaccion`** - Interaction recommendation
   - Example: "Asociación contraindicada. Se recomienda suspender uno de los principios activos"
   - NLP Task: Extract action type (contraindicated, monitor, adjust dose)

3. **`teratogenia`** - Teratogenicity warning
   - NLP Task: Extract risk category (A, B, C, D, X)

4. **`notas`** in biomarkers - Clinical notes
   - NLP Task: Extract dosage recommendations, alternative drugs

5. **`observaciones`** in supply problems - Observations
   - NLP Task: Identify alternative medications

6. **`riesgo_pacience_geriatria`** - Geriatric risk
   - NLP Task: Extract specific risk types

---

## Next Steps

1. Design MongoDB schema (document-oriented)
2. Design Neo4J schema (graph-oriented, optimal for interactions)
3. Define data transformation pipeline
4. Plan NLP extraction strategy for interaction classification
