# GULA — National Health Platform Foundation

> الأساس المعماري للمنصة الصحية الوطنية — 48 مليون مواطن، سجل صحي واحد لكل مواطن، لا تكرار أبدًا.

This document defines **what the system is** and **what it must never become**.
It is the contract every future service, schema migration, and integration
adapter must respect. No code. No SQL. Only abstractions, boundaries, and
invariants.

---

## 1. Mission statement

Connect every **Lab**, **Doctor**, and **Citizen** in Iraq (≈48 M people) into
a single, lifelong, non-duplicating health record, while preserving:

1. **Patient data sovereignty** — a citizen's record belongs to the citizen,
   not to any single lab or institution.
2. **Lab tenancy** — each lab keeps autonomous operational control of its own
   orders, samples, billing, and staff.
3. **Audit immutability** — every identity decision, every data access, every
   merge, is append-only and hash-chained.
4. **Government interop** — the platform speaks to the Iraqi National ID
   registry, Health Insurance, and Residency systems through well-defined,
   swappable adapters — never with direct coupling.

---

## 2. Three-layer architecture

```
                    ┌────────────────────────────────────────┐
                    │              EDGE                       │
                    │  • Lab front-end (web/mobile)           │
                    │  • Doctor portal                        │
                    │  • Citizen portal (self-service)        │
                    └────────────────┬───────────────────────┘
                                     │   HTTPS · JWT
          ┌──────────────────────────┴────────────────────────┐
          │                    LIMS LAYER                     │
          │  (existing gula-backend — lab-scoped operations)  │
          │                                                    │
          │  Owns: labs, lab_users, patients*, lab_orders,    │
          │        samples, lab_results, claims, audit_logs   │
          │                                                    │
          │  *patients here = LOCAL patient rows scoped by    │
          │   lab_id. Not the canonical citizen record.       │
          │                                                    │
          │  Every query filters by current_user.lab_id.       │
          │  Publishes events to outbox_events.                │
          └──────────────────────────┬────────────────────────┘
                                     │   MPI IdentityClaim · outbox
          ┌──────────────────────────┴────────────────────────┐
          │                 NATIONAL LAYER                    │
          │  (new — citizen-scoped, cross-lab authority)       │
          │                                                    │
          │  Owns: citizens, identity_claims, mpi_merge_audit │
          │        (future) national_records, consent_ledger, │
          │                 fhir_resources, outbox_consumer   │
          │                                                    │
          │  Never writes LIMS tables directly.                │
          │  Never scoped by lab_id.                           │
          └──────────────────────────┬────────────────────────┘
                                     │   Adapters (gateways/)
          ┌──────────────────────────┴────────────────────────┐
          │              GOVERNMENT BOUNDARY                  │
          │                                                    │
          │  • البطاقة الوطنية    (NID verification)           │
          │  • الضمان الصحي       (Health insurance eligibility)│
          │  • الإقامة للأجانب   (Foreigner residency lookup)  │
          │  • Ministry of Health reporting                    │
          │                                                    │
          │  Each integration = one gateway adapter with two   │
          │  modes: `stub` (default) and `live` (credentialed).│
          │  The platform never hard-codes a provider.         │
          └────────────────────────────────────────────────────┘
```

### Why three layers and not two?

The LIMS layer already exists and is **correct for lab operations**: it
enforces tenancy, rate limits, billing, quality control. Adding "national"
responsibilities on top of the lab-scoped `patients` table would break that
model — a ministry admin reading 48 M rows cannot also be filtered by
`lab_id`.

The National layer is therefore a **sibling**, not a replacement. It reads
LIMS events via the outbox (asynchronously) and exposes canonical identity
via the Master Patient Index. LIMS continues to work if the National layer
is entirely offline.

---

## 3. Data model (abstractions — no columns yet)

Only three first-class concepts at the architectural level:

### 3.1 Citizen (national layer)

The one canonical record for **a real human being** in Iraq (or a legal
resident with an assigned national identity). One-per-person, for life.

Properties (abstract):
- **Canonical identity** — hashed national ID, verification flag
- **Demographics** — normalized name, DOB parts, gender, phone, family ID
- **Matching keys** — blocking key, canonical name, family hash
- **Lifecycle** — status (active/merged/review/deceased), merged_into pointer
- **Concurrency** — optimistic version

A `Citizen` row **never stores raw PII that has a hashed alternative**
(national ID is HMAC-SHA256, never clear text). A `Citizen` row is **never
deleted** — merged citizens stay with `status='merged'`.

### 3.2 Lab (LIMS layer)

An institution that produces clinical data for citizens. A lab has:
- Its own users, subscription tier, rate limits, billing
- Local patient rows (`patients.lab_id`) which are **working copies** — the
  canonical truth lives in the National layer
- Complete operational autonomy: orders, samples, results, claims

A lab cannot read another lab's data. Period.

### 3.3 Record (bridges both layers)

Any **clinical event** produced by a lab for a citizen: an order, a result,
a sample, a report.

Records live primarily in the LIMS layer (where they are produced). The
National layer sees them through the outbox: LIMS publishes
`result.finalized`, the National consumer links the result header to the
canonical citizen via `IdentityClaim` and stores a national-layer reference.

A record therefore has **two identities**:
- **Local**: `(lab_id, order_id)` or `(lab_id, result_id)`
- **Canonical**: `(citizen_id, record_ulid)`

Queries within a lab use the local identity. Queries across labs (a doctor
viewing a citizen's full history) use the canonical identity.

### 3.4 Supporting concepts (name only — defined elsewhere)

- **IdentityClaim** — the join row linking `(lab_id, patient_id)` → `citizen_id`
- **MergeAudit** — append-only, hash-chained ledger of identity decisions
- **Outbox event** — exists today (`outbox_events`), is the sync channel
- **Gateway adapter** — a pluggable external-system integration

---

## 4. Boundary contract (invariants — never violate)

These rules are enforced by code review, CI gates, and — where possible — by
foreign-key constraints.

### 4.1 Direction of coupling

| From                    | May read | May write |
|-------------------------|----------|-----------|
| Edge → LIMS             | ✅        | ✅         |
| Edge → National         | ✅ (citizen portal, read-only for most users) | ❌ |
| LIMS → National         | ✅ (via MPI resolve)  | ✅ (via outbox publish only) |
| National → LIMS         | ❌        | ❌ (never) |
| National → Government   | ✅ (via gateway) | ❌ (read-only) |
| LIMS → Government       | ❌ (must go through National) | ❌ |

**Key rule**: the National layer **must never query LIMS tables directly**.
All lab data reaches National via outbox events. This keeps LIMS deployable
and scalable independently.

### 4.2 Identity resolution

1. When a lab creates a patient, it calls `POST /mpi/resolve` with the
   patient's demographics and (optional) raw national ID.
2. The MPI service finds or creates a canonical `Citizen` and returns the
   `citizen_ulid`.
3. The lab stores the `citizen_ulid` on its `patients` row (optional denorm)
   and writes one `IdentityClaim(lab_id, patient_id, citizen_id)`.
4. Every future result/order for that patient inherits the citizen linkage
   via the claim — no re-resolution needed.

**NID is hashed at the LIMS edge**, never transmitted in clear text to the
National layer, never logged.

### 4.3 Append-only guarantees

- `mpi_merge_audit` is **immutable** at the application layer. Each row's
  `entry_hash = SHA256(prev_hash || canonical_json(row))`. Tampering is
  detectable by scanning the chain.
- `audit_logs` (existing) remains hash-chained (`20260324_0009` migration).
- Citizens are **never DELETEd** — they are marked `merged` or `deceased`.
- Records (orders, results) follow existing LIMS archival policy — the
  National layer never deletes its references.

### 4.4 Read rules

- Every LIMS query must filter by `current_user.lab_id` (existing invariant
  in `CLAUDE.md § Security Invariants`).
- Every National query must follow the `merged_into_id` chain on read:
  `SELECT * FROM citizens WHERE (id=? OR merged_into_id=?) AND status IN ('active','review')`.
- Cross-lab reads (citizen portal, ministry dashboard) go through the
  National layer only, using `citizen_ulid` — never via the LIMS tables.

### 4.5 Government integration rules

- Every outbound call to a government system goes through
  `backend/app/gateways/` — never direct `requests.get(...)` in business code.
- Every gateway has **two modes**: `stub` (default, offline, returns canned
  responses) and `live` (credentialed, real HTTP). The mode is controlled by
  a single env var per gateway (e.g. `GOV_NID_MODE=live`).
- Every gateway call is logged to `audit_logs` with request fingerprint,
  latency, outcome, and the `citizen_ulid` on whose behalf it was made.
- Circuit breaker: three consecutive failures opens the circuit for 60 s
  (existing pattern in `app/core/self_healing.py`).

---

## 5. Scaling to 48 million citizens

### 5.1 Numbers

- 48 M citizens × (avg 3 lab visits / year) = **144 M clinical events / year**
- Peak: 10 k concurrent users during Ramadan check-ups
- Storage: ~200 bytes/row for `citizens` → 10 GB canonical; + indexes ≈ 20 GB

### 5.2 What the architecture buys us

| Bottleneck          | Mitigation                                        |
|---------------------|---------------------------------------------------|
| MPI candidate search | Blocking key + composite index reduces 48 M → ~50 rows per query |
| Write amplification  | Outbox decouples LIMS writes from National replication |
| DB connections       | Supabase connection pooler (port 6543) — see `supabase/README.md` |
| Hot-read cache       | Cloudflare edge cache for static citizen lookups (read-only) |
| Regional latency     | Cloudflare Workers run logic at the edge — sub-50ms nationwide |
| Failover             | Render + DigitalOcean active-standby on same Supabase DB |

### 5.3 What we do **not** do

- We **do not** shard citizens by province. Provinces overlap (people move);
  the MPI would have to re-resolve on every move, breaking audit continuity.
- We **do not** use a graph DB. The data is relational; PostgreSQL + proper
  indexes handle 48 M rows easily (GitHub runs 100× that).
- We **do not** introduce eventual consistency inside the LIMS transaction.
  MPI resolution is synchronous within a patient create; outbox replication
  to National is async, but LIMS reads see their own writes.

---

## 6. Integration surface (government + cloud)

| System                             | Layer       | Gateway adapter    | Mode matrix |
|------------------------------------|-------------|--------------------|-------------|
| البطاقة الوطنية (Iraqi NID)       | National    | `gateways/gov_nid`       | stub / live |
| الضمان الصحي (Health Insurance)   | National    | `gateways/gov_insurance` | stub / live |
| الإقامة (Foreigner Residency)     | National    | `gateways/gov_residency` | stub / live |
| Cloudflare (DNS/WAF/Workers/R2)    | Edge + Ops  | `gateways/cloudflare`    | stub / live |
| Render                             | Deploy      | `render.yaml`            | n/a         |
| Supabase                           | Data        | `DATABASE_URL`           | n/a         |
| DigitalOcean App Platform          | Deploy      | `digitalocean/app.yaml`  | n/a         |

All four adapters share the same `backend/app/gateways/base.py` contract:
`probe() → healthy? | request(op, payload) → typed response | record(audit)`.

---

## 7. What lives where — quick reference

| Concern                        | Layer      | File / table                              |
|--------------------------------|------------|-------------------------------------------|
| Lab authentication             | LIMS       | `app/security/auth.py`, `lab_users` table |
| Patient-lab operational record | LIMS       | `patients` table (scoped by `lab_id`)     |
| Lab order state machine        | LIMS       | `app/domain/order_state.py`               |
| Canonical citizen identity     | National   | `citizens` table                          |
| Lab↔citizen linkage            | Bridge     | `identity_claims` table                   |
| Identity merge history         | National   | `mpi_merge_audit` table (hash-chained)    |
| LIMS→National sync             | Bridge     | `outbox_events` (existing)                |
| Government API calls           | Gateways   | `app/gateways/gov_*`                      |
| CDN / edge / WAF               | Ops        | `cloudflare/` + `gateways/cloudflare`     |
| Secrets                        | Ops        | `.env.deploy` (never committed)           |

---

## 8. Out of scope for this foundation document

This document defines the **shape** of the system, not its current
implementation status. Concrete code lives in:

- `backend/app/services/mpi/` — Master Patient Index (next delivery)
- `backend/app/gateways/` — integration adapters (next delivery)
- `backend/app/services/consent/` — *future*, intentionally empty
- `backend/app/services/fhir/` — *future*, intentionally empty

When those services are built, they must respect every invariant in §4.

---

*Document version: 1.0 — 2026-04-13.*
*Changes to this document require architectural review.*
