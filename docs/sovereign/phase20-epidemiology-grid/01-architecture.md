# Phase 20-01 — Epidemiology Grid Architecture

## Position

The epidemiology grid is **separate from the clinical platform**. It is an
analytical perimeter that:

- **reads** anonymised, aggregated extracts from the clinical platform
- **never writes** to the clinical platform
- **never reads** raw patient identifiers
- exposes intelligence outputs to public-health authorities under their own
  audit chain

## Layers

```
+--------------------------------------------------------+
|  Public-health authority consumers (MOH, WHO, DHIS2)   |
+----------------------+---------------------------------+
                       |
              read-only adapter (Phase 16, INTEROP_AGGREGATOR_DEID)
                       |
+----------------------v---------------------------------+
|  Analytical perimeter                                  |
|  - aggregation engine                                  |
|  - anonymisation pipeline                              |
|  - statistical governance                              |
|  - outbreak detection                                  |
+----------------------+---------------------------------+
                       |
              one-way ETL (signed, scheduled)
                       |
+----------------------v---------------------------------+
|  Clinical platform (untouched, source of truth)        |
+--------------------------------------------------------+
```

The analytical perimeter and the clinical platform are **separate
deployment units**. Bringing one down does not affect the other.

## Data Flow

1. Clinical platform exports daily/hourly de-identified slices.
2. ETL applies anonymisation rules (k-anonymity, l-diversity targets,
   suppression of small cells).
3. Aggregation engine produces metrics by region, facility, demographic
   bucket, vocabulary code (mapped via terminology governance).
4. Outbreak detection runs over aggregates; alerts go to the public-health
   authority.
5. Aggregates feed DHIS2 via the adapter.

## Anonymisation Pipeline (high level)

- Raw national_id never leaves the clinical platform.
- Demographic fields are bucketised before export (age in 5-year bands,
  locality at the district level).
- Direct identifiers are stripped.
- Quasi-identifiers checked against a configurable k-anonymity floor.
- Cells failing the floor are suppressed with a "<5" placeholder.
- Re-identification audits run sample queries against the output.

## Outbreak Detection Approach

- Time-series surveillance over LOINC-grouped result codes.
- Threshold detection (z-score over rolling window) per region + condition.
- Alerts queued, ranked, reviewed by public-health authority.
- No automated public communication; review-driven release.

## ICU / Capacity Forecasting

When ICU/capacity data is added to the clinical platform (out of current
scope), forecasting:

- runs in the analytical perimeter
- consumes anonymised facility-level aggregates
- never exfiltrates patient-level data

## Federated Analytics

For deployments where data residency forbids centralising even aggregates:

- federated analytics with per-region aggregation
- only post-aggregation results travel to the central authority
- regional perimeters report rates, not patient lists

## Boundaries Honored

- TI-2: national queries via governed analytical tenants
- TI-3: no cross-tenant identity leakage
- AG-4: no AI cross-tenant access outside governed analytics
- GL-5: data residency respected
- The analytical perimeter is itself audit-logged (separate from clinical
  audit chain, but referenced)
