# Phase 20-02 — Public-Health Intelligence Preparation

## Capabilities

| Capability | Inputs | Outputs | Authority |
|------------|--------|---------|-----------|
| Disease surveillance | Lab results aggregated by LOINC + region + week | Incidence trends, threshold alerts | Public-health authority + DHIS2 |
| Outbreak detection | Spike detection over rolling windows | Ranked alert queue | Public-health authority review |
| Laboratory intelligence | QC, calibration, turnaround aggregates | Lab quality dashboards | Lab director + regulator |
| Capacity forecasting | Order volume, ICU occupancy (when fed) | Forecasted load | Operations + ministry |
| Utilisation intelligence | Procedure / test mix per facility | Utilisation reports | Insurer + ministry |

## Statistical Governance

- Threshold parameters approved by the public-health authority before
  deployment.
- Methodology documented and signed (model card per detector).
- Re-runs are reproducible from inputs + parameters.
- Calibration reviewed quarterly (false positive / negative balance).

## Alert Workflow

1. Detector fires.
2. Alert enters review queue with metadata: detector id, parameters,
   contributing aggregates, confidence.
3. Public-health reviewer sees redacted views; can request more
   aggregations.
4. Reviewer disposes: `escalate`, `monitor`, `dismiss`.
5. All dispositions audited.

There is **no automated public-facing alert**. Communication is reviewer-
gated.

## Crisis-Mode Surveillance

During crisis (Phase 23):

- Detectors run on whatever fresh data the perimeter has.
- Stale-data warnings on alerts older than the freshness SLA.
- Fallback to manual/paper aggregation if ETL is offline.

## Standards Mapping

- LOINC for lab observations.
- ICD for diagnoses.
- WHO disease codes (ICD-aligned) for surveillance categories.
- DHIS2 data sets for outward push.

## Tenant-Safe Operation

The perimeter is **its own tenant**. Its operators do not touch clinical
tenants. Conversely, clinical-tenant operators do not see the perimeter's
internals.

## Ethical Safeguards

- Surveillance does not target individuals.
- Bias review every model deployment (demographic representativeness,
  geographic coverage).
- Public-health authority publishes a transparency report on detectors in
  use (frequency: annual).

## Out of Scope (this phase)

- Building the detectors
- Building the dashboards
- Building the federated-analytics infrastructure
- Building the ETL pipeline
