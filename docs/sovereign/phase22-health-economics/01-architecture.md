# Phase 22-01 — Healthcare-Economics Architecture

## Position

The economics layer is a **read-mostly** intelligence layer with a small,
governed set of **write** workflows for reimbursement preparation,
provider settlement, and insurance lifecycle events.

The schema for Financial Engine Phase A is already in place
(`backend/app/financial/`, `migrations/.../20260505_0001_financial_engine_phase_a.py`).
Phase 22 documents the governance + architectural shape that future Phase
B+ implementations must respect.

## Layers

```
+--------------------------------------------------+
| Insurer / Treasury / Ministry of Finance peers   |
+----------------------+---------------------------+
                       |
              Phase 16 adapters (insurer, payment, treasury)
                       |
+----------------------v---------------------------+
| Economics service (Phase 22, mostly read)        |
|  - reimbursement preparation                      |
|  - utilisation aggregation                        |
|  - fraud / waste / abuse detection (advisory)     |
|  - actuarial inputs                               |
+----------------------+---------------------------+
                       |
              read access via existing models;
              writes via human-approved flows only
                       |
+----------------------v---------------------------+
| Clinical platform (source of truth)              |
+--------------------------------------------------+
```

## Read Surfaces

- Lab order volumes, by tenant + period
- Test mix by LOINC + region
- Provider utilisation aggregates
- Insurance plan coverage usage (anonymised where required)
- Critical-result frequency for actuarial forecasting

## Write Surfaces (governed)

- Reimbursement claim preparation rows (`fin_*` tables)
- Settlement event records
- Conversion and campaign attribution rows (Phase A schema present)
- Audit-only fraud flags (never executory)

Every write surface:

- requires a human-approved upstream action
- creates an audit row (chain participation)
- is reversible via a compensating row (no UPDATE-in-place semantics for
  financial rows beyond status transitions)

## Authorisation Model

| Role family | Read | Write |
|-------------|:----:|:-----:|
| Lab finance | own tenant aggregates | own tenant prepared claims (under approval workflow) |
| Insurer (via adapter) | their insurer's claims | claim-status updates (acknowledgements only) |
| Ministry finance | aggregated only | none in this phase |
| Treasury (via adapter) | settlement summaries | settlement acknowledgements only |
| Auditor | full read on warrant | none |
| Regulator | full read on warrant | none |

A role MUST NOT combine "claim approval" + "audit modification". A role
MUST NOT combine "fraud flag" + "claim execution".

## AI in Economics

AI used for FWA detection / actuarial forecasting:

- runs under Phase 21 governance
- authority class is `advisory`
- outputs require human review before any financial consequence
- runs in `aggregate` scope when over national data; `tenant` scope for
  tenant-internal flagging

No AI executes financial actions.

## Treasury Integration

A treasury adapter, when introduced, accepts one-way settlement
notifications:

- inbound: settlement acknowledged
- outbound: settlement requested

The adapter:

- emits InteropAuditEvent on every transition
- never auto-creates a payment without a human-approved settlement intent
  upstream
- carries idempotency keys to prevent double-payment on retry

## Insurance Lifecycle

- Coverage check (read)
- Pre-authorisation request (write, human-driven)
- Claim submission (write, human-approved batch)
- Claim status receipt (read from peer)
- Settlement (write, treasury adapter)

Each transition is auditable, reversible (via compensating events), and
exposed in the audit chain.
