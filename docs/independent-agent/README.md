# Independent agent — scope, isolation and method

**Worktree:** `/home/user/gula-audit` · **Branch:** `claude/independent-audit-1` ·
**Base:** `203c85aa` on `claude/autonomous-run-1`.

## A disclosure that matters for reading these findings

This agent and the agent that produced commits up to `203c85aa` on
`claude/autonomous-run-1` are **the same session**. The brief that created this
role describes a "primary agent" owning NR-164; NR-164 does not exist in this
lane's register, which ends at NR-089. NR-164 belongs to the **sibling lane**,
`claude/p0-2-pharmacy-reconciliation` (PR #258), which is a different branch in a
different container.

So "independent" here means one thing honestly and not another:

* **Honest:** this pass works in its own worktree, touches no file the sibling
  lane owns, and re-derives every claim from the code rather than from the
  register.
* **Not claimed:** independence from the author of `claude/autonomous-run-1`.
  Where a finding concerns that lane's own work it is marked SELF-REVIEW, because
  a second look by the same author is worth less than a second author and saying
  otherwise would be the kind of false assurance this whole register exists to
  prevent.

## Method

Every finding below was reached the same way, and the order is deliberate:

1. a cheap structural sweep to locate candidates;
2. **reading the candidate**, because three of this pass's five leads died there;
3. measuring the *effective* path — for routes that means the served OpenAPI
   surface and router-level dependencies, never the route signature;
4. only then a severity.

The three leads that died are recorded in `findings.md` as verified negatives
rather than dropped. A sweep that reports only what survived is a sweep whose
false-positive rate you cannot see.

## Isolation actually held

`git worktree list` shows two trees on two branches. Nothing outside
`/home/user/gula-audit` was written during this pass. No push, no force-push, no
history rewrite, no branch checkout in the other tree.

## Release-blocker passes

| pass | subject | artifact | outcome |
|---|---|---|---|
| RB-1 | migration head on the integration lineage | `rb1-migration-head.md` | RESOLVED — 112/112, head `20260916_0001`, 423 tables, round-trip passes |
| RB-2 | ORM ↔ migration reconciliation | `orm-migration-reconciliation.md` | RECONCILED — 780 mapped / 423 physical / 371 absent / 14 orphan; accepted for inventory; IA-004 raised |
| RB-3 | the served `/ehr` surface, end to end | `rb3-ehr-surface-audit.md` | AUDITED — 53 BROKEN, 1 PARTIAL, 0 REAL of 54 paths; IA-005 (P0) and IA-006 (P1) raised |

| IA-005 / IA-006 | remediation of the two findings RB-3 raised | `ia005-ia006-remediation.md` | IA-005 **RESOLVED** (mapper-driven serializer across 12 ORM bases); IA-006 **OPEN**, zero migrations authored — ADR-016 forbids the tables; IA-007 raised |

| IA-005 addendum | full serializer sweep, 137-model impact matrix, per-operation EHR verification | `ia005-ia006-addendum.md`, `ia005-impact-matrix.md`, `ia006-per-operation.md` | 5 further live sites fixed; `col.key` conclusion corrected; exposure measured (34 HIGH, 10 live) |

| IA-006 decision package | 18-table architectural decision matrix, `national_patients` analysis | `ia006-decision-package.md` | **NEEDS_DECISION** — one question, not eighteen; zero migrations; lane-independence verified |

| national_patients | end-to-end trace + historical archaeology | `national-patients-decision-package.md` | **BLOCKED on NR-022** — already the programme's own named decision; pharmacy identity is **coherent** in the shipping lineage (NO DEFECT FOUND) |

| IA-014 / IA-015 / IA-016 | kernel event bus reachability, protocol and admin surface | `ia014-ia016-decision-package.md` | IA-015 **FIXED** (dead `hasattr` probe on 89 served paths / 115 ops); IA-013a **FIXED** (unbounded `EventStore`); IA-014 and IA-016 **NEEDS_DECISION** — IA-016 deliberately unfixed because the obvious one-line repair raises `AttributeError` on 130 served ops in 4 clinical domains. Corrects IA-013's subscriber claim: **zero** kernel-bus subscribers exist in production code |

| IA-017 / IA-018 | offline sync and conflict resolution, end to end | `findings.md`, `test-matrix.md` | Both **NEEDS_DECISION**. The platform's only served offline-sync endpoint cannot produce a non-zero result and reports `"engine": "active"`; `ConflictResolver.resolve` is called **0** times in a full cycle; `sync_to_edge` reports `records_synced: N` while discarding the payload. Four classes share the name `OfflineSyncEngine`, and the most sophisticated one — the only one with its own test file — has **zero** production importers and 5 real defects |

| Lab Result Workflows | order → test type → specimen → result → validation → report → audit/event, end to end | `findings.md`, `test-matrix.md` | IA-019 and IA-020 **FIXED** (3 of 4 write paths wrote no test-type link; a critical analyzer result was stored unflagged); IA-021 and IA-022 **NEEDS_DECISION** (the MoH DHIS2 export cannot report an abnormal result; three event buses with zero subscribers). Corrects the task premise: `test_type_id` is nullable in all three lineages and in the migrated database — NR-164 did not close it here. 7 verified negatives recorded |

| Lab Result Workflows (cont.) | NR-164 premise re-measured; write-path matrix; analyzer boundary; result update | `findings.md`, `test-matrix.md` | **NR-164 premise corrected**: CODE/MIGRATION/DATABASE separated — no code↔DB mismatch exists, and migrations `20260930_0001/0002` are absent from every worktree *and every git ref*, so NR-164's content is **BLOCKED, not disproven**. IA-024 mechanism **FIXED** (24 of 37 critical-capable tests have no catalog entry, so the earlier fix was necessary but **not sufficient**); IA-026 **FIXED** (a `unit`-only PATCH blanked value and both ranges while leaving `flag='critical'`); IA-025 recorded (a third, unreachable lab-result writer). **Proven: a bare NR-164 NOT NULL would reject every result for an uncatalogued test, even after the fixes.** |

RB-5, RB-4 and RB-6 are not started.

