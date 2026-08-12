# Phase 16-01 — Interoperability Architecture

## Position in the Stack

Interop sits **between** the existing FastAPI monolith and any institutional
peer. It does not replace existing routes; it augments the platform with a
sidecar pattern that is invoked from explicitly-marked entrypoints.

```
                +------------------------------------+
                |  Institutional peers (MOH, NHIS,   |
                |  hospitals, telcos, payment gw)    |
                +-----------------+------------------+
                                  |
                          (signed messages, FHIR/HL7,
                           per-adapter auth, retries)
                                  |
                  +---------------v---------------+
                  |   AdapterBase (Python)        |
                  |   - bounded trust domain      |
                  |   - manifest                  |
                  |   - failure isolation         |
                  |   - InteropAuditEvent emit    |
                  +---------------+---------------+
                                  |
            +---------------------+---------------------+
            |                                           |
+-----------v-----------+               +---------------v---------------+
| Outbound: gula client |               | Inbound: dedicated FastAPI    |
| -> peer system        |               | router under /interop/*       |
+-----------+-----------+               | (mounted only when            |
            |                            |  ENABLE_INTEROP=true)        |
            v                            +---------------+--------------+
   gula-backend monolith                                 |
   (clinical writes, audit chain) <-----------------------+
```

## Bounded Trust Domains

Every external peer maps to a **TrustDomain**. A trust domain declares:

- `domain_id` — globally unique opaque identifier
- `institution_type` — `ministry | insurer | hospital | lab | telco | payment | statistics | nhop`
- `allowed_operations` — capability whitelist (e.g., `["fhir.read.Observation", "hl7.send.ORU"]`)
- `data_classes_in` / `data_classes_out` — the data classes the adapter is permitted to receive / send
- `audit_topic` — the audit-chain topic the adapter writes into
- `failure_policy` — `fail_closed` (always) and the retry budget
- `tenancy_mode` — `single_tenant_proxy` (default), `multi_tenant_aggregator` (regulator-only), or `national_aggregator` (statistics, anonymized)

A trust domain manifest is the **only** authority binding for that adapter.
No code path may broaden the bind at runtime.

## Adapter Modes

1. **API interop** — request/response, e.g., HL7 v2 over MLLP, FHIR REST.
2. **Async / event-driven** — outbox-pattern emission to a queue (RabbitMQ /
   national message bus), with idempotent consumer.
3. **Secure message exchange** — signed envelopes (JWS), encrypted payloads
   (JWE) for high-sensitivity inter-institutional transfers.
4. **Federated organization model** — consumer of a national patient identity
   service, with reconciliation per Phase 19.

## Failure Isolation

Every adapter carries its own:

- circuit breaker (existing pattern from `core/self_healing.py`, scoped per adapter)
- retry queue (Outbox-pattern, see `services/outbox_service.py`)
- bulkhead concurrency cap (separate from clinical-write pool)

A failing adapter MUST NOT:
- consume the global concurrency budget reserved for clinical writes
- delay critical-result delivery on the clinical path
- drop audit events; failed events go to the dead-letter chain, never
  silently discarded

## Offline / Low-Connectivity Preparation

Edge sites (province-level GULA installations, mobile collection points) are
treated as **partially-trusted internal peers**:

- Each edge is its own bounded trust domain.
- Edge-to-core sync uses the same adapter interface.
- Edge adapters declare `allow_offline=true`; outbound events are batched in a
  signed local outbox until the wide-area link returns.
- Reconciliation on reconnect is conflict-detectable; never auto-merging.

## Mount Strategy (Non-Breaking)

The interop router under `/interop/*` is **not** mounted by default. Wiring
is gated on:

```
ENABLE_INTEROP=true
INTEROP_ADAPTER_ALLOWLIST=fhir_moh,hl7_lablink,...
```

Until both are set in production, the interoperability surface is silent —
this preserves the "zero breaking changes" guarantee.
