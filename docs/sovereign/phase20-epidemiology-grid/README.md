# Phase 20 — National Epidemiology & Health Intelligence Grid

**Goal:** Prepare sovereign public-health intelligence capabilities — outbreak
detection, disease surveillance, lab intelligence aggregation, ICU/capacity
forecasting, utilisation intelligence — under privacy-preserving, governed
analytical isolation.

## Documents

| File | Subject |
|------|---------|
| [`01-architecture.md`](./01-architecture.md) | Epidemiology grid architecture |
| [`02-public-health-intelligence.md`](./02-public-health-intelligence.md) | Public-health intelligence preparation |
| [`03-anonymization-governance.md`](./03-anonymization-governance.md) | Anonymization governance |
| [`04-privacy-preserving-analytics.md`](./04-privacy-preserving-analytics.md) | Privacy-preserving analytics assumptions |
| [`05-survivability-analysis.md`](./05-survivability-analysis.md) | Sovereign public-health survivability |

## Sovereign Invariants Honored

- TI-2 (national queries via governed analytical tenants only)
- TI-3 (no cross-tenant identity leakage)
- AG-4 (no AI cross-tenant access outside governed analytics)
- All epidemiology paths are read-only on the production clinical layer
