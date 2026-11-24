# TEST BASELINE PLAN — PROGRAM-GULA-PARALLEL-001

**Status:** PLAN ONLY — **0 tests executed this session · 0 machine-readable artifacts produced**
**Date:** 2026-11-19
**Related:** `MASTER_REMEDIATION_REGISTER.md §11` (no gate baseline), A09 `QA_AUDIT.md`

> Establish a reproducible, honest test baseline **without** destructive tests, database
> migrations, service starts, or production operations. Historical pass/fail numbers
> (including "31 tests, 31/0", "407/833 tables", "119 migration failures") are
> **CLAIM — UNVERIFIED** until they are reproduced with artifacts in an approved isolated
> environment. Do not claim the CONFLICT_QUARANTINE patch is verified.

---

## 1. Current evidence state

| Property | Verified value | Source |
|---|---|---|
| Backend `test_*.py` files | 335 (219 tracked, 116 untracked USER) | A09, read-only count |
| AST-parsed test functions | 4,379 | A09 |
| Frontend unit test files / cases | 15 / 54 | A09 |
| Playwright specs / declarations | 12 / 22 | A09 |
| Machine-readable result artifacts (XML/log) | **0** | A09, repo-wide search |
| Tests executed in this program | **0** | Orchestrator log |
| Patch verification | **NOT VERIFIED** | This document |

Note: `backend/.pytest_cache/v/cache/nodeids` shows a **past collection** (including stale `test_crdt_merge`) but contains no pass/fail outcomes — collection is not execution. `security-audit/bandit.json` holds a stale source excerpt, not a result for the current patch.

---

## 2. Environment capability (read-only probes, this session)

| Component | Status |
|---|---|
| Python | 3.10.12 ✅ |
| pytest | 9.1.1 ✅ |
| cryptography (needed by `EncryptedSyncStore` tests) | 49.0.0 ✅ |
| Test config | `backend/pytest.ini`, `backend/pyproject.toml`, `backend/tests/conftest.py` exist ✅ |
| Isolated clone | `/tmp/opencode/gula-isolation-eval` @ `2206654d`, clean (0 changes) ✅ |
| `node_modules` in clone | absent (frontend gates not executable there without install) ⚠️ |
| Patch present in clone | **No** — clone has HEAD's unsafe `CRDT_MERGE` ❌ |

**Conclusion:** the toolchain is capable; the **only blocker** to executing the patch tests is that the patch is uncommitted protected user work. Replicating it into the clone requires the USER release + ORCH authorization in `ISOLATION_OPTIONS.md Option D` (or a user-created commit, Option E). That authorization has **not** been granted, so no test was executed.

---

## 3. Designed test suite for CONFLICT_QUARANTINE (31 tests, 0 executed)

### 3.1 `backend/tests/test_offline_sync.py` — 20 tests (14 engine + 6 store)
Existing 19 tests (create/receive/signatures/pending/mark-synced/clear/vector clocks/LWW/conflict detection/log/duplicate/causal/vector increment + 6 store tests) plus the patched test:
- `test_conflict_quarantine_preserves_both_versions` — asserts `_resolution_status == CONFLICT_QUARANTINED`, both `"Ali"/"Ahmed"` retained, `phone`/`email` non-contested keys merged, contested `"name"` absent from projection, replay returns identical result, exactly one `conflict_resolved` audit row.

### 3.2 `backend/tests/test_offline_conflict_synthetic.py` — 11 tests (untracked USER work)
- `test_clinical_value_never_silently_overwritten` — POSITIVE/NEGATIVE retained; later timestamp (9999) does not win; provenance kept.
- `test_agreed_values_merge_without_quarantine` — `MERGED`, no `_conflicts`.
- `test_out_of_order_arrival_retains_same_versions` — retained value set independent of arrival order (explicitly **not** CRDT convergence).
- `test_two_node_sync_and_reconnect_with_conflict` — reconciler quarantines both writes.
- `test_multi_node_no_data_loss` — every distinct value survives in projection or conflict record.
- `test_duplicate_event_and_business_key_no_false_conflict` — exact replay returns same object, no conflict.
- `test_idempotent_resolution_and_single_audit_row` — 3 replays identical, one audit row, correct op IDs and timestamp.
- `test_manual_resolution_remains_available_and_deterministic` — MANUAL path unchanged and replay-stable.
- `test_invalid_signature_is_rejected` — tampered signature → FAILED.
- `test_replay_based_recovery_rebuilds_state` — logical replay recovery; explicitly excludes crash durability.
- `test_no_crdt_enum_value_remains` — no `crdt` value in `ConflictResolution`.

### 3.3 Required additional tests (not yet written — gaps found in review)
| ID | Test | Purpose |
|---|---|---|
| T-R1 | resolve → replay **incoming op** via `receive_operation` → assert resolution unchanged and one audit row | Closes the receive-layer reset gap (Appendix A R1) |
| T-R2 | concurrent `resolve_conflict` from N threads → one audit row | Closes the concurrency gap (R2) |
| T-R3 | op data containing keys `_conflicts`/`_resolution_status`/`_message` → no metadata overwrite | Closes namespace collision (R3) |
| T-R4 | restart/new-engine replay scope assertion | Documents that durability is **not** provided (R4) |
| T-R5 | enum value `"crdt_merge"` external/persisted string handling decision | Backward-compatibility gate (R5) |

**Total designed: 31 + 5 = 36 tests. Executed: 0.**

---

## 4. Baseline establishment procedure (once authorized)

1. **Prepare clone:** verify `/tmp/opencode/gula-isolation-eval` clean at `2206654d`, or use the user's Option E commit. Record `git status --porcelain` and `rev-parse HEAD`.
2. **Replicate patch (Option D only, after release):** apply the exact captured diff to the two tracked files; copy the untracked companion test. Record SHA-256 of each replicated file. Record SHA-256 of the protected originals before and after to prove no change.
3. **Committed baseline (Option B):** from untouched HEAD clone, run the narrow unit targets to record pre-patch behavior. This does **not** verify the patch.
4. **Patch suite (Option D/E):** run only the two offline test files with verbose JUnit XML + stdout log:
   - `cd <clone>/backend && python3 -m pytest -q tests/test_offline_sync.py tests/test_offline_conflict_synthetic.py --junitxml=<clone>/artifacts/offline.xml 2>&1 | tee <clone>/artifacts/offline.log`
   - No `-k` filters that hide failures; no `--passWithNoTests`; record exit code.
5. **Gap tests:** add T-R1…T-R5 inside the clone, re-run, record artifacts.
6. **Static gates only:** `python3 -m compileall` on the two files; `git diff --check`; no DB/service commands.
7. **Protected-tree proof:** re-hash the 378 protected paths' `git status --porcelain` and compare to the Phase 0 snapshot; confirm byte-identical.

**Prohibited at every step:** DB connections/migrations, `alembic upgrade`, service start, `pytest` targets that require a live DB or external service, production deploy, any write to the protected working tree.

---

## 5. Gate catalogue (discovered, not assumed)

| Gate | Command (package-local) | Evidence required | Status |
|---|---|---|---|
| Offline unit suite | `python3 -m pytest ... --junitxml=...` | XML + log + exit code | NOT RUN |
| Frontend typecheck | `frontend-v3/: pnpm typecheck` | log + exit code | NOT RUN (no node_modules in clone) |
| Frontend unit | `pnpm test` | XML + log | NOT RUN |
| Unification/contracts/boundary | `pnpm verify:unification`, `verify:contracts`, `verify:integration-boundary` | logs | NOT RUN |
| Data sources/route/audit artifacts | `pnpm generate:data-source-inventory`, `verify:data-sources`, `generate:route-gate`, `verify:audit-artifacts` | generated artifacts | NOT RUN |
| Build/bundle | `pnpm build`, `pnpm check:bundle` | logs | NOT RUN |
| E2E | `pnpm test:e2e` | report | NOT RUN (browser deps absent in clone) |
| Aggregate | `pnpm check` | log | NOT RUN |
| Backend suite | `pytest` (335 files) | XML + log | NOT RUN |
| Backend CI | `make ci` | log | NOT RUN |
| Migration graph | static integrity check only | report | NOT RUN (no DB execution) |

Note: the discovered `check` script uses `pnpm` while CI uses `npm` (DEDUP-01/A08-009) — resolve with A08 before relying on aggregate results.

---

## 6. Acceptance criteria for a valid baseline

1. Every gate run records: command, working directory, exit code, key output, pass/fail/blocked, artifact path.
2. Zero artifacts originate from the protected working tree.
3. Patch verification requires **all 36 designed tests green** with XML artifacts in the isolated clone; otherwise the patch stays **NOT VERIFIED**.
4. Clinical synchronization certification remains **HALTED** until A06-001 and A06-002 are both resolved and verified — a green offline unit suite alone is insufficient (A06-001 needs a real server-backed harness).
5. No historical count is promoted to "verified" without an artifact from this program.

---

## 7. Decision required

Authorize (a) the isolation option in `ISOLATION_OPTIONS.md`, (b) execution of the 36 designed tests in the isolated clone only, and (c) confirmation that no DB/service/production operation is in scope. Without these, the patch remains unverified and no baseline exists.
