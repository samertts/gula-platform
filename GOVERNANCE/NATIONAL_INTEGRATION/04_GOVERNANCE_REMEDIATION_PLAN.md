# Governance Remediation Plan

**Document:** 04 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `IMPLEMENTED` (classification and remediation routes defined; no governance outcome invented).

---

## 1. Principle

The engagement directive permits **synthetic-safe technical evidence work and preparation of decision packages for the named owners**. It does **not** permit changing an owner's recorded decision, and this program does not claim any owner decision has been superseded. Therefore:

- Original records (`FINAL_DECISION.md`, MPI audit/findings, `ADR_DECISION_REQUEST.md`, GECS registries) are read-only evidence.
- Every status change is a **new** record under `GOVERNANCE/NATIONAL_INTEGRATION/` that references the original by md5 and states exactly which evidence changed.
- `HOLD` and `REJECT` remain the effective verdicts until an owner signs a superseding package (`05_DECISION_PACKAGES.md`).

## 2. Item classification and route

| Item | Current | Technically remediable now? | Route | Target status in this program |
|---|---|---|---|---|
| MPI **REJECT** (AUD-02 HIGH: DB UNIQUE not applied) | OPEN | **Partially** — app-layer controls verified; DB UNIQUE needs owner migration | MP-001 package + disposable-clone rehearsal | `BLOCKED` → `TESTED` evidence only |
| MPI AUD-07 (MEDIUM re-resolve) | BLOCKED | No — behavior change needs D-MPI-5 / ODR-002 | Decision package ODR-002 | `BLOCKED` |
| MPI AUD-16 (INFO fork-response) | BLOCKED | No — policy needs D-MPI-3/4 / ODR-003 | Decision package ODR-003 | `BLOCKED` |
| MP-001 | Owner-gated | Rehearsal on disposable clone only | `05` package §2 | `BLOCKED` |
| ODR-001…004 | Owner-gated | Packages can be prepared | `05` §3 | `BLOCKED` |
| D-020 (security certification) | PENDING | No — human security sign-off | `05` §4 | `BLOCKED` |
| D-021 (clinical certification) | PENDING | No — human clinical/legal sign-off | `05` §4 | `BLOCKED` |
| ADR-A (426-table migration strategy) | PENDING | NR-011 prerequisite engineering is `TESTED`; decision still needed | `05` §5 | `BLOCKED` (NR-011 prerequisite no longer outstanding) |
| ADR-B (3-table ownership) | PENDING | No — DB owner decision | `05` §5 | `BLOCKED` |
| ADR-C (care_continuum host) | PENDING | No — architecture decision | `05` §5 | `BLOCKED` |
| ADR-D (audit actor) | PENDING | Design package only; no blanket `system:admin` change without decision | `05` §5 | `BLOCKED` |
| ADR-E…J | PENDING | No — architect/owner decisions | `05` §5 | `BLOCKED` |
| NR-011 (`alembic check` abort) | `TESTED` | **Done** — 14/14 regressions + disposable-PG proof, 0 metadata aborts | recorded in `13` §2.1 | `TESTED` (complete) |
| HOLD release decision | HOLD | No — owner only; 5 exit criteria unmet | `05` §6 | `BLOCKED` |

## 3. What this program may legitimately change

1. **Evidence status only** — e.g. a finding's `TESTED` evidence can be extended with new synthetic regressions, but its owner-gated verdict cannot be flipped.
2. **Technical prerequisites** — NR-011 is engineering work; fixing it does **not** approve ADR-A.
3. **Decision-package completeness** — packages can reach `IMPLEMENTED` (written, evidence-linked) without the decision being made.
4. **Synthetic gate coverage** — new tests may be added; no existing assertion may be removed or weakened.

## 4. Forbidden transformations (explicit)

- Rewriting `HOLD` → `GO` or `REJECT` → `ACCEPT` in any original file.
- Applying MP-001 to a non-disposable database.
- Activating a dormant router/engine to "prove" coverage.
- Recording a skipped/unimplemented item as passed.
- Using a demo as production validation.
- Claiming SNOMED CT / official terminology validation without a license.

## 5. Traceability requirement

Every superseding record must contain: original document path + md5, exact finding IDs addressed, command + exit code + counts of the evidence run, boundary statement (synthetic / disposable), and the named authority still required. `status_registry.json` is the machine-readable index of these records.
