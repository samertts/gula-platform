# Medical Ontology Seed Data

Canonical Iraqi medical intelligence ontology — biomarkers, symptoms, diseases,
panels, organ systems, specimens, and units — with LOINC / SNOMED CT / ICD-10 /
RxNorm / CPT cross-references, multilingual synonyms (English, Modern Standard
Arabic, Iraqi dialect, Arabizi), demographic-aware reference ranges, and unit
conversions.

Seed files here are the **source of truth** for the tables created by migration
`20260908_0001_medical_ontology_core.py`. The loader
`scripts/seed_medical_ontology.py` upserts them into the database and is
idempotent — running it twice is a no-op when nothing changed.

## Files

| File | Purpose |
|------|---------|
| `concepts.yaml` | Canonical concepts (id, category, display labels, primary codes, canonical unit) |
| `synonyms.yaml` | Multilingual terms + Iraqi aliases + Arabizi variants → concept_key |
| `relations.yaml` | Graph edges (panel_includes, measures, indicates, is_a, part_of) |
| `reference_ranges.yaml` | Demographic-aware normal / critical bands per (concept, unit, age, sex, pregnancy) |
| `unit_conversions.yaml` | Canonical unit + inter-unit conversion factors |

## Data-quality rules

1. Every concept has a stable `concept_key` (slug) — **never rename** an existing
   key; deprecate + add a new one instead. Migrations depend on stability.
2. Every biomarker concept must have a `canonical_unit` and at least one adult
   reference range.
3. Every reference-range row must cite a `source` (`CLSI`, `WHO`, `NICE`, `Mayo`,
   `CAP`, `internal`) and, where possible, a `source_url`.
4. Iraqi-dialect synonyms use `locale: ar-IQ`; Arabizi entries use
   `locale: arabizi`.
5. Ranges without an `age_max_years` mean "and older"; without `age_min_years`
   mean "and younger". `sex: any` and `pregnancy_status: any` are the fallback.
6. `unit_conversions` where `concept_scope` is null are universal (e.g.
   °C↔°F, kg↔lb); when scoped, they apply only to that concept (e.g. mg/dL↔mmol/L
   for glucose vs. for creatinine differ).

## Provenance

Seed values were compiled from public authoritative sources (CLSI C28-A3,
Mayo Clinic Laboratories reference intervals, WHO haematology guidance, NIH
MedlinePlus). Where an Iraqi-specific reference or Iraqi Ministry of Health
guidance was consulted, `source: ministry_iq` is used. **No proprietary
UpToDate content is stored here.**

Every row is versioned via the `version` column on `medical_ontology_concepts`
and the `source_version` string on ranges — bump on any material change.
