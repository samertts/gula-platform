# Phase 20-03 — Anonymisation Governance

## Principles

1. **Direct identifiers are never exported.** national_id, sndhs_health_id,
   phone, full DOB, and free-text fields with potential PHI are stripped
   before crossing the analytical perimeter.
2. **Quasi-identifiers are bucketised.** Age in 5-year bands; locality at
   district resolution; small categories collapsed.
3. **k-anonymity floor is configurable, never below the regulator-set
   minimum.** Default `k=5` in early deployments.
4. **l-diversity** within each anonymity equivalence class for sensitive
   attributes (e.g., diagnosis).
5. **Suppression** of cells failing thresholds; never zero-padding.
6. **Re-identification testing** on every export pipeline change.

## Pipeline Stages

```
[clinical extract]
    -> [PII strip]
    -> [bucketisation]
    -> [join + aggregation]
    -> [k/l checks]
    -> [suppression]
    -> [signed output]
    -> [analytical store]
```

Each stage is auditable. Each stage's output is verifiable on demand.

## Configurable Parameters

| Parameter | Default | Source |
|-----------|---------|--------|
| `k_anonymity_min` | 5 | Regulator-set, jurisdiction-specific |
| `l_diversity_min` | 2 | Regulator-set |
| `age_band_years` | 5 | Public-health authority |
| `locality_resolution` | district | Public-health authority |
| `suppression_marker` | `"<5"` | Public-health authority |

Each parameter change is governance-tracked.

## Re-identification Risk Review

For each export type, a periodic risk review:

- runs sample queries against the export
- checks unique combinations
- flags equivalence-class outliers
- reports to the privacy officer

A failed review halts the export until remediated.

## Forbidden Outputs

- Patient lists, even partial
- Patient-day-level records
- Patient demographic tuples without bucketisation
- Free-text excerpts
- Provider-identifiable counts below the suppression threshold

## Permitted Outputs

- Aggregated counts above the floor
- Time-series at week or larger resolution (more granular requires
  specific approval)
- Geographic resolution at district or larger
- Demographic tuples after bucketisation, post-suppression

## Audit Surface

Anonymisation pipeline emits its own audit lineage:

- inputs hash
- parameters
- outputs hash
- suppression statistics
- pipeline version

The audit lineage is referenced from the clinical audit chain so an
investigator can trace clinical → exported analytical row provenance.

## Incident Mode

If a re-identification incident is suspected:

- the affected export is suspended
- consumers are notified
- root cause review runs (parameter drift? aggregation defect?)
- remediation parameters set
- re-export validated before resumption
