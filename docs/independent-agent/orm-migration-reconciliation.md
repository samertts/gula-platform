# RB-2 — ORM ↔ migration reconciliation

Measured against the **proven** migration-head database, not against a
pre-existing fixture: `gula_agent2`, dropped and recreated, migrated to
`20260916_0001` (112/112, 0 errors, 423 tables) from
`claude/p0-2-pharmacy-reconciliation`. ORM inventory taken from that same lineage
with the app assembled.

## Reproduced inventory

| | count |
|---|---|
| ORM-mapped tables | **780** |
| physical tables at head | **423** |
| mapped **and** present | **409** |
| mapped, **not** present | **371** |
| physical, **not** mapped | **14** |

### Correction to my own earlier figures

The earlier audit reported "564 ORM tables, 222 discrepancies". Both numbers were
right about what they measured and wrong as a description of this question:

* **564** was the table count inside `SHARED_METADATA` on
  `claude/autonomous-run-1` — one namespace, not every mapped table. Counting all
  mapped classes gives **780** on either lineage.
* **222** was measured against `gula_canon`, a fixture; **371** is measured
  against a database that provably reaches head.

So the discrepancy is larger than first reported, and the denominator was wrong.
Recorded rather than quietly replaced.

## The decisive classifier

**369 of the 371 absent tables are named in no migration at all** — not in a
`create_table`, not in a reference, nowhere in 112 files. They are therefore not
"an unreached lineage": nothing in the migration layer has ever heard of them.
Only two are named anywhere, and neither is created (§ IA-004).

## Classification by module, with evidence

`served` means the assembled app serves at least one path under that module's
prefix — i.e. the subsystem has a live HTTP surface while its tables do not exist.

| module | absent tables | named in any migration | served | class | action |
|---|---|---|---|---|---|
| `national` | 92 | 2 | yes | **B** dormant, + 2 × **F** (IA-004) | needs the national canonical-table decision |
| `governance` | 58 | 0 | yes | **B** | owner decision per subsystem |
| `care_continuum` | 45 | 0 | yes | **B** | owner decision |
| `clinical` | 39 | 0 | yes | **B** | owner decision |
| `national_data` | 36 | 0 | yes | **B** | owner decision |
| `document_intelligence` | 21 | 0 | yes | **B** | owner decision |
| `ehr` | 18 | 0 | yes | **B** → **RB-3** | see RB-3; 54 served paths |
| `health_data` | 17 | 0 | yes | **B** | owner decision |
| `hospital` | 10 | 0 | yes | **B** | 4 hospital tables DO exist; the 10 are beyond `efcc4b6e`'s minimal set — the open NR-028 scope question (3 vs 13) |
| `roadmap` | 8 | 0 | yes | **B** | non-clinical |
| `research_platform` | 7 | 0 | no | **B** | unserved |
| `financial` | 6 | 0 | no | **A** intentionally unmanaged | CLAUDE.md: Financial Engine Phase A is schema-only and flag-gated |
| `command_intelligence` | 5 | 0 | no | **B** | unserved |
| `simulation` | 5 | 0 | yes | **A/B** | simulation harness, not clinical record |
| `knowledge_graph` | 3 | 0 | yes | **B** | owner decision |
| `radiology` | 1 | 0 | yes | **B** | one table; `radiology_ai_analysis_jobs` exists physically but unmapped (below) |

**No migration was created.** 369 tables belong to dormant subsystems whose table
shape is a domain design decision; authoring them from ORM declarations would be
inventing schema at scale, which is the failure mode this classification exists to
prevent. Category **F** applies to exactly two tables, and both are gated (IA-004).

## The 14 physical tables with no ORM model

| table | class | evidence |
|---|---|---|
| `alembic_version` | **C** generated | Alembic's own bookkeeping |
| `fin_ads_campaigns`, `fin_ads_clicks`, `fin_ads_conversions`, `fin_clinical_behavior`, `fin_fraud_logs`, `fin_market_benchmarks` | **A** intentionally unmanaged | Financial Engine Phase A is schema-only; `ENABLE_FINANCIAL_ENGINE` / `ENABLE_ADS` default off. Physical-without-ORM is the intended Phase A state |
| `gov_guardians`, `gov_qr_codes`, `gov_recovery_requests` | **G** | created by migration, no ORM owner. Needs an owner answer: is access intended via raw SQL, or is a model missing? |
| `idempotency_keys` | **A** | written by the canonical idempotency helper, not an ORM entity |
| `radiology_ai_analysis_jobs` | **G** | same shape as `gov_*` |
| `sndhs_audit_logs`, `visits` | **A** | SNDHS Phase 1, created by the `20260505_000x` series and gated behind `SNDHS_ENABLE_VISITS` |

Ten of fourteen are explained by documented intent. **Four (`gov_*` ×3,
`radiology_ai_analysis_jobs`) are category G** and need an owner statement: a
migrated table with no model is reachable only by raw SQL, and nothing records
whether that is the design.

## IA-004 — P1 — a guarded foreign key silently leaves PHI authorization unenforced

**This is the one concrete defect RB-2 surfaced, and it is not a missing table.**

`20260811_0002_citizen_relationship_foundation.py:68-82` creates four foreign keys
through a guard:

```python
for constraint_name, column, target_table in (
    ("fk_citizen_relationship_user",     "legacy_user_id",     "users"),
    ("fk_citizen_relationship_lab_user", "legacy_lab_user_id", "lab_users"),
    ("fk_citizen_relationship_citizen",  "citizen_id",         "national_citizens"),
    ("fk_citizen_relationship_patient",  "patient_id",         "national_patients"),
):
    if _has_table(target_table):
        op.create_foreign_key(...)
```

`users` and `lab_users` exist, so those two constraints are created.
`national_citizens` and `national_patients` **do not exist and are created by no
migration**, so those two are **silently skipped**. Confirmed physically: a query
of `information_schema` on the head database returns **0** foreign keys targeting
either table.

**Why this matters more than the missing tables themselves.**
`niam_citizen_relationships.citizen_id` and `.patient_id` are the columns
`require_citizen_relationship` matches on — the router-level dependency that
authorizes all 17 `/citizen-platform/{citizen_id}` PHI routes (verified correct in
IA-002). The authorization logic is sound; the data it trusts has **no referential
integrity**. A relationship row can name a citizen or patient that does not exist,
and the database will not object.

The guard itself is defensible — it is why head builds at all — but a guard that
turns a referential-integrity constraint into a no-op without recording the fact
is a false green at the schema layer. `alembic upgrade head` reports complete
success while two designed constraints are absent.

**Recommended fix, not implemented here:** the honest options are (1) create the
`national_citizens` / `national_patients` tables and the two constraints, which is
the canonical-table decision this audit cannot take; or (2) keep the guard and add
a post-migration assertion that lists every constraint it skipped, so a
successfully migrated database states which of its designed constraints do not
exist. Option 2 is independently valuable and safe, and belongs with the RB-6
preflight work.

**Status:** OPEN, reported. Not fixed: option 1 requires a schema-ownership
decision, and option 2 touches migration tooling the other lane is actively
changing.

## RB-2 acceptance

Every one of the 385 discrepancies now has a documented reason: 369 dormant or
intentionally-unmanaged tables classified by module with migration and served
evidence, 2 genuine category-F tables identified and gated, and 14 physical
orphans classified with 4 flagged as needing an owner statement. No migration was
authored, no model deleted, no table fabricated.
