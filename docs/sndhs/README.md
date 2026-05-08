# Sovereign National Digital Health System (SNDHS) — Core Architecture

> **Audience:** Principal architects, lead engineers, security & clinical
> governance officers, and the Ministry of Health technical board.
>
> **Status:** Implementation-ready specification. Every document in this
> directory is normative — deviations require a signed exception logged in the
> Policy Authority (see `11-governance.md`).

SNDHS is the sovereign clinical core of the national health stack. It owns
clinical state, identity-of-record, emergency timing, and legal auditability.
GULA is a non-clinical UI / service / integration layer that consumes SNDHS
through a constrained gateway. The two systems are physically and legally
separated.

## Hard Constraints (system-level invariants)

| # | Constraint | Enforcement |
|---|------------|-------------|
| H1 | P99 critical-path response < 2000 ms | SLO loop (`12-performance.md`), priority scheduler |
| H2 | Time-violation rate < 2% | Monotonic clock + drift watchdog (`11-governance.md`) |
| H3 | Bypass rate < 3% | Operational integrity layer (`14-integrity.md`) |
| H4 | 72 h full-offline survivability per node | MSBC + sync engine (`05-offline-sync.md`, `08-msbc.md`) |
| H5 | 100% legal auditability of all state-changing actions | Append-only event log + hash chain (`07-events.md`, `06-security.md`) |
| H6 | GULA never stores clinical data, never makes clinical decisions | Gateway DLP + ABAC (`10-gula-integration.md`) |
| H7 | Every clinical decision is bound to an immutable policy version | Policy authority (`11-governance.md`) |
| H8 | No AI output may cross the patient boundary unless promoted | Shadow-mode pipeline (`01-architecture.md` §AI) |

## Document map

| File | Section |
|------|---------|
| `01-architecture.md` | System architecture spec — components, modules, data flow, SNDHS↔GULA boundary |
| `02-database.md` | PostgreSQL schema, FHIR mapping, event sourcing, versioning, offline conflict resolution |
| `03-api.md` | MPI / EMR / Referral / Triage / Emergency / Event-streaming APIs + Zero-Trust + ABAC |
| `04-state-machines.md` | Referral lifecycle, critical encounter, MCOM 1–4 |
| `05-offline-sync.md` | Sovereign node design + sync protocol + conflict resolution + priority sync |
| `06-security.md` | Identity model, ABAC, audit chain, data segmentation |
| `07-events.md` | Event taxonomy, message bus, idempotency, replay |
| `08-msbc.md` | Minimal Sovereign Build Core — exact one-region deploy |
| `09-failure-scenarios.md` | Outage / partial failure / MCOM-3/4 / data conflict / human misuse playbooks |
| `10-gula-integration.md` | Gateway, DLP, UI flow, fail-safe |
| `11-governance.md` | Policy versioning + trusted time + data lifecycle |
| `12-performance.md` | Load model (1×/10×/100×), P99/P999, resource reservation |
| `13-validation-loop.md` | Continuous validation: sampling, clinical review, feedback injection |
| `14-integrity.md` | Operational integrity — bypass detection, behavior monitoring, enforcement |
| `15-wargames.md` | National-scale failure simulation design and pass/fail criteria |

## Conventions

- **MUST / MUST NOT / SHOULD** follow RFC 2119.
- All identifiers are ULIDs (Crockford base32, 26 chars) unless explicitly typed.
- All timestamps are stored as `(monotonic_ns BIGINT, wall_utc TIMESTAMPTZ, tz_offset_minutes SMALLINT, time_authority_id UUID, time_quality ENUM)` — never bare `now()`.
- All clinical writes carry `policy_version_id` (immutable FK) and `decision_context_hash` (sha256).
- All cross-domain calls carry `request_id`, `caller_principal_id`, `caller_attestation_id`, `correlation_id`, `causation_id`.
- Cryptographic primitives: Ed25519 (signing), X25519 (KEX), XChaCha20-Poly1305 (AEAD), BLAKE3 (hashing where speed matters), SHA-256 (hash chain — FIPS).

## Build & verification matrix

Every change to SNDHS must pass:

1. Syntax/type gate (mypy --strict, ruff, sqlfluff, jsonschema).
2. Migration round-trip on clean DB (forward → back → forward).
3. State-machine model check (TLA+ specs in `formal/` — see `04-state-machines.md`).
4. Property tests on invariants (Hypothesis + custom strategies).
5. Chaos suite (`/tests/chaos/`) on a 3-node cluster.
6. War-game replay on the latest national-scale traces (`15-wargames.md`).
7. Clinical governance sign-off for any rule whose `severity ≥ S2`.

## How to read this set

Start with `01-architecture.md` → `06-security.md` → `04-state-machines.md` →
`05-offline-sync.md`. Everything else builds on those four.
