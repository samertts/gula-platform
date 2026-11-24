# ADR Decision Request — Unification Program

**Status:** **PENDING PROGRAM DIRECTOR / ARCHITECTURE APPROVAL — nothing below is implemented.**
**Repository:** `/home/samertts/workspace/projects/gula-integration` @ `2827c1ff`
**Date:** 2026-11-17
**Source of truth for context:** `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md` §9,
`GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` §13, `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md`

Each item states the decision needed, the options, the recommendation, what it unblocks, and why it
is reversible. No schema change, ownership change or module activation has been performed.

---

## ADR-A — Migration strategy for the 426 unmigrated ORM tables

**Evidence.** 833 ORM tables across 40 contexts; **407 migrated (48.9 %)**; **426 missing**;
**18 / 40** contexts fully covered. Largest gaps: `national` 98, `governance` 58,
`care_continuum` 45, `clinical` 39, `national_data` 36, `insurance` 30, `document_intelligence` 21,
`ehr` 18, `health_data` 17, `hospital` 13.

**Hard prerequisite (ordering, not implementation):** `NR-011` must be fixed first —
`alembic check`/autogenerate currently abort with
`NoReferencedTableError: ehr_allergies.encounter_id → national_encounters`, because
`migrations/env.py:38` imports only `app.national.base` and `national_encounters`
(`backend/app/national/domain/encounter.py:9`) appears in no migration and no migrated database.

**Options.**

| Option | Approach | Cost | Risk |
|---|---|---|---|
| **A1** | Import all domain models in `env.py`, repair metadata, then author migrations **context-by-context** (one PR per context, each with a strict-schema round-trip test) | High (40 contexts) | Low per step; long duration |
| **A2** | Author one bulk "baseline everything currently in the ORM" revision | Medium | **High** — a single unreviewable diff; impossible to attribute a failure |
| **A3** | Declare the unmigrated contexts **non-shipping** (feature-gated off) and migrate only what a release actually serves | Medium | Trades scope for honesty; must be stated in the release notes |
| **A4** | `create_all()` at deploy time for the remainder | Low | **Rejected** — abandons migration integrity; masks drift permanently |

**Recommendation: A1 + A3 together.** Fix `NR-011`, then migrate in context order for anything the
release serves, and formally mark the rest non-shipping. A2 and A4 are rejected on review quality and
integrity grounds.

**Unblocks:** any strict-schema release claim; W1 exit evidence. **Reversible:** yes — each context is
an independent revision; no destructive action is proposed.

---

## ADR-B — Ownership of `facilities` / `organizations` / `national_facilities`

**Evidence.** These three tables survive `alembic downgrade base` (documented in
`DATABASE_COMPATIBILITY_REPORT.md` §9.7), and `national_facilities` is mapped by **two** ORM packages
(`NR-006`). Whether they are pre-existing tenant infrastructure or migration-owned objects is
undecided, which is why they were **not dropped**.

**Options.** B1 — declare them pre-existing baseline infrastructure (excluded from `downgrade base`
by design, documented as such). B2 — declare them migration-owned and add them to the downgrade path.
B3 — split: `national_facilities` migration-owned, the other two pre-existing.

**Recommendation: B1 with an explicit architecture record**, plus one authoritative ORM owner for
`national_facilities`. B2 is riskier (dropping a table that may hold national reference data).

**Unblocks:** release condition 5 (`MIG-EXISTING`) and `NR-006`. **Reversible:** yes (a follow-up
migration can drop or adopt them); deliberately not forced here.

---

## ADR-C — `care_continuum`: cross-cutting host or decomposed services?

**Evidence.** 45 tables, **0 migrated**; hosts primary care, maternal/child, immunization, chronic,
referral, home care and public health. Dental / rehabilitation / mental-health appear only as
signals.

**Options.** C1 — keep it as a **permanent cross-cutting host** with internal bounded modules.
C2 — decompose into 3–5 domains (each needing its own contract, migration set and isolation
certification). C3 — decompose only the referral + immunization paths now.

**Recommendation: C1 for this release cycle**, with C3 considered in W3 if service demand appears.
C2 multiplies contracts before any contract is STABLE (currently 0 stable).

**Unblocks:** contract 07 status. **Reversible:** yes.

---

## ADR-D — Audit coverage and replacement for blanket `system:admin`

**Evidence.** Several write paths still record `system:admin` as the actor, which makes the immutable
audit trail unable to attribute an action to a human or a specific principal.

**Options.** D1 — require a real principal on every audited write (reject writes without one).
D2 — introduce scoped service principals per subsystem. D3 — keep `system:admin` but add a
`source` field.

**Recommendation: D2 (scoped service principals) + D1 for human-initiated paths.** This preserves
attribution while allowing genuine internal jobs. D3 does not solve attribution.

**Unblocks:** release conditions 7 and 10; audit immutability claim. **Reversible:** additive field
and policy; existing rows are untouched.

---

## ADR-E — Public token/phone access model

**Evidence.** Some portal paths are reachable by possession of a token or a phone number rather than
an authenticated session (documented as public-by-design in `PUBLIC_ENDPOINT_REGISTER.md`).

**Options.** E1 — signed, short-TTL, single-use links bound to an entity, rate-limited, audited.
E2 — require full authentication everywhere (breaks patient-facing flows). E3 — keep as-is with
rate-limiting only.

**Recommendation: E1.** E2 breaks legitimate journeys (results delivery); E3 does not meet the
authorization bar.

**Unblocks:** contracts 04 and journey J4. **Reversible:** yes — interface-level change.

---

## ADR-F — Lab duplication (`lab_service` vs inline `routes/labs.py`)

**Evidence.** 9 service modules ported with tests, but only 5 routes delegate. `admin`,
`test_results`, `labs`, `samples` keep inline logic (2 216 LOC) while their service twins are **dead
code**. This is release condition 9.

**Options.** F1 — wire the routes to the services and diff OpenAPI before/after per route.
F2 — delete the unused services and keep inline logic. F3 — leave both (status quo).

**Recommendation: F1, one route per PR**, after the contract/exception mapping decision
(`DomainError` → `build_error_payload` vs `HTTPException` → `public_http_detail` — payload shapes and
Arabic/English messages differ, so behaviour is **not** guaranteed identical). F3 is what the
`NR-006-dupe` row incorrectly called "resolved".

**Unblocks:** release condition 9. **Reversible:** yes per route.

---

## ADR-G — Insurance provisioning: 5 live operations vs 84 unserved endpoints

**Evidence.** Live insurance surface = **5 operations**. `backend/app/insurance/api/*` exposes **84
endpoints** and is **imported by nothing**. Duplicate claims implementations exist
(`routes/claims.py` live, `insurance/api/claims.py` unserved). Verdict recorded as
**UNSERVED/BLOCKED**.

**Options.** G1 — provision insurance properly (mount, migrate its 30 tables, contract it).
G2 — archive the unserved API and declare insurance out of scope for this release.
G3 — leave it unserved but keep the code.

**Recommendation: G2** (or G1 only after a contract exists). G3 keeps a misleading surface and a
false capability signal.

**Unblocks:** contracts 05/06. **Reversible:** yes — archive preserves the code (see ADR-I).

---

## ADR-H — Shared Core boundary

**Evidence.** 50-service Shared Core registry exists, but the enforcement boundary (what a domain may
import across domains) is only partly gated; the domain isolation validator passes 11/11 on the
current manifest.

**Options.** H1 — codify an allow-list per domain, enforced in CI. H2 — rely on review only.
H3 — no boundary (status quo).

**Recommendation: H1.** It is the only option that makes cross-domain coupling a build failure rather
than a convention.

**Unblocks:** every contract row. **Reversible:** yes — the allow-list is configuration.

---

## ADR-I — Register or archive the unserved insurance API

**Evidence.** 84 endpoints, zero importers, zero tests, 30 unmigrated tables (see ADR-G).

**Options.** I1 — archive to `archive/legacy/` with provenance (single `git revert` restores it).
I2 — keep in place with a deprecation notice. I3 — delete.

**Recommendation: I1.** Archive-first is the program rule; deletion loses strategic code and I3 would
require the approval this request is asking for.

**Unblocks:** ADR-G. **Reversible:** yes, by design.

---

## ADR-J — Offline durability

**Evidence.** `backend/app/services/offline_sync_service.py` keeps the offline engine **in memory**;
a restart loses queued work. This cannot satisfy an offline-first national guarantee.

**Options.** J1 — durable queue (PostgreSQL outbox + idempotency keys) with conflict resolution.
J2 — device-side persistence only. J3 — document the limitation and gate the feature off.

**Recommendation: J1**, sequenced in W4 (after contracts 01/04 leave DRAFT). J3 is acceptable as an
interim **only** if the feature is gated off in production.

**Unblocks:** offline-first claim; journey J6. **Reversible:** yes — additive tables.

---

## Decision summary table

| ADR | Topic | Recommended | Unblocks | Status |
|---|---|---|---|---|
| A | 426-table migration strategy (NR-011 first) | A1 + A3 | strict-schema release, W1 | **PENDING** |
| B | 3 ambiguous tables' ownership | B1 + single ORM owner | condition 5, NR-006 | **PENDING** |
| C | `care_continuum` shape | C1 (host) | contract 07 | **PENDING** |
| D | Audit attribution | D2 + D1 | conditions 7, 10 | **PENDING** |
| E | Public token/phone access | E1 | contract 04, J4 | **PENDING** |
| F | Lab/service duplication | F1 per route | condition 9 | **PENDING** |
| G | Insurance provisioning | G2 (or G1 after contract) | contracts 05/06 | **PENDING** |
| H | Shared Core boundary | H1 (CI-enforced) | all contracts | **PENDING** |
| I | Unserved insurance API | I1 (archive) | ADR-G | **PENDING** |
| J | Offline durability | J1 (durable queue) | offline-first claim | **PENDING** |

**Additional decision required (not an ADR):** the rollback procedure must be recorded as
**snapshot restore**, or **`downgrade base` + `upgrade head`**. A partial rewind to a prior release
revision is **proven unsafe** (exit 0 while leaving 2 version rows and 7 residual tables) and must
never enter a runbook. Source: `PHASE_C_DATABASE_REHEARSAL_REPORT.md` §5.

---

## W1 addendum (2026-11-17) — strict-schema evidence refines ADR-A and the NR-011 prerequisite

**This addendum adds evidence; it does not change any recommendation or approve anything.**

1. **ADR-A is now quantified functionally, not only structurally.** Running 53 modules / 872 tests
   against a migration-only PG16 clone gives **753 passed / 119 failed**, while the identical modules
   give **872 / 872** under the SQLite `create_all()` control. 4 P0 patient-workflow modules fail
   (ICU/LIMS 6/7, emergency surgery 2/4, pharmacy/radiology 1/3, pharmacy POS 0/3). The unmigrated
   tables are therefore a **release-blocking functional gap**, not bookkeeping.
2. **The 426-table figure has a companion measurement.** Per declarative base the migrated database
   has **416 / 756** ORM tables (**340** missing) and **82 migrated tables lack 664 ORM columns**.
   The earlier 407 / 833 / 426 figure uses a different (per-context) denominator. Both are valid;
   neither supersedes the other. The per-base figure is the one directly exercised by the suite.
3. **NR-011's prerequisite is two-part, not a one-line import.** Probe B (import
   `app.national.domain`) **moves** the error to `national_patients`, because all four
   `ehr_allergies` FKs are cross-metadata (`EHRBase.metadata → NationalBase.metadata`) and cannot
   resolve in any import order. Probe C (7 omitted bases + one merged `MetaData`) eliminates
   `NoReferencedTableError` and exposes the real diff (284 distinct missing tables). Recommended
   ordering is unchanged: **NR-011 fix → ADR-A authoring → strict suite green**.
4. **ADR-B is unchanged but now gates more.** The three residual reference tables still need an
   owner; W1 does not alter that analysis.
5. **New supporting decision (not an ADR):** the fixture write leak (`SessionLocal` bound to the
   engine instead of the savepoint connection) must be fixed before strict runs are repeatable —
   otherwise run #2 self-poisons the audit-chain assertions. No production change.
6. **ADR-A option A4 (`create_all()` for the remainder) is now empirically rejected.** The control
   run proves `create_all()` makes the suite green while the migrated schema does not, which is
   exactly the masking behaviour A4 would institutionalise.

Full evidence: `GOVERNANCE/W1_CHECKPOINT.md` and `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md` §11.

**No decision in this document has been implemented. No schema, ownership, activation or
authorization change was made on the strength of an unapproved ADR.**
