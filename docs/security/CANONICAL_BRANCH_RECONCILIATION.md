# Canonical Branch Reconciliation — Diff Map & STOP Report

**Status of this document: DIAGNOSTIC, NOT A COMPLETED RECONCILIATION.**
Per Phase 10/Phase 15 of the "GULA Canonical Baseline Reconciliation"
directive, this pass gathered real, git-derived evidence (Phases 0-4, plus
a sampled Phase 5/8) and found **concrete, material conflicts that meet
this program's own STOP conditions**. No merge, no cherry-pick, and no new
branch were created this pass. Nothing was pushed except this document (on
the existing `claude/mustafa-parallel-engineering` branch, which was not
otherwise modified).

## 1. Branches and re-measured state (Phase 0)

Re-fetched and re-measured from git directly, not assumed from prior reports:

| | Branch | HEAD (re-measured) | Unique commits vs `main` |
|---|---|---|---|
| A | `claude/mustafa-parallel-engineering` | `ac68a0a55ddaf6ce17ffb3c314b8803bd318dfae` | 139 |
| B | `claude/p0-2-pharmacy-reconciliation` | `ce097a0c52aa49a2b9aef335066f37f8b979e026` | 176 |
| — | `main` | `46158e905fd97f57ca21c61bb5574d03aed90293` | — (common ancestor) |

**Important**: Branch B's HEAD has moved since it was last reported
(previously `96f40e02`) — it gained further commits between this program's
Batch 8 and this reconciliation pass. Re-measured fresh per the directive's
own instruction not to trust old numbers.

Common ancestor for all three: `46158e90` (confirmed via `git merge-base`
pairwise across all three refs — identical result each time).

Working tree at reconciliation start: **clean** (`git status --short`
empty). No stash, reset, or checkout was needed or performed.

## 2. Scale of divergence (Phase 1)

| | vs `main` |
|---|---|
| Branch A (Mustafa) | 260 files changed, +32,356 / -1,036 |
| Branch B (Pharmacy) | 535 files changed, +148,276 / -6,110 |

**Files touched by both branches (real overlap/conflict surface): 73**,
including — critically — `backend/app/security/rbac.py`,
`backend/app/lims/services.py`, `backend/app/lims/routes.py`,
`backend/app/services/hospital_service.py`, `backend/app/routes/hospital.py`,
`backend/app/routes/patients.py`, `backend/app/routes/identity.py`,
`backend/app/routes/compliance.py`, `backend/app/routes/batch.py`, one
shared migration, and a large NIAM identity/federation/governance/trust
surface. Full list: see this session's working notes (73 paths,
reproducible via `git diff --name-only origin/main...A` ∩ `...B`).

## 3. What a real (git-native) 3-way merge simulation shows (Phase 5, sampled)

Ran `git merge-tree --write-tree --name-only` between the two branch tips —
a safe, read-only git operation that does not touch the working tree, any
branch ref, or create any commit. Of the 73 overlapping files:

- **16 auto-merge cleanly** (git's own 3-way merge resolves them without
  conflict) — notably `backend/app/routes/patients.py`,
  `backend/app/routes/identity.py`, `backend/app/security/rbac.py`,
  `backend/app/services/mpi/scope.py`, `backend/app/services/order_service.py`,
  `backend/migrations/versions/20260815_0023_drug_substitution.py`,
  `backend/tests/test_emergency_surgery_workflow_p0.py`. This means most of
  this program's own P1 authorization fixes (Batches 6-8) sit on
  non-overlapping lines relative to Branch B's changes to the same files —
  good news for eventual reconciliation.
- **57 have real, git-detected textual conflicts** requiring semantic
  (human or carefully-scoped-agent) resolution, including
  `backend/app/lims/services.py`, `backend/app/lims/routes.py`,
  `backend/app/services/hospital_service.py`, `backend/app/routes/hospital.py`,
  `backend/app/routes/batch.py`, `backend/app/routes/compliance.py`, and
  most of the NIAM identity subsystem (adaptive_auth, admin, workspaces,
  certificates, compliance, federation, governance, lifecycle,
  notifications/routes.py, trust, workflows/routes.py), plus all of
  `nursing/*`, `pharmacy/{inventory,models,services}.py`,
  `pilot_platform`, `radiology/pacs.py`, `routes/{admin,authorization,
  canonical_patient,care_continuum,samples}.py`,
  `services/care_continuum_service.py`, and the `nhop-platform/` app tree.
- **4 are "add/add" conflicts** — both branches independently created a
  *new* file at the same path with different content:
  `backend/tests/test_canonical_patient_scope.py`,
  `backend/tests/test_care_continuum_tenant_scope.py`,
  `backend/tests/test_rbac_tenant_scope.py` (confirmed neither exists on
  `main`; Mustafa's version is 194 lines, Pharmacy's is 244 — genuinely
  different, not yet read line-by-line to classify per Phase 3/9),
  `nhop-platform/app/core/trusted_context.py`,
  `nhop-platform/tests/test_result_verification_identity.py`,
  `scripts/tenant_mass_assignment_scan.py`.

## 4. Confirmed duplicate fix (Phase 3) — LIMS/Hospital audit-role hardcoding

Both branches independently found and fixed the **exact same defect** this
program closed in Batch 8 (`user_role="lab_tech"` /
`user_role="hospital_staff"` hardcoding — see
`docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` Pattern 4):

- **LIMS** (`app/lims/services.py`): Branch A threads `user_role: str`
  (this program's Batch 8). Branch B threads `actor_role` (their own,
  differently-named parameter, referenced in their commit as part of
  NR-156's fix). Confirmed via direct content diff — same 4 call sites,
  different parameter name, same underlying correction.
- **Hospital** (`services/hospital_service.py`): same pattern — Branch A
  uses `user_role`, Branch B uses `actor_role=actor_role` (5 call sites,
  confirmed via grep).

**Neither implementation should simply overwrite the other.** Reconciling
this requires picking one parameter-naming convention and verifying the
other branch's call sites/tests still work under it — a real, if small,
piece of semantic reconciliation work, not a mechanical merge.

## 5. Confirmed one-directional security gaps (Phase 8) — must be preserved

Direct content inspection (not assumption) of Branch B's copies of the
files this program's Batches 6-8 fixed for missing-permission-check P1s
confirms **Branch B does NOT have these fixes**:

| File | Branch A (Mustafa) | Branch B (Pharmacy) |
|---|---|---|
| `routes/identity.py::link_national_id` | `require_permission("patients:write")` | still `get_current_user` only |
| `routes/patients.py` (6 routes) | `require_permission("patients:read"/"patients:write")` | still `get_current_user` only, zero `require_permission` calls |
| `routes/compliance.py` (4 FHIR routes) | `require_permission("patients:read"/"results:read")` | still `get_current_user` only |
| `routes/batch.py::create_batch_orders` | `require_permission("orders:write")` | still `get_current_user` only |

**These are real P1 authorization fixes that exist only on Branch A.** Per
Phase 8's own rule ("if one branch contains a security fix and the other
does not, the canonical baseline must preserve the security fix"), any
canonical baseline **must** carry these forward from Branch A, regardless
of which branch is chosen as the reconciliation base.

Conversely, `backend/app/security/rbac.py` (the permission matrix itself)
is **byte-identical** between the two branches — both independently made
the same tiny fix to it (confirmed via direct diff, zero output). No
conflict there.

## 6. Confirmed one-directional data-integrity/schema fixes — must be preserved

- **`backend/migrations/versions/20260815_0023_drug_substitution.py`**:
  Branch B corrected an in-place, self-aborting migration bug (two FK
  columns declared `String(26)` against an `Integer` primary key, causing
  `DatatypeMismatch` on every clean PostgreSQL database — meaning this
  migration, as it exists on `main` **and on Branch A**, has never
  successfully applied to any real database). Branch B's own justification
  for editing an already-published migration (normally forbidden by this
  program's own rules) is that no database could have applied a
  self-aborting migration, so the "never modify an existing migration"
  rule's underlying rationale doesn't apply here. Verified by direct diff:
  only the docstring and the two column type declarations changed;
  `revision`/`down_revision` unchanged. **This appears to be a real,
  narrowly-scoped, well-justified fix that Branch A is missing entirely** —
  Branch A's pharmacy drug-substitution feature is currently broken on
  fresh PostgreSQL deployments and neither this reconciliation pass nor any
  prior batch discovered it.
- **`backend/migrations/versions/20260820_0003_hospital_core_schema.py`**
  (Branch B only): creates `hospitals`, `hospital_departments`,
  `hospital_operation_theaters` — explicitly scoped as "the minimum
  dependency closure" needed to unblock `20260820_0004`'s (also Branch B
  only) surgical-safety-checklist foreign key, which itself was previously
  aborting with `UndefinedTable` on every clean database. **This directly,
  partially resolves the "Hospital schema blocker" this program has carried
  forward as BLOCKED since Batch 4** — though only for 3 of the 14 Hospital
  tables (the ones `hospital_operation_theaters`-dependent code needs,
  which includes this program's own Batch 8 OT/surgical-checklist
  audit-role fix); the other 11 tables (`beds`, `bed_assignments`,
  campuses, buildings, floors, clinics, rooms, units, equipment, cost
  centres) remain unmigrated on both branches.

## 7. Confirmed migration-head conflict — genuine STOP condition (Phase 4)

**Both branches independently created a new migration with
`down_revision = "20260908_0001"`**:

- Branch A: `20260908_0003_platform_authority_foundation.py` →
  `down_revision = "20260908_0001"`
- Branch B: `20260909_0001_pharmacy_canonical_drug_identity.py` →
  `down_revision = "20260908_0001"`

If both branches' `migrations/versions/` directories were combined
as-is, Alembic would have **two divergent migration heads** branching
from the same point — a real, material schema-history conflict, not a
hypothetical one. Per this task's own Phase 4 instruction ("If two
branches contain conflicting schema evolution: STOP THAT SPECIFIC
RECONCILIATION and report the conflict"), **this migration reconciliation
is explicitly not resolved in this pass.** Resolving it requires either an
Alembic merge revision (a new migration whose `down_revision` is the tuple
of both heads) or renumbering one chain — the latter is a migration-file
rewrite this program has never done without explicit human approval, and
the former requires deciding which of the two subsequent chains
(`20260908_0004`→`20260908_0005` on Branch A: certificate-issuer FK fix +
NIAM idempotency keys; `20260909_0001`→...→`20260916_0001` on Branch B: 8
further migrations covering pharmacy identity, organizations, citizen
relationships, governance/trust columns, claims idempotency) should be
Alembic-ordered before the other, which is itself a product decision, not
a technical one.

Branch B's other 12 unique migrations (beyond the 2 above) chain linearly
from `20260909_0001` through `20260916_0001` with no internal conflicts —
the problem is purely the fork point shared with Branch A's chain.

## 8. What this means for Phase 10 (choosing a canonical baseline)

**The evidence gathered this pass does not support choosing either branch
wholesale, and does not yet support a fully-automated file-by-file
reconciliation within this pass's effort budget.** Specifically:

- Neither branch is a superset of the other. Branch A owns this program's
  entire authorization/security-triage effort (Batches 1-8: ~10+ P1
  findings closed with full negative-proof discipline, ADR-009, the
  production readiness matrix). Branch B owns a large, independently
  rigorous LIMS/pharmacy/MPI/ORM/NIAM-schema effort with its own P0
  closures (NR-156's LIMS 500-error bug, the drug-substitution migration
  fix, partial Hospital schema unblocking) that Branch A never discovered.
- 57 of 73 overlapping files have real textual conflicts. Many span
  subsystems (NIAM identity federation/governance/trust/workflows,
  nursing, pharmacy internals, `nhop-platform/`) this reconciliation pass
  has no session history or design context for on Branch B's side —
  resolving them by guessing "ours" or "theirs" would violate this
  program's own explicit rule against exactly that shortcut.
- A genuine migration-head conflict exists and cannot be resolved without
  a human or architecture decision on migration ordering.
- At least one confirmed duplicate fix (LIMS/Hospital audit-role,
  different parameter names) and at least 3 confirmed "add/add" test-file
  conflicts need line-by-line reading before classification, not yet done
  this pass.

**Per this directive's own Phase 10 rule ("If the evidence is insufficient
to choose: STOP and ask for human decision") and its STOP conditions
("migration histories conflict materially" — confirmed; "branch choice
cannot be justified objectively" — confirmed), this pass stops here rather
than guessing a resolution for the 57-file conflict set or the migration
head conflict.**

## 9. What was NOT done this pass (explicitly, per the directive's own scope limits)

- No reconciliation branch was created.
- No commit was cherry-picked.
- No file was merged.
- No migration was written, merged, or renumbered.
- No new feature or bug-fix work was performed (per the directive's own
  "stop feature/security expansion" instruction).
- The full backend regression was **not** re-run this pass (nothing in
  the working tree changed besides this document, so Batch 8's last
  regression result — 3128 passed, 27 skipped, 2 pre-existing failures —
  still describes Branch A's current state exactly).

## 10. Recommended next action (for a human)

1. Decide, for the migration-head conflict specifically: should Branch
   A's `20260908_0003→0005` chain be renumbered to follow Branch B's
   `20260916_0001`, or vice versa, or should a formal Alembic merge
   revision be authored? This is a product/release decision, not
   something to infer from code.
2. Decide the LIMS/Hospital audit-role parameter-naming convention
   (`user_role` vs `actor_role`) once, so it can be applied consistently
   wherever the eventual merge touches either.
3. For the 57 real-conflict files: recommend a **domain-owner-by-domain**
   follow-up (NIAM identity, nursing, pharmacy, Hospital/LIMS, nhop-platform)
   rather than one more mega-pass — each domain's conflicts are
   self-contained enough (per the file list above) to review independently,
   and each needs someone who has read both sides' actual design intent,
   not just their diffs.
4. Once 1-3 are decided, a dedicated reconciliation pass can create the
   actual reconciliation branch (Phase 11) and run the full Phase 12
   verification (compile, tests, PostgreSQL LIMS journey, migration
   checks) — none of which was attempted this pass because there is
   nothing yet to verify.
