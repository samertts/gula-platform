# GULA DATABASE OWNERSHIP PROPOSAL — ADR-A / ADR-B (owner decision C)

**Directive:** GULA-OWNER-GATE-2026-11-20 §3C · **Decision IDs:** `OD-003` (ADR-A), `OD-004` (ADR-B)  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-20  
**Method:** read-only. No DDL, migration, metadata registration, DB connection, test run or Git write was performed. This is a proposal, not an approval and not a work order.

---

## 1. Problem statement (source-grounded)

| Fact | Exact value | Source |
|---|---|---|
| Declarative bases on disk | **19** | `GULA_ORM_MIGRATION_COMPLETENESS_REPORT.md` §2 |
| Bases registered in `backend/migrations/env.py` | **17** | same |
| Unregistered bases | `DocIntelBase` (21 tables), `InsBase` (30 tables) | same, rows 18–19 |
| Tables on unregistered bases | **51** (21 + 30), `OWNERSHIP_UNCLEAR`, 0 migration references | same, §3 |
| Distinct ORM table names | **834** (835 definitions; one duplicate `national_facilities`) | same, §2 |
| Migration-referenced table names | **493** | same, §3 |
| Exact source-based discrepancy | **354** at HEAD `2206654` | same, §3 |
| Historical discrepancy (preserved, not current) | **426** per-context at `2827c1ff`; 340 per-base; 284 probe-C | same, §3.1 / §11 |
| 354-table classification | `261 ACTIVE_REQUIRED` · `51 OWNERSHIP_UNCLEAR` · `22 DORMANT` · `20 UNUSED` | same, §4 matrix (354 classified rows) |
| FK / enum complexity | 188 tables with `ForeignKey`, 126 with enum columns | same, §3 |
| Alembic head | exactly one, `20261119_0003` (111 revisions, 0 orphan roots) | same, §3.2 |
| Duplicate ownership | `national_facilities` mapped by `models/clinical_scope.py:136` and `national/domain/facility.py:9` | same, §6 |
| Test masking | `backend/tests/conftest.py` uses `create_all()` from combined metadata; strict gate `FAILED` | `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` §4; `GULA_W017_STRICT_GATE_REASSESSMENT.md` §1 |

**GULA constitution constraint (non-negotiable):** dormant modules are strategic assets. "Non-shipping" must never become deletion, archival without evidence, or activation of unfinished functionality.

---

## 2. The four alternatives

| # | Alternative | Definition |
|---|---|---|
| **1** | Register all existing ORM bases centrally | Import all 19 bases into `backend/migrations/env.py` under one shared `target_metadata`, then authorize migrations for all 354 tables. Equivalent to ADR-A A1's first half without domain registries. |
| **2** | Establish explicit domain-owned metadata registries | Each bounded context publishes a registry of its own `DeclarativeMeta` objects; `env.py` imports the registries and unions them into Alembic metadata. A domain owns its schema, keys, indexes and downgrade path. |
| **3** | Consolidate only confirmed active models | Migrate the `261 ACTIVE_REQUIRED` tables only; leave the other 93 to a later, explicit decision. |
| **4** | Retain dormant modules outside the active migration chain | Record a ship/no-ship declaration for the `22 DORMANT` + `20 UNUSED` tables; keep the code intact and unactivated, excluded from release migrations (ADR-A A3). |

Rejected out of hand (existing ADR-A A2/A4): one bulk "baseline everything" revision (unreviewable, unattributable failures) and deploy-time `create_all()` (abandons migration integrity and permanently masks drift).

---

## 3. Evaluation across the seven required criteria

| Criterion | 1 — central registration | 2 — domain-owned registries | 3 — active only | 4 — dormant outside chain |
|---|---|---|---|---|
| **Migration safety** | Autogenerate finally sees all 51 blind tables, but one global diff over 354 tables with 188 FKs is high-risk and hard to attribute | Best: one registry = one reviewable per-context revision, ordered FK handling, strict round-trip each; autogenerate still sees all bases | Good for the 261 active; silently defers 93, so the matrix remains partially uncovered | Safe for retained code; must be paired with an explicit non-shipping record — never a silent omission |
| **Data integrity** | Highest short-term risk: a single revision can create wrong constraints across domains; national reference data at risk | High: domain owners define constraints; ADR-B reference tables kept as baseline infrastructure and never dropped | Preserves active integrity; unclear-ownership tables (51) stay unowned, including live doc-intel/insurance consumers | Preserves dormant data by not touching it; requires an inventory entry so "non-shipping" cannot be misread as "absent" |
| **Domain isolation** | Weakest: one shared metadata re-couples all domains through Alembic and invites cross-domain FK edges | Strongest: ownership and revision boundaries align with bounded contexts; CI can enforce a registry allow-list (ADR-H) | Neutral: reduces scope but does not define ownership | Strong: dormant surfaces do not enter the active dependency graph |
| **Maintainability** | Simple file, enormous review surface; future autogenerate noise grows | More structure (one registry per domain) but small, attributable diffs and clear ownership | Moderate; leaves a permanent "deferred" backlog | Good; explicit ship/no-ship list is auditable |
| **Upgrade complexity** | One giant upgrade step; ordering of 188 FKs / 126 enums is fragile | Sequential per-context upgrades; each reversible and independently testable | Manageable for 261 tables; deferred 93 need a later wave | No upgrade cost; zero DDL |
| **Downgrade safety** | One global downgrade can drop shared tables; ADR-B tables must be excluded by design | Per-context `downgrade()` tested upgrade→downgrade→re-upgrade; ADR-B B1 keeps `facilities`/`organizations`/`national_facilities` intact | Each active revision reversible; deferred tables never touched | Nothing to downgrade — inherently safe |
| **Long-term national scalability** | Central coupling becomes a bottleneck as domains grow; violates Domain Sovereignty direction | Best: new domains add a registry + one revision; supports ministry/hospital/lab hierarchy and national rollout | Scales only for shipped contexts; permanent incomplete matrix | Correct for strategic dormant assets; must keep them mergeable into future national releases |

---

## 4. Recommendation

**Adopt Alternative 2 as the ownership architecture, with the safe parts of Alternative 1, sequenced by Alternative 3 and complemented by Alternative 4.**

Concretely:

1. **Ownership:** each bounded context publishes an explicit metadata registry; `env.py` imports registries only (no direct model imports scattered through migrations). This satisfies the architecture gate and ADR-H.
2. **Visibility:** register `DocIntelBase` and `InsBase` so Alembic autogenerate is no longer blind to 51 live tables — but registration alone is not a migration authorization.
3. **Sequencing:** migrate `261 ACTIVE_REQUIRED` tables one context per revision, priority `P0` (unregistered bases, ≥20 app refs, patient/claim-critical) first; strict round-trip proof for every revision.
4. **Dormant strategy:** record ship/no-ship for `22 DORMANT` + `20 UNUSED`; keep all code, mark non-shipping in release notes; no deletion, no `create_all()`, no activation.
5. **ADR-B:** option **B1** — `facilities`, `organizations`, `national_facilities` are pre-existing baseline infrastructure, excluded from `downgrade base` by design; assign a single ORM owner for `national_facilities` in a separate reversible change.

This is the least-risk extensible path because it converts one unreviewable 354-table problem into small, attributable, independently reversible changes while preserving domain isolation and the national platform's dormant strategic assets. It is equivalent to ADR-A A1 + A3 and ADR-B B1, and it never uses A2 or A4.

---

## 5. Exact scope this proposal does **not** authorize

- No migration file, DDL, metadata edit, `env.py` edit, or test change was made.
- No production or shared database connection; no `alembic stamp`; no `create_all()`; no downgrade on any real database.
- No deletion or archival of dormant models; no feature activation; no route changes.
- No commit, staging, push, merge, PR or deployment.
- No change to the protected MD5s, 20 staged `R100` renames, sibling repo, or any pre-existing work.
- No release or `PRODUCTION READY` claim; HOLD unchanged.

---

## 6. Approval required (exact text)

> *"I approve ADR-A as amended in `GULA_DATABASE_OWNERSHIP_PROPOSAL.md`: domain-owned metadata registries imported into `env.py`, registration of `DocIntelBase` and `InsBase`, context-by-context additive reversible migrations with disposable-PG16 upgrade/downgrade/re-upgrade proof, and a recorded ship/no-ship declaration for the 22 DORMANT and 20 UNUSED tables; no bulk revision, no `create_all()`, no production DDL in this approval."*

> *"I approve ADR-B option B1: `facilities`, `organizations` and `national_facilities` are pre-existing baseline infrastructure excluded from `downgrade base` by design, with one named ORM owner for `national_facilities`."*

Approvers: Program Director / Architect (ADR-A) and Database owner (ADR-B). Each approval is separate; neither is recorded here.

---

## 7. Reversal strategy

- `env.py` registration: one file, one targeted revert; no data change.
- Each context revision: additive, independent `downgrade()`, verified on disposable PG16; a single `git revert` restores the previous state.
- ADR-B: documentary only; a later migration may adopt or drop the tables under a new decision.
- Ship/no-ship declarations: dated records, superseded by new records; code is never deleted.

---

## 8. Non-claims

No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` award is made here. Historical discrepancy figures (426/340/284) are preserved and reconciled to 354, not overwritten. No test was run; no schema was inspected live; no owner approval is invented. Standing decision **HOLD**; Stable v1.0.0 **NOT declared**; `production_ready_items = 0`.
