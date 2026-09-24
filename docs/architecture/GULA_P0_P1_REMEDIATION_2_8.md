# GULA P0 / P1 Remediation — BATCH-2.8

**Baseline:** branch `claude/p0-2-pharmacy-reconciliation`, HEAD `ae3e1f56`
(BATCH-2.7), clean tree, Python 3.13.12, PostgreSQL 16, Alembic head
`20260912_0001`, 106 migrations.
*(The batch brief named `7319dc0d`; that is one commit stale — BATCH-2.7 landed
and closed NR-029.)*

---

## 1. NR-026 — the finding was far too small

I recorded this in BATCH-2.7 as *"two nursing features fail at runtime"*.
BATCH-2.8 executed the queries instead of reasoning about them:

```
ClinicalChecklist  UndefinedTable   relation "nursing_checklists" does not exist
EscalationRecord   UndefinedTable   relation "nursing_escalations" does not exist
NursingNote        UndefinedColumn  column nursing_notes.encounter_id does not exist
NursingShift       UndefinedColumn  column nursing_shifts.department_id does not exist
```

**Every nursing model fails on a plain SELECT.** The whole domain is
non-functional — not two features.

| Measured | Value |
|---|---|
| Nursing models | 15 |
| Models naming a table that does not exist | 2 |
| Models whose PK is `String(26)` against a physical `INTEGER` | **13 of 13 that have a table** |
| Type mismatches across the domain | **97** |
| ORM columns with no physical column | **137** |

This is the Pharmacy P0-2 defect at Pharmacy's scale, in a domain never
reconciled. Pharmacy took four milestones (M1–M4) to fix 27 tables.

### `escalated_to` — semantics proven, not assumed

Migration `20260716_0002` declares
`sa.Column("escalated_to", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"))`,
and the constraint exists in a database at head. It is a `lab_users` foreign
key, Integer. The ORM's `String(26)` is simply wrong. No guessing was required.

### Data risk: none

No application code, raw SQL, seeder or generator anywhere names
`nursing_clinical_checklists` or `nursing_escalation_records`, and the ORM that
would have written the other thirteen cannot execute a statement against them.
**The tables are provably empty.** The reconciliation therefore needs no data
migration and no backfill — the physical schema is already correct and complete.

### Repair status — **BLOCKED**, deliberately

Not repaired in this batch, for a reason rather than for lack of time:

- The primary key type is wrong on **all fifteen**. They reference each other,
  so they must move together — a piecemeal fix breaks the FKs between them.
- Fixing two of fifteen would leave the only two correct models sitting on a
  base (`NursingBaseEntity`) that is itself wrong, which is worse than uniform.
- The correct shape is the M1–M4 pattern already proven for Pharmacy: rewrite
  every model from the physical schema, then reconcile services and routes.

That is its own authorised batch, not a sub-item of one that also carries a
repository-wide reduction scan. **`backend/tests/test_nursing_domain_contract.py`
pins the exact scope** — 15 models, 2 missing tables, 97 mismatches, 137 phantom
columns — so the reconciliation has a target and the defect cannot be forgotten
or quietly grow.

## 2. Sample transition idempotency — **FIXED**

`POST /samples/{id}/transition` required an `Idempotency-Key`, then discarded it
without claiming a receipt.

**Replay was never able to apply the transition twice.** The service takes a row
lock and validates against a strict map
(`collected → identified → received → testing → validated`), so a second call
fails the state check. That is a refusal, not the canonical replay answer, and it
said nothing about a reused key carrying a *different* payload. It also left this
the only guarded Blood Bank route writing **no audit entry**.

Fixed by claiming and completing a receipt through the existing
`ClinicalCommandGuard` — no second idempotency mechanism. Four regressions in
`backend/tests/blood_bank/test_sample_transition_idempotency.py`; **three of four
fail with the fix reverted**:

| Property | Result |
|---|---|
| first valid request succeeds, one receipt, one audit entry | PASS |
| exact replay: no second effect, no second receipt, no second audit event | PASS |
| same key + different payload refused | PASS |
| missing key still refused | PASS |

## 3. Carried forward, verified unchanged

| Finding | Status | Evidence |
|---|---|---|
| NR-029 | **VERIFIED** — still closed | `PHANTOM_FK_TARGETS` empty; guard passes |
| NR-030 | **PARTIALLY VERIFIED** | 12 classified; condition-E guard passes |
| NR-023 | **BLOCKED** by NR-006 + NR-030 | unchanged |
| NR-006 | **PARTIALLY VERIFIED** | not merged; BATCH-3 item 1 |
| NR-007 | **PARTIALLY VERIFIED** | 7 LIVE / 6 DEAD / 15 UNRESOLVED |
| NR-018 | **PARTIALLY VERIFIED** | Pharmacy + NHDW VERIFIED; 6 partial |
| NR-027 | **PARTIALLY VERIFIED** | 7 routes classified; 1 of them fixed above |
| NR-022 | **BLOCKED** | National Core out of scope |
| MCM-P0-1..4 | **BLOCKED / dependent** | P0-1..3 depend on NR-023; P0-4 is CI-scope framing, unchanged |

No National Core table was created. No migration was created or modified.

## 4. Verification

```
alembic upgrade head / downgrade -1 / upgrade head   exit 0, PYTHONPATH unset
423 tables, 7/7 CI-required, head 20260912_0001
migrations: 106 files before and after, git clean

test_alembic_metadata_registry.py            5 passed
test_nursing_domain_contract.py              3 passed
test_identity_contract_guards.py             5 passed
blood_bank/ (incl. 4 new idempotency tests) 54 passed
blood_bank/test_state_registry_guard.py      4 passed
ruff on changed files                        no new findings (21 vs 22 at HEAD)
```
