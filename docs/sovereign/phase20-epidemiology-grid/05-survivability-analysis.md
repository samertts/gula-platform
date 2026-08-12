# Phase 20-05 — Sovereign Public-Health Survivability

## Survivability Goals

The epidemiology grid must:

- continue producing useful aggregates during partial outages
- never block clinical writes when degraded
- preserve audit lineage on its own analytical chain
- recover cleanly from gaps (back-fill on reconnect)

## Failure Modes

| Failure | Behaviour |
|---------|-----------|
| ETL job fails | Latest aggregate is stale; consumer sees stale-data warning; ETL retried |
| Anonymisation pipeline regression | Pipeline halts; existing exports retained; root-cause analysis |
| Detector false positives | Alerts marked low confidence; retraining schedule triggered |
| Source clinical region offline | Aggregates for that region absent; explicit "no data" not "zero" |
| Analytical perimeter crash | Clinical platform unaffected; analytics resumes from last checkpoint |

## Recovery Discipline

After any gap in surveillance data:

- Back-fill ETL runs explicitly with a "back-fill" flag.
- Detectors do NOT auto-trigger on back-filled data older than a threshold
  (avoid false retroactive alerts).
- Public-health authority sees the gap explicitly in dashboards.

## Crisis-Mode Operation

During Phase 23 crisis:

- Surveillance prioritises critical conditions.
- ETL frequency may be reduced; surveillance accuracy degrades gracefully.
- Manual / paper-based regional reports feed back into the perimeter when
  ETL resumes.

## DR Considerations

The analytical perimeter has its own DR target:

- RPO ≤ 24h (analytics is not synchronous-replica-required)
- RTO ≤ 24h (a day's gap is tolerable for surveillance; not for clinical)

DR for analytics is independent of clinical DR; analytical disaster does
not propagate to clinical, and vice versa.

## Verification

Annual exercise:

- inject synthetic anomaly into a non-prod replica
- verify detector fires at expected confidence
- verify alert review workflow operates
- verify audit lineage captures the run end-to-end

Failed exercises feed the dependency register.
