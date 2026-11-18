# Dependency Graph & Critical Path

**Document:** 02 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `IMPLEMENTED` (deterministic graph and schedule; no execution dependency implied).

---

## 1. Node definitions

| ID | Node | Kind | Owner authority | Current status |
|---|---|---|---|---|
| ADR-A | Migration strategy for 426 unmigrated ORM tables | Decision | Program Director / Architect | `BLOCKED` |
| ADR-B | Ownership of 3 downgrade-residual tables | Decision | Database owner | `BLOCKED` |
| ADR-C | care_continuum host vs decomposition | Decision | Architect | `BLOCKED` |
| ADR-D | Audit actor / scoped service principals | Decision | Security + owner | `BLOCKED` |
| ADR-E…J | Remaining architecture decisions | Decision | Architect / owner | `BLOCKED` |
| NR-011 | `alembic check` metadata registration + merged MetaData | Engineering | Backend owner | `TESTED` (14 regressions + disposable-PG proof) |
| MP-001 | DB `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` | Engineering + owner migration | Identity/DB owner | `BLOCKED` |
| ODR-002 / D-MPI-5 | Re-resolve corrected identity payloads | Decision | Identity owner | `BLOCKED` |
| ODR-003 / D-MPI-3/4 | Fork-response policy | Decision | Identity/clinical owner | `BLOCKED` |
| D-020 | Security certification | Sign-off | Security lead | `BLOCKED` |
| D-021 | Clinical safety certification | Sign-off | Clinical lead | `BLOCKED` |
| HOLD | Unification release decision | Sign-off | Program Director | `BLOCKED` |
| REJECT | MPI acceptance decision | Sign-off | Identity owner | `BLOCKED` |
| WS-01…07 | Workstreams (see `03`) | Engineering | Workstream leads | mixed — see registry |

## 2. Edges (`from → to` means `to` requires `from`)

```
NR-011 ──────────────────► ADR-A
ADR-A ───────────────────► context-by-context migrations (WS-07)
ADR-B ───────────────────► MIG-EXISTING closure
ADR-D ───────────────────► audit actor remediation (WS-02)
context-migrations ──────► MIG-EXISTING closure
MIG-EXISTING closure ────► HOLD lifting
D-020 ───────────────────► HOLD lifting
D-021 ───────────────────► HOLD lifting
ADR-C ───────────────────► WS-07 national journeys
MP-001 ──────────────────► AUD-02 closure
AUD-02 closure ──────────► MPI ACCEPT (REJECT superseded)
ODR-002 ─────────────────► AUD-07 closure ─► MPI ACCEPT
ODR-003 ─────────────────► AUD-16 closure ─► MPI ACCEPT
MPI ACCEPT ──────────────► WS-01 national identity
D-020 ───────────────────► WS-02 security certification claim
WS-03 (FHIR adapter) ────► WS-06 client contracts
WS-04 (terminology) ─────► WS-03 FHIR validation
WS-05 (reliability) ─────► WS-07 journeys (offline-first)
WS-01 identity ──────────► WS-07 journeys (patient context)
```

## 3. Critical path

Longest owner-gated chain (all external approvals are **decision packages only** in this program):

```
NR-011 (engineering, `TESTED` — prerequisite complete)
  → ADR-A (owner decision)
  → context-by-context migrations (engineering)
  → MIG-EXISTING closure (needs ADR-B + production-like snapshot)
  → HOLD lifting (needs D-020 + D-021 + owner)
  → production readiness
```

Second critical chain (national identity):

```
MP-001 (owner migration)
  → AUD-02 closure
  → AUD-07 + AUD-16 closures (ODR-002 / ODR-003 decisions)
  → MPI ACCEPT (supersedes REJECT)
  → WS-01 national identity platform
```

**Shortest executable engineering chain in this program:** `WS-04 terminology offline validation hardening` → `WS-03 FHIR adapter` → `WS-06 client contracts` → focused + regression tests → independent review. NR-011 prerequisite engineering is already `TESTED` and is not repeated. This chain requires **no** invented human approval and is the recommended first implementation tranche.

## 4. Workstream execution schedule (dependency-respecting, not time-estimated)

| Tranche | Workstreams | Entry gate | Exit evidence |
|---|---|---|---|
| T1 (Phase B start) | WS-04, WS-05 | 773 baseline green | focused tests; no baseline regression |
| T2 | WS-02, WS-03 | T1 green | contract diff; security review scope |
| T3 | WS-06 | T2 green | client manifest validation; RTL/a11y unchanged |
| T4 | WS-01 (synthetic-safe portion) | MPI decision packages registered | no MPI status claim change |
| T5 | WS-07 | ADR-A/C + migrations (owner) | journey tests; no route activation |

**Parallelism rule:** T1 WS-04 (`health_core/terminology/`, `national/reference/`) and WS-05 (`health_core/reliability/`) have **disjoint file ownership** and may run concurrently. WS-02 and WS-03 likewise have disjoint primary surfaces. No two agents may write the same file; the registry records ownership.

## 5. Rule for status escalation

An edge target may not be marked `INTEGRATED` or `INDEPENDENTLY VERIFIED` while any prerequisite is `BLOCKED`/`NOT IMPLEMENTED`, **except** for explicitly synthetic, in-repo evidence that does not claim the target's production outcome. Synthetic test evidence is always labelled with its boundary.

---

_Schedule is dependency order only; no duration or completion date is asserted._
