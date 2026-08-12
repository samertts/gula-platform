# ADR-017: National Health Data Platform

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, Data Engineering Lead

---

## Context

The GULA platform generates and processes vast amounts of health data across laboratory workflows, clinical records, patient demographics, and operational metrics. As the platform scales to national coverage in Iraq, there is a critical need for a unified data backbone that serves as the single source of truth for analytics, AI, reporting, and interoperability.

**Requirements:**
- Unified data lake for all structured and semi-structured health data
- Enterprise data warehouse for aggregated reporting and analytics
- Master Data Management (MDM) for patient, provider, and organization identity resolution
- Event store for real-time data streaming and change data capture
- Data governance framework including lineage, cataloging, and quality monitoring
- AI-ready data pipelines with feature store integration
- Compliance with Iraqi data sovereignty and privacy regulations

**Constraints:**
- Must not disrupt existing GULA operational databases or APIs
- Must handle both real-time streaming and batch processing workloads
- Must scale to population-level data volumes (45M citizens, billions of clinical events)
- Must support both SQL and analytical query patterns
- Must operate within existing infrastructure budget

## Decision

Extend the existing `national_data/` module with a comprehensive data platform architecture incorporating canonical data models, an event store, a warehouse, and a governance framework. The platform is built incrementally, reusing existing GULA data infrastructure where possible.

### Architecture

```
+------------------------------------------------------------------+
|                    National Health Data Platform                 |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |                   Data Sources Layer                      |   |
|  |  GULA DB  |  SNDHS  |  Device Bridge  |  External APIs   |   |
|  +---------------------+--------------------------+----------+   |
|                       |                          |               |
|  +--------------------+--------------------------+-----------+   |
|  |              Ingestion & Streaming Layer                   |   |
|  |  CDC (Debezium)  |  Event Bus (Kafka)  |  Stream Proc    |   |
|  +----------------------------------------+------------------+   |
|                                           |                       |
|  +----------------------------------------+-------------------+   |
|  |                  Storage & Compute Layer                    |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Data Lake|  |Warehouse |  | Event    |  | Feature  |     |   |
|  |  | (Parquet)|  |(Star S.) |  | Store    |  | Store    |     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  +----------------------------------------+------------------+   |
|                                           |                       |
|  +----------------------------------------+-------------------+   |
|  |                  Governance Layer                           |   |
|  |  Data Catalog  |  Lineage  |  Quality  |  Access Control   |   |
|  +----------------------------------------+------------------+   |
|                                           |                       |
|  +----------------------------------------+-------------------+   |
|  |                  Consumption Layer                          |   |
|  |  BI Tools  |  AI/ML  |  National Reports  |  APIs          |   |
|  +------------------------------------------------------------+   |
|                                                                   |
+-------------------------------------------------------------------+
```

### Key Design Decisions

1. **Canonical data models** — Define a set of canonical models (`Patient`, `Encounter`, `Observation`, `DiagnosticReport`, `Organization`, `Practitioner`) in the `national_data/models/` directory. These models are the interchange format between all systems, mapped to/from GULA's internal models via the orchestration layer.

2. **Event-first architecture** — All domain events (order placed, result published, patient merged) are captured in an event store. This enables real-time processing, audit, and replay capabilities. Kafka is the event backbone with Debezium for CDC from PostgreSQL.

3. **Single source of truth** — The warehouse is the authoritative source for all aggregated/reporting data. MDM reconciles patient and provider identities across all sources into golden records.

4. **AI-ready pipelines** — Data pipelines produce clean, feature-engineered datasets directly consumable by AI/ML models. A feature store provides low-latency access to pre-computed features.

5. **Phased implementation** — Start with the warehouse and canonical models (Phase 1), add event store and streaming (Phase 2), then MDM and governance (Phase 3).

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | Canonical models, warehouse schema, batch ETL from GULA DB | 10 weeks |
| **Phase 2** | Event store, CDC streaming, real-time enrichment pipelines | 8 weeks |
| **Phase 3** | MDM, data catalog, lineage tracking, quality monitoring | 8 weeks |
| **Phase 4** | Feature store, AI pipeline integration, performance optimization | 6 weeks |

## Consequences

### Positive
- **Single source of truth** — All national health data has one authoritative location
- **AI-ready infrastructure** — Clean, feature-engineered data for ML models without ad-hoc ETL
- **Real-time capabilities** — Event-driven architecture enables real-time alerts, dashboards, and triggers
- **Data governance** — Full lineage, catalog, and quality monitoring for regulatory compliance
- **SNDHS readiness** — Data platform natively supports national health reporting requirements
- **Scalable** — Decoupled architecture allows independent scaling of each component

### Negative
- **Increased infrastructure complexity** — Kafka, warehouse, and governance tools add operational overhead
- **Data latency** — Batch pipelines introduce minutes-to-hours latency for warehouse data
- **Storage costs** — Data lake and warehouse storage for national-scale health data is significant
- **Skill requirements** — Team needs expertise in Kafka, warehouse design, MDM, and data governance

### Risks
- **Data quality at source** — If GULA operational data has quality issues, they propagate to the data platform. Mitigated by: data quality checks at ingestion, monitoring dashboards, quality SLAs.
- **Schema evolution** — Canonical models will evolve as requirements change. Mitigated by: schema registry with backward compatibility enforcement, versioned models.
- **Eventual consistency** — Warehouse data lags behind operational data. Mitigated by: clear documentation of staleness bounds, real-time paths for time-sensitive queries.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 3** — Data integrity is paramount; canonical models ensure consistency
- **Engineering Constitution Section 5** — Modularity and separation of concerns through layered architecture
- **ADR-005** — PostgreSQL 16 remains the operational source of truth; warehouse is a read-only derivative
- **ADR-010** — SNDHS integration feeds into the national data platform
- **ADR-016** — EHR platform consumes from and contributes to the data platform
- **Iraqi Data Sovereignty Regulations** — All data remains within national infrastructure
- **HIPAA/GDPR-aligned data governance** — Privacy and access controls at every layer
