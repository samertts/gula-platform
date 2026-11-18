# Integration Testing & Verification Record

**Document:** 13 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `IMPLEMENTED` (strategy); evidence rows carry their own statuses.
**Phase B addendum:** §6 below records the synthetic engineering tranche executed after the Phase A commit. Phase A rows are retained unchanged as historical evidence.

---

## 1. Gate ladder (mandatory order)

| Level | Command / method | Pass criterion | Current result |
|---|---|---|---|
| L0 focused | pytest on changed module tests only | 0 failed, 0 skipped-added | PASS for Phase B artifacts — 31/31 validator, 14/14 NR-011 |
| L1 workstream | all tests owned by the WS | 0 failed | 773 baseline green |
| L2 full regression | `pytest tests/health_core -q --tb=short` | **≥ 773 passed**, 0 failed, 0 skipped | **773 passed, 1 warning** (re-executed with complete toolchain, 13.41 s) |
| L3 contract | OpenAPI/schema diff before vs after for route changes | byte-stable or documented correction | no route changes in Phase A |
| L4 static | Ruff + MyPy on changed scope | 0 new violations | **PASS** — ruff clean; mypy 0 issues in 75 files (complete toolchain restored) |
| L5 preservation | HEADs, protected md5s, 0 deletions, no protected-repo writes | all PASS | PASS (see `01`) |
| L6 adversarial | independent reviewer with no file ownership | verdict PASS | **PASS** — round 2 independent review (see `ADVERSARIAL_REVIEW_RECORD.md`) |

### 2.1 Phase B engineering evidence (this program)

| Artifact | Focused verification | Status |
|---|---|---|
| `scripts/national_integration_verify.py` + `backend/tests/unit/test_national_integration_registry.py` | **31 passed / 0 failed** — integrity gate for the machine-readable registry (docs, vocabulary, md5s, HEAD format, production-ready invariant, CLI exit codes) | `TESTED` |
| NR-011 prerequisite engineering (pre-existing uncommitted work, now verified) | `test_nr011_metadata_discovery.py` **14 passed**; disposable PG `gula_nr011_verify`: `alembic upgrade head` exit 0; `alembic check` 0 metadata aborts, 284 documented unmigrated-table diffs | `TESTED` |

Disposable-DB commands are reproducible with `DATABASE_URL=postgresql://postgres:***@172.18.0.2:5432/gula_nr011_verify` against the local container; the database is dropped after evidence capture. No operational DB, no DDL outside the disposable clone.

## 2. Reproducible commands

```bash
# Re-established toolchain (environment recovery)
# Complete toolchain: Python 3.12.13, pytest 9.1.1, ruff 0.16.0,
# mypy 2.3.0, alembic 1.18.5, signxml present.
VENV=/home/samertts/workspace/projects/gula-platform/backend/.venv/bin

# Full Health Core gate
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  $VENV/python -m pytest tests/health_core -q --tb=short
# → 773 passed, 1 warning in 13.41s  [exit=0]

# Full-suite collection (regression of the signxml environment gap)
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  $VENV/python -m pytest tests/ --collect-only -q
# → 4675 tests collected in 22.55s  [0 errors]
```

## 3. Evidence integrity rules

1. Every recorded number must come from an executed command in this or a cited prior-cycle record.
2. Skipped, xfailed, unimplemented and demo-only checks are **never** counted as passed.
3. A test may not be deleted or weakened to obtain a pass; new strictness is allowed.
4. Synthetic fixtures only; no real patient data, no national identifiers, no production connection.
5. Any toolchain substitution must be disclosed with version parity evidence (`01` §2).

## 4. Adversarial review protocol (Phase D)

- Reviewer must not have authored any file in the change set.
- Review dimensions: correctness, security, contract stability, test integrity, governance traceability, honesty of status labels.
- Findings are recorded with severity, owner, evidence and disposition; no finding is silently closed.
- A workstream may be marked `INDEPENDENTLY VERIFIED` only after a PASS verdict.

## 5. Current verification verdict

| Area | Status |
|---|---|
| Phase A baseline | `TESTED` (self-executed; 773 count independently re-run — see review record) |
| Ruff / MyPy (current phase) | `TESTED` — complete toolchain restored |
| Registry integrity gate | `TESTED` — focused tests (all negative cases included) |
| NR-011 prerequisite engineering | `TESTED` — 14 regressions + disposable-PG proof |
| Protected md5s / repository HEADs | `INDEPENDENTLY VERIFIED` — independently re-checked by the reviewer |
| Preservation 24/24 gate | `TESTED` (carried prior-cycle evidence) |
| Workstreams C and E | `NOT IMPLEMENTED` |
| Phase D (adversarial review) | `INDEPENDENTLY VERIFIED` — round 1 FAIL → all 8 findings fixed → round 2 independent PASS |
| Phase A change set (as scoped in the review record) | `INDEPENDENTLY VERIFIED` — engineering-evidence verdict only; HOLD/REJECT unchanged, no release claim |

**No production, clinical, security-certified or release verdict is implied by this document.**

---

## 6. Phase B addendum — synthetic engineering tranche

All commands below were executed on branch `integration/gula-unification-v1` with the
complete Python 3.12 toolchain from `gula-platform/backend/.venv`. Phase A HEAD
`0cb067ae` is the recorded baseline; the program is authorized to advance the
integration branch by local reviewed commits only.

### 6.1 Deterministic gate (`scripts/phase_b_gate.py`)

| Check | Command / criterion | Result |
|---|---|---|
| preservation | protected md5s; platform HEAD pinned to `f478676b`; integration branch `integration/gula-unification-v1`; 0 tracked deletions | **PASS** |
| registry | `national_integration_verify.py` integrity gate | **PASS** — 0 errors / 0 warnings |
| focused | six Phase B focused suites | **PASS — 235 tests** (registry 31, NR-011 14, T1 106, T3 19, T5 14, T6 51) |
| static | Ruff on all Phase B targets | **PASS** — 0 findings |
| types | MyPy on `app/health_core` | **PASS** — 0 new errors; 2 documented pre-existing `order_state.py:63,81` tolerated |
| regression | `pytest tests/health_core` | **PASS — 773 passed, 1 warning**, 0 failed (baseline preserved) |

Reproduce: `python scripts/phase_b_gate.py` (exit 0; `--json` for full command traces).

### 6.2 Task evidence (Program Director task IDs — see registry disambiguation note)

| Task | Artifact | Focused result | Status | Boundary |
|---|---|---|---|---|
| T1 | `app/health_core/terminology/checkdigit.py` | 106 + 103 contract/provenance | `TESTED` | Official Appendix C.1 Mod-10; C.2 letter-prefixed fail closed; licensed release dataset `BLOCKED` |
| T3 | `app/health_core/reliability/durable_queue.py` | 19 | `TESTED` | Synthetic in-process queue; no runtime wiring |
| T5 | `app/health_core/audit_anchor/` | 14 | `TESTED` | Local JSONL hash chain; durable external anchor `NOT IMPLEMENTED` |
| T6 | `app/interoperability/fhir_http/` | 51 | `TESTED` | Non-activated; relocated out of Health Core to preserve the WS-E guard; external validation `BLOCKED` |
| DB | `PHASEB_DB_ALEMBIC_DIFF_CLASSIFICATION.md` | live disposable PG: `upgrade head` 0, `check` 255, 284 add_table, 0 aborts | `BLOCKED` | Classification only; ADR-A owner-gated; 1364 destructive-looking ops never auto-applied |

Evidence index: `GOVERNANCE/PHASE_B_EVIDENCE/` (five reports).

### 6.3 Broader regression and disclosed pre-existing failure

- Full-suite collection: **4865 tests collected, 0 errors** (Phase A 4675 + 190 new Phase B tests).
- Broad deterministic selection (`unit contracts security identity kernel kernel_hardening health_core`):
  **1654 passed, 4 skipped, 1 failed**.
- The single failure is `test_nr011_metadata_discovery.py::TestMetadataDiscovery::test_cross_metadata_foreign_keys_resolve`
  (`NoReferencedTableError: niam_adaptive_mfa_sessions.session_id -> niam_user_sessions.id`).
  It is **pre-existing and out of Phase B scope**: it reproduces only when `tests/identity` is
  co-collected (a global SQLAlchemy metadata interaction), passes in isolation and in the
  focused gate, and involves no Phase B file. It is disclosed here rather than suppressed.
- Database-backed integration execution is `BLOCKED` in this environment (no reachable
  PostgreSQL); the disposable-DB evidence above is the authorized substitute.

### 6.4 Independent review and status boundary

Independent read-only review (session `ses_e0ff9c922fferm5xYuovZPWVX4`, no file
ownership) returned **PASS with zero findings**: all six gates and the 235 focused
tests re-run, source-level correctness/security review, documentation honesty
cross-check, and reproduction of the disclosed pre-existing NR-011 broad-suite
failure. Recorded in `ADVERSARIAL_REVIEW_RECORD.md`.

The Phase B change set is therefore `INDEPENDENTLY VERIFIED` **within that review
scope only** — an independent engineering-evidence verdict. It is **not**
`PRODUCTION READY`. HOLD, MPI REJECT and all owner-gated decisions are unchanged;
no route was activated; no production or external system was contacted.
