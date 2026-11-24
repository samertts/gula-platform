# P0 CONTAINMENT PLAN — PROGRAM-GULA-PARALLEL-001

**Companion to:** `POST_WAVE_B_EXECUTION_PLAN.md` (severity reassessment §2), `MASTER_REMEDIATION_REGISTER.md` §4
**Status:** PLAN ONLY — no containment action has been executed against source or Git state
**Date:** 2026-11-19

> Covers all **eight original P0 findings**. Six are confirmed P0 after reassessment;
> two (A02-001, A06-001) are downgraded to P1 but retain containment because the
> standing instruction keeps clinical-sync certification halted until A06-001 and
> A06-002 are both resolved and verified.
> Every "reproduction" below is **read-only/static** — no destructive script, DB,
> service, or production action is authorized.

---

## 1. A08-R001 — `emergency-recover.sh` destructive recovery (P0, KEPT)

- **Root cause:** A field-repair script hard-coded to a stale branch `claude/fix-bugs-vulnerabilities-Y6mGU` (absent from all 16 local/remote branches) performs `git checkout -B`, `git reset --hard`, and `git clean -fd`, with no dirty-tree guard and no explicit confirmation flag. `deploy.sh:173` tells operators to run it on merge-conflict markers, so a live execution path exists.
- **Exact affected files:**
  - `emergency-recover.sh:15-21,34,53-67,71,76,81,122-153` — **clean/tracked** (no user modifications), but must not be edited or moved without approval.
  - `deploy.sh:173` — guidance that invokes it.
  - `PROGRAM_CONTROL.md §2.2` — the 378 protected paths at risk.
- **Reproduction procedure (read-only):** `grep -nE 'TARGET_BRANCH|checkout -B|reset --hard|clean -fd' emergency-recover.sh`; `git branch -a --list '*fix-bugs-vulnerabilities*'` (empty → stale); `sed -n '170,175p' deploy.sh`. **Do not execute the script.**
- **Containment strategy (G0):** publish a written DO-NOT-RUN notice to all agents/operators; add a quarantine marker in the control docs; design (do not apply) a dirty-tree guard (`git status --porcelain` → refuse if non-empty) plus `CONFIRM_DESTRUCTIVE_RECOVERY=1` requirement and a valid branch reference; amend `deploy.sh` guidance to remove the instruction to run it. No edit/move/rename of the original file without approval.
- **Proposed permanent fix:** guarded script: refuse on non-empty porcelain, require explicit flag, verify target branch exists on remote, back up before any reset/clean, never touch `/etc/nginx` without auth. Clean file → implementer A08; approval ORCH + USER.
- **Required approval:** ORCH (quarantine) + USER (any edit to original file).
- **Regression tests:** static test asserting the script contains a non-empty-tree guard and confirmation flag; test that `deploy.sh` no longer references it as a fix; workflow lint.
- **Acceptance criteria:** the script cannot run in the current tree even if invoked; zero references instruct operators to run it; original file unchanged until approval.

---

## 2. A06-002 — Unsafe `CRDT_MERGE` in HEAD; safe fix only in user work (P0, KEPT)

- **Root cause:** committed HEAD enum `CRDT_MERGE = "crdt_merge"` implements first-seen-key-wins; it silently selects one value in a clinical conflict. The safe `CONFLICT_QUARANTINE` replacement exists only as uncommitted user work and has never been committed/verified.
- **Exact affected files:**
  - `backend/app/services/offline_sync_service.py` — ` M` (user patch; `:20-25,154-271`).
  - `backend/tests/test_offline_sync.py` — ` M` (user patch; `:193-247`).
  - `backend/tests/test_offline_conflict_synthetic.py` — `??` (user work; 11 tests).
  - HEAD baseline: `git show HEAD:...:19,176-182` (unsafe version).
- **Reproduction procedure (read-only):** `git diff -- <two files>`; `git show HEAD:backend/app/services/offline_sync_service.py | sed -n '19p;176,182p'`; static trace of the first-seen-wins loop (`if k not in merged: merged[k]=v` — first op wins). Do not run production sync.
- **Containment strategy (G0–G1):** freeze all offline-conflict changes; obtain USER release; review in isolated clone only (Appendix A of the execution plan); keep certification halted; never run `gula_offline_simulation_test.py` as evidence.
- **Proposed permanent fix:** adopt `CONFLICT_QUARANTINE` after adding R1 (receive-replay) and R2 (concurrency) regression tests; decide R3 metadata namespace; scope R4 durability; add a documented enum migration note for R5.
- **Required approval:** USER (release) + CLIN (clinical semantics) + SEC + ORCH.
- **Regression tests:** the 31 designed tests (`TEST_BASELINE_PLAN.md §3`) + new: resolve→replay incoming op single audit row; concurrent resolution single audit row; metadata-key collision; restart/durability scope assertion.
- **Acceptance criteria:** no contested clinical value auto-selected; idempotent across replay and concurrency; all tests green with machine-readable artifacts; certification gate unblocked only after A06-001 also resolved.

---

## 3. A05-001 — No critical-result delivery/acknowledgement path (P0, KEPT)

- **Root cause:** `lims/workflows.py` deliberately refuses to claim delivery and writes a durable outbox event (`delivery_status: pending_dispatch`, `delivery_recipient: None`, `escalation_policy: NOT_CONFIGURED`, `acknowledgement_status: NOT_CONFIGURED`); `routes.py:2213-2229` commits only the event. No recipient policy, escalation, delivery worker, or acknowledgement path exists.
- **Exact affected files:** `backend/app/lims/workflows.py:227-318` (` M` — USER), `backend/app/lims/routes.py:2213-2229` (clean), `backend/tests/unit/test_lims_critical_result_outbox.py:63-70` (test pins honest state). Production mounting: `factory.py:689-690`.
- **Reproduction procedure (read-only):** read the cited lines; inspect the test asserting `notification_pending` / `clinician_notified is False`. No live result generation.
- **Containment strategy:** keep the honest state (do not fabricate "alerted"); add an explicit operator-visible banner that critical-result delivery is not configured; freeze clinical certification for this dimension.
- **Proposed permanent fix:** define recipient/escalation/ack policy (clinical decision), then add a delivery worker/adapter with fail-closed escalation and durable audit; route outcome becomes `delivered`/`acknowledged` only on real confirmation.
- **Required approval:** CLIN (policy + semantics) + DB-API (outbox/audit schema) + A07/A09.
- **Regression tests:** unit tests for no-recipient fail-closed; delivery worker success/failure/retry; ack immutability; route never reports `clinician_notified=True` without a real adapter result.
- **Acceptance criteria:** every detected critical result has a configured recipient or an explicit fail-closed incident; no false delivery claim; audit trail complete.

---

## 4. A05-002 — Auto-validation omits QC gate (P0, KEPT)

- **Root cause:** `lims/workflows.py:32-41` documents five checks including a fail-closed QC gate, but the implementation (`:61-166`) has no QC branch; `services.py:252-259` omits four documented context inputs; `routes.py:1346-1349` release accepts `auto_validated`; production route `:2145-2183` sets `validation_status = "auto_validated"` without QC evidence.
- **Exact affected files:** `backend/app/lims/workflows.py` (` M` USER), `backend/app/lims/services.py` (clean), `backend/app/lims/routes.py:1346-1349,2145-2183` (clean).
- **Reproduction procedure (read-only):** compare documented check list at `:32-41` with implementation `:61-166`; inspect caller args at `services.py:252-259` and `routes.py:2158-2166`. Do not auto-validate live results.
- **Containment strategy:** prevent release eligibility of `auto_validated` results until QC evidence exists (design only, no source change); keep clinical certification halted.
- **Proposed permanent fix:** implement fail-closed QC gate with patient/delta context; block release path when QC evidence absent; add immutable audit of gate decision.
- **Required approval:** CLIN + DB-API.
- **Regression tests:** QC-pass, QC-fail, QC-missing, context-missing cases; release-path negative test; audit-record assertion.
- **Acceptance criteria:** no result released as auto-validated without passing QC evidence; all documented checks executed or explicitly waived by an authorized human.

---

## 5. A05-007 — FHIR `transaction` bundles not atomic (P0, KEPT)

- **Root cause:** `POST /fhir` accepts `batch` and `transaction` but processes both identically: per-entry loop (`:1446-1497`), per-entry `HTTPException` caught and converted to a status (`:1498-1499`), then a single `db.commit()` (`:1505-1507`) with no rollback, savepoint, pre-validation, or all-or-nothing gate. Earlier writes survive a later failure.
- **Exact affected files:** `backend/app/routes/ehr_fhir.py:1437-1507` (clean/tracked; production `feature_routes` via `factory.py:570`), `backend/tests/test_fhir_comprehensive.py:115-133` (only empty-batch and unsupported-type tests).
- **Reproduction procedure (read-only/static):** trace the loop and the single commit; note the absence of `rollback()`; confirm tests never exercise a failing transaction entry. **No live FHIR writes.**
- **Containment strategy:** document `POST /fhir` transaction semantics as **UNVERIFIED / NOT ATOMIC**; freeze changes to this route pending approval; no production transaction bundles in any test.
- **Proposed permanent fix:** distinguish `batch` (per-entry commit allowed) from `transaction` (all-or-nothing): pre-validate entries, execute in one DB transaction with rollback on any failure, return proper transaction response; add version-aware error contract.
- **Required approval:** CLIN (interop semantics) + DB-API + A07 + A09.
- **Regression tests:** failure-injection at entry 2/3 asserting zero committed writes; success case; mixed batch/transaction; error-contract assertions.
- **Acceptance criteria:** a failing transaction entry leaves the database unchanged; tests prove rollback with machine-readable artifacts.

---

## 6. A03-003 — Pharmacy substitution same-click request + approval (P0, KEPT)

- **Root cause:** `PharmacyPosPanel.tsx:52-70` mutation function calls `pharmacyApi.createSubstitutionRequest(...)` then immediately `approveSubstitution(request.id)`; `:59` hardcodes a reason; `:158` renders one button (`طلب واعتماد`). There is no distinct approval step, approver identity, or independent authorization. Consent checkbox only gates some candidates.
- **Exact affected files:** `frontend-v3/src/pages/pharmacy/PharmacyPosPanel.tsx:52-70,158` (page-local), `frontend-v3/src/api/endpoints.ts:1759-1760` (real endpoints), `frontend-v3/src/routes/index.tsx:222-223` (admin/readonly exposure).
- **Reproduction procedure (read-only):** read the cited lines; trace both API calls in `endpoints.ts`; confirm route exposure. Do not invoke the API.
- **Containment strategy:** UI-boundary halt only — mark the action as requiring human approval; do not call the approve endpoint from the client flow until separated; freeze page changes pending CLIN + SEC approval.
- **Proposed permanent fix:** two-step flow — authenticated request creation, then a separate approval action with approver identity, reason, and server-side authorization; remove hardcoded reason; add audit of both steps; restrict roles appropriately.
- **Required approval:** CLIN + SEC + DB-API (contract) + A03 implementer.
- **Regression tests:** component test proving no approval call on request click; server auth test rejecting self-approval; audit test recording both steps; role matrix test.
- **Acceptance criteria:** no substitution can be requested and approved by one client mutation; approver identity and reason are server-validated and audited.

---

## 7. A06-001 — Offline sync simulation fakes success (P1 after downgrade; certification gate retained)

- **Root cause:** `gula_offline_simulation_test.py:59-83` opens only the local SQLite DB, recomputes a local SHA-256, and sets `status='SYNCED'` with the comment "Simulate successful sync"; `:101-102` prints "[VERIFICATION PASSED] 100% data integrity". No server, transport, acknowledgement, conflict handling, or idempotency. The guide (`gula_offline_simulation_guide.md:24-34`) presents it as a pre-disaster operational test with `0% data loss` criteria. No CI reference exists.
- **Exact affected files:** `gula_offline_simulation_test.py` (clean), `gula_offline_simulation_guide.md` (clean), `config/quality-gates/offline-gate.py` (clean).
- **Reproduction procedure (read-only):** read `:59-83,101-102`; `grep -rn 'gula_offline_simulation_test\|offline-gate' .github/workflows` → no matches. Do not run the script as verification.
- **Containment strategy:** relabel as **demo/UI aid only**; mark all "100% integrity / 0% loss" claims UNVERIFIED; remove from field-use guidance; keep clinical-sync certification halted per standing instruction.
- **Proposed permanent fix:** build an isolated harness with a disposable server/DB; exercise real reconnect, acknowledgement, conflict, retry, and idempotency; emit machine-readable artifacts; rewrite guide success criteria.
- **Required approval:** ORCH + CLIN + A09 (QA design); no new paid dependency.
- **Regression tests:** server-backed reconnect suite; negative tests for lost acknowledgement and duplicate delivery; artifact emission assertions.
- **Acceptance criteria:** no "sync verified" claim without a real server round-trip and artifacts; certification remains halted until resolved **and** verified.

---

## 8. A02-001 — Split token architecture (P1 after downgrade; not a patient-safety P0)

- **Root cause:** two CSS entry files define two token vocabularies. `main.tsx:4` imports only `src/styles/index.css` (shadcn vocabulary); the dead `src/index.css` defines `bg-surface`/`border-outline`/`text-on-surface*`. Tailwind v4 generates utilities from the imported theme, so the Material-3 classes used by `Modal.tsx:37,42-44`, `EmptyState.tsx:17-21`, and `Skeleton.tsx:4,25` produce **no CSS** — overlays/loading/empty states render unstyled.
- **Exact affected files:** `frontend-v3/src/main.tsx:4`, `frontend-v3/src/styles/index.css:5-42` (active), `frontend-v3/src/index.css:8-54` (dead), and the three consumer components. All clean/tracked.
- **Reproduction procedure (read-only):** `grep -c 'bg-surface\|border-outline\|text-on-surface' frontend-v3/src/styles/index.css` → 0; same on `src/index.css` → 4; `grep -rn` the three components → consumers found. Visual check only; no patient data involved.
- **Containment strategy:** lower to P1; no P0 halt; bundle with A02 batch 1 and A03 page-level coordination; do not let it block clinical-sync certification.
- **Proposed permanent fix:** preferred — add semantic aliases for the missing utilities to the active `@theme inline` block (single-file, lower risk); alternative — migrate the four components to the shadcn vocabulary. Then delete/gate the dead stylesheet (A02-018).
- **Required approval:** design/visual review + A03 coordination; no CLIN/SEC/DB-API gate.
- **Regression tests:** assertion that every shipped utility class resolves to generated CSS; visual snapshots for Modal/EmptyState/Skeleton; build succeeds.
- **Acceptance criteria:** no shipped component references a non-generated utility; rendered surfaces have intended background/border/text; no flash of unstyled content.

---

## 9. Cross-cutting containment rules

1. No finding is marked Fixed or Verified until tests execute with artifacts (`TEST_BASELINE_PLAN.md`).
2. P0-related files are frozen: no edit by any agent until the owning approvals in `APPROVAL_MATRIX.md` are recorded.
3. The two downgraded findings still have named containment owners and acceptance criteria; downgrade ≠ abandonment.
4. Clinical synchronization certification stays **HALTED** until A06-001 **and** A06-002 are resolved and verified.
5. `emergency-recover.sh` remains DO-NOT-RUN; its original bytes and permissions are unchanged.
6. All reproduction procedures above are read-only; any step that would touch source, Git state, DB, or production is explicitly out of scope.
