# Test Evidence Index — Adversarial Assurance Cycle

**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Interpreter:** `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12)
**CLI:** `/home/samertts/.local/bin/uv` (0.11.26)
**Data:** synthetic only. No operational DB, no network install, no deployment.

This index records reproducible commands and their **observed** results. It does not
claim status beyond what was actually executed. `INDEPENDENTLY VERIFIED` is recorded
only in `INDEPENDENT_VERIFICATION_TEAM_C.md` and the Phase A/B review record.

---

## 1. Authoritative gate

| # | Command (from `gula-integration/`) | Observed result | Status |
|---|---|---|---|
| G1 | `python scripts/phase_b_gate.py` | **exit 0** — 6/6 PASS: preservation, registry, focused 6/6, static (Ruff), types (0 new MyPy errors, 2 documented baseline), regression **773 passed / 1 warning in 6.05 s** | `TESTED` |
| G2 | `python scripts/national_integration_verify.py` | **VERDICT: PASS** — one advisory WARN (integration HEAD moved `0cb067ae` → `2206654d` since the Phase A baseline; expected after the Phase B commit) | `TESTED` |

## 2. Static / integrity checks (all re-run against the final working tree)

| # | Command | Observed result |
|---|---|---|
| S1 | `ruff check` on all 10 remediation source/test files | **All checks passed!** (exit 0) |
| S2 | `uv lock --check` (from `backend/`) | **PASS** — `Resolved 66 packages`, no drift |
| S3 | `uv export --frozen --no-hashes --format requirements-txt --no-emit-project -o /tmp/opencode/gula-uv-requirements.txt` | **PASS** — 144-line export; all 7 corrected pins present |
| S4 | YAML parse of `.github/workflows/security-hardening.yml` + `.github/dependabot.yml` | **PASS** — new job `python-uv-lock-consistency` and `uv` ecosystem entry present |
| S5 | `md5sum` of the three protected governance records | `effdfeaf10234678d83b2668c4489552`, `1a02c01563c93b07a7cdb92c0462bf36`, `ea3969d09aaf7b0b28a065838b44a594` — all match baseline |
| S6 | `git rev-parse HEAD` (integration / platform) | `2206654d…` / `f478676b…` — both intact |
| S7 | `git diff --cached --name-status \| wc -l` | **20** — the pre-existing `R100` renames, all under `archive/legacy/workflow_runtime/`; no staged change outside them |
| S8 | JSON parse + count of `FINDINGS_REGISTER.json` / `REMEDIATION_REGISTER.json` / `status_registry.json` | **PASS** — 81 findings, 4 remediations, registry validates |

## 3. Targeted remediation tests

All commands run from `backend/` with `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`.

| # | Target | Tests | Observed result |
|---|---|---|---|
| T1 | `pytest tests/unit/test_fk_target_integrity.py -q` | FK-target integrity (NR-011) | **5 passed** (collect-only confirmed 5 tests; Team C re-run `5 passed` `EXIT_CODE=0`). An earlier note of 6 was inaccurate — corrected. |
| T2 | `pytest tests/unit/test_lims_critical_result_outbox.py -q` | `AUD-CLIN-001` durable outbox + honest status | **4 passed** (Team C re-run `EXIT_CODE=0`, 83.42 s) |
| T3 | `pytest tests/unit/test_mpi_unverified_nid_gate.py tests/test_mpi_audit0416_integrity.py -q` | `AUD-MPI-001` unverified-NID gate + AUD-04 idempotency | **13 passed** (4 new + 9 existing; Team C re-run `EXIT_CODE=0`, 80.18 s) |
| T4 | `ruff check` on the 10 changed files | static | clean (see S1) |
| T5 | NR-011 original co-collection: `pytest tests/unit/test_nr011_metadata_discovery.py tests/identity -q` | forced merge-layer reproduction | **185 passed, 4 pre-existing skips** (Team C, `EXIT_CODE=0`); `test_cross_metadata_foreign_keys_resolve` ran and passed |
| T6 | Forced FK walk on real Alembic merged metadata (Team C probe) | 1174 FKs | **zero `NoReferencedTableError`**; `niam_adaptive_mfa_sessions.session_id -> ['niam_sessions.id'] resolves: True` |

## 4. Dependency pin verification

Seven transitive pins in `backend/uv.lock` after regeneration with `uv 0.11.26`:

| Package | Floor (`pyproject.toml` / `requirements.txt`) | Locked version | Result |
|---|---|---|---|
| certifi | ≥2026.10.18 | 2026.10.23 | PASS |
| dnspython | ≥2.9.2 | 2.9.2 | PASS |
| idna | ≥3.20 | 3.20 | PASS |
| joserfc | ≥1.8.0 | 1.8.0 | PASS |
| pillow / Pillow | ≥13.0.0 | 13.0.0 | PASS |
| pyasn1 | ≥0.6.5 | 0.6.5 | PASS |
| urllib3 | ≥2.8.0 | 2.8.0 | PASS |

## 5. Prior-cycle independent evidence (retained, not re-awarded)

| Evidence | Source | Result |
|---|---|---|
| Phase A round 2: registry 31, NR-011 14, health_core 773, collection 4675, validator PASS | `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md` | `INDEPENDENTLY VERIFIED` within that scope |
| Phase B: gate 6/6, focused 235, terminology 103, collection 4865, health_core 773, zero findings | same record | `INDEPENDENTLY VERIFIED` within that scope |
| NR-011 co-collection failure reproduced (now resolved locally — see §6) | same record | Historical disclosure retained |

## 6. NR-011 co-collection failure — resolution evidence

| Step | Result |
|---|---|
| Prior disclosed failure | `NoReferencedTableError: niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id` when `tests/identity` co-collected (Phase B independent review reproduced: **1 failed, 1658 deselected**) |
| Fix | `session_id` FK → `niam_sessions.id`; `IdentityAuthorityRecord` ORM mirror added + registered |
| Targeted regression | `tests/unit/test_fk_target_integrity.py` — **5 passed** (corrected from an earlier inaccurate note of 6) |
| Final broad regression on complete tree | See §7 below |

## 7. Full broad regression

Command (from `backend/`):
```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
  -m pytest tests/ -q --tb=short
```

**Observed result:** **`4851 passed, 27 skipped, 202 warnings in 543.64s (0:09:03)`, 0 failed.** Run against the complete final working tree (including the pre-existing uncommitted surface). The previously disclosed NR-011 co-collection failure (`test_cross_metadata_foreign_keys_resolve`) is **resolved** — the full `tests/` tree now collects and runs with zero failures. Warnings are pre-existing deprecations (`datetime.utcnow()`, Starlette TestClient, SQLAlchemy SQLite adapter, joserfc test key size) and were not suppressed.

Reference points: `1416 passed / 4 skipped` (after FK fix, before CLIN/MPI/uv changes) and `4865 collected, 0 errors` (Phase B). The final count reflects the additional auditor/remediation tests on the tree. No test was deleted or weakened to obtain this result.

---

## 8. Phase 1 — Critical security / API / architecture remediation (2026-11-19)

Environment for every command below: `backend/`, `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`,
interpreter `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python`.

### 8.1 Targeted adversarial suites

| # | Finding | Command (target file) | Observed result |
|---|---|---|---|
| T7 | AUD-SEC-001 | `pytest tests/unit/test_aud_sec_001_control_plane_authorization.py -q` | **14 passed** |
| T8 | AUD-SEC-002 | `pytest tests/unit/test_aud_sec_002_account_domain.py -q` | **18 passed** |
| T9 | AUD-SEC-003 | `pytest tests/unit/test_aud_sec_003_staged_privileged_login.py -q` | **13 passed** |
| T10 | AUD-API-002 | `pytest tests/unit/test_aud_api_002_oauth2_token_usable.py -q` | **6 passed** |
| T11 | AUD-ARCH-003 | `pytest tests/health_core/test_authorization_synthetic_scope.py -q` | **7 passed** |

### 8.2 Backward-compatibility neighbor suites

| # | Scope | Observed result |
|---|---|---|
| T12 | AUD-SEC-001 neighbors (NIAM registry authorization, security-audit phase 9, professional registry, control-plane authorization, governance anonymous/audit) | **83 passed** |
| T13 | AUD-SEC-002 neighbors (auth/security suites) | **95 passed** |
| T14 | AUD-SEC-003 neighbors (login/MFA suites) | **44 passed** |
| T15 | AUD-API-002 neighbors (`test_auth_infrastructure.py`, `test_dependency_upgrade_compat.py`, `test_security.py`) | **103 passed** |
| T16 | AUD-ARCH-003 neighbors (`tests/health_core/`, `tests/test_domain_platform.py`, `identity/test_authorization_phase8.py`) | **870 passed** |

### 8.3 Static and authoritative gates

| # | Command | Observed result |
|---|---|---|
| S9 | `ruff check` on all 16 Phase 1 source/test files | **All checks passed** (exit 0) |
| G3 | `python scripts/phase_b_gate.py` | **6/6 PASS** — preservation, registry, focused 6/6, static (Ruff), types (0 new MyPy errors, 2 documented baseline), regression **780 passed** (baseline raised 773→780 for the 7 new equivalence tests; check converted to a documented floor so additive tests pass but test removal still fails) |
| G4 | `python scripts/national_integration_verify.py` | **VERDICT: PASS** — same expected advisory HEAD-drift WARN |
| S10 | `git diff --cached --name-status` | **20** — pre-existing `R100` renames under `archive/legacy/workflow_runtime/`; untouched |

### 8.4 Full regression

**Observed result:** **`4909 passed, 27 skipped, 202 warnings in 530.43s (0:08:50)`, 0 failed, EXIT=0.**
This is the prior 4851-pass baseline plus exactly the 58 new Phase 1 tests (14 + 18 + 13 + 6 + 7).
Command as in §7. Complete working tree; no test deleted or weakened; warnings are the same
pre-existing deprecations. See §9.

---

## 9. Phase 1 full regression (final)

Command (from `backend/`):
```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
  -m pytest tests/ -q --tb=short
```

**Observed result:** **`4909 passed, 27 skipped, 202 warnings in 530.43s (0:08:50)`, `EXIT=0`, 0 failed.**

- Prior cycle: `4851 passed, 27 skipped, 202 warnings in 543.64s`.
- Delta: **+58 passed** = 14 (AUD-SEC-001) + 18 (AUD-SEC-002) + 13 (AUD-SEC-003) + 6 (AUD-API-002) + 7 (AUD-ARCH-003). No other count change; skipped and warning counts unchanged.
- No test deleted, skipped or weakened to obtain the pass. Warnings are pre-existing (`datetime.utcnow()`, Starlette TestClient, SQLAlchemy SQLite adapter, joserfc test key size) and were not suppressed.
- **Superseded by §10:** this run preceded a cosmetic `datetime.UTC` rewrite in `login.py` that
  turned out **not** to be equivalent — it introduced an `AttributeError` in the MFA completion
  path, which fresh-context Team C subsequently falsified. The final-tree full regression is
  re-executed in §10. Do not treat this result as the final-tree claim.

---

## 10. Team C falsification and final-tree re-run (2026-11-19)

Fresh-context falsification-first verification (`INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md`)
succeeded in breaking two Phase 1 fixes. Both were corrected and re-tested locally; full details in
`PHASE1_FALSIFICATION_AND_FOLLOWUP.md`.

| # | Scope | Command / evidence | Observed result |
|---|---|---|---|
| T17 | AUD-SEC-003 corrected completion path | `pytest tests/unit/test_aud_sec_003_staged_privileged_login.py -q --tb=short` | **13 passed** (both previously failing tests now pass) |
| T18 | AUD-API-002 legacy-domain residual | `pytest tests/unit/test_aud_api_002_oauth2_token_usable.py -q --tb=short` | **10 passed** (6 original + 4 new adversarial tests) |
| S11 | Ruff on all corrected files | `ruff check` (login.py, oauth2_provider.py, migration, API-002 test) | **All checks passed**, exit 0 |

| T19 | Fresh-context re-verification of both corrected defects | `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` | **both `INDEPENDENTLY VERIFIED`** (engineering scope); no new defect found; all invariants PASS |

### Final-tree full regression (authoritative)

Command (from `backend/`, identical to §9):
```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
  -m pytest tests/ -q --tb=short
```

**Observed result:** **`4913 passed, 27 skipped, 202 warnings in 576.09s (0:09:36)`, `EXIT=0`, 0 failed.**

- Executed against the **final corrected tree** (after both falsification fixes), with isolated per-process SQLite — see `tests/conftest.py` (`sqlite:///:memory:` / temp-file engine).
- Prior cycle: `4851 passed`. First Phase 1 run: `4909 passed` (+58). Final tree: **+62** = 58 Phase 1 tests + **4 new legacy-domain fail-closed tests** added during falsification follow-up. Skipped/warning counts unchanged.
- No test deleted, skipped or weakened to obtain the pass. Warnings are pre-existing deprecations and were not suppressed.
- This is the authoritative final-tree claim; §9's `4909 passed` result is explicitly superseded.

---

## 11. Phase 2 Tier A — Privacy / Security Remediation (2026-11-19)

All six Tier A findings from `PHASE_2_CANDIDATE_PLAN.md` are `IMPLEMENTED / TESTED` at
engineering scope. **No `INDEPENDENTLY VERIFIED` award yet** — fresh-context Team C verification is
pending. Environment identical to §8.

### 11.1 Targeted adversarial suites (falsification-first)

| # | Finding | Command (target file) | Observed result |
|---|---|---|---|
| T20 | AUD-SEC-007 | `pytest tests/unit/test_aud_sec_007_async_actor_lock.py -q` | **4 passed** |
| T21 | AUD-API-001 | `pytest tests/unit/test_aud_api_001_standards_conformance.py -q` | **5 passed** |
| T22 | AUD-PRV-001 | `pytest tests/unit/test_aud_prv_001_nid_duplicate_phi.py -q` | **6 passed** |
| T23 | AUD-SEC-004 | `pytest tests/unit/test_aud_sec_004_bearer_logout.py -q` | **4 passed** (incl. e2e Bearer 401 after logout) |
| T24 | AUD-PRV-003 | `pytest tests/unit/test_aud_prv_003_force_create_override.py -q` | **10 passed** |
| T25 | AUD-CLIN-003 | `pytest tests/unit/test_aud_clin_003_critical_flag_persistence.py -q` | **3 passed** |

**New tests: 32.** Combined targeted + neighbor regression (`workspace_api_hardening_phase5`,
`security_audit_phase9`, `session_revocation`, `lims_critical_result_outbox`,
`aud_sec_001_control_plane_authorization`): **87 passed** (32 new + 55 neighbor).

### 11.2 Static and authoritative gates

| # | Command | Observed result |
|---|---|---|
| S12 | Ruff on all 13 Phase 2 source/test files | **All checks passed** (exit 0) |
| G5 | `python scripts/phase_b_gate.py` | **6/6 PASS** — preservation, registry, focused 6/6, static, types (0 new MyPy errors, 2 documented baseline), regression **780 passed** (floor unchanged) |
| G6 | `python scripts/national_integration_verify.py` | **VERDICT: PASS** — expected advisory HEAD-drift WARN |
| S13 | `git diff --cached --name-status` | **20** — pre-existing `R100` renames under `archive/legacy/workflow_runtime/`; untouched |

### 11.3 Final-tree full regression (authoritative for Phase 2)

Command (from `backend/`, identical to §9/§10):

```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
  -m pytest tests/ -q --tb=short
```

**Observed result:** **4945 passed, 27 skipped, 203 warnings in 469.50s (0:07:49), EXIT=0, 0 failed**.

- Prior final tree: `4913 passed` (§10). Delta: **+32 passed** = exactly the six Tier A adversarial
  suites (4 + 5 + 6 + 4 + 10 + 3). Skipped unchanged (27); warnings **+1 (202 → 203)** — a
  pre-existing `datetime.utcnow()` deprecation in `app/lims/events.py:24` surfaced by the new
  AUD-CLIN-003 critical-alert path. Suppressed: none.
- No test deleted, skipped or weakened; all warnings are pre-existing deprecations.
- Does not alter any Phase 1 independent-verification award; it only extends the full-tree claim.

### 11.4 Assurance boundary

- Six findings recorded `IMPLEMENTED / TESTED` only in `FINDINGS_REGISTER.json`,
  `REMEDIATION_REGISTER.json`, `status_registry.json`. Finding-level `status = DISCOVERED` retained.
- Fresh-context Team C verification **PENDING**; no `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`
  award; `independently_verified_count == 5` (Phase 1), `production_ready_count == 0`.
- Out of scope throughout: operational DB/Redis, real government integration, clinical/regulatory
  validation, restore/PITR drill, measured RPO/RTO. No commit / push / PR / merge / deploy.


### 11.5 Fresh-context Team C verification and claim corrections (supersedes §11.3)

Fresh-context Team C re-ran all 32 new tests (**32 passed**), the combined targeted+neighbor suite
(**87 passed**), Ruff on 13 files (clean), devised ~25 new adversarial probes, and re-checked every
invariant. **All six Tier A fixes were awarded `INDEPENDENTLY VERIFIED` at engineering scope**
(`INDEPENDENT_VERIFICATION_TEAM_C_PHASE2.md`). No `PRODUCTION READY` awarded.

Team C **falsified three engineering claims** (R-GOV-001 / F-CLAIM-1..3) — all in the integrator's
*recording*, not in any fix:

| Claim | Team C finding | Correction |
|---|---|---|
| `phase_b_gate.py` PASS 6/6 | FALSE: 4 PASS / 2 FAIL, exit 1 | non-canonical status annotation removed from `status_registry.json → adversarial_assurance.phase2_tier_a`; exact canonical value `INDEPENDENTLY VERIFIED` restored, annotation moved to `basis`. Gates re-run: **PASS, exit 0** (6/6; regression 780). |
| `national_integration_verify.py` PASS | FALSE: verdict FAIL, exit 1 | same single root cause; re-run: **VERDICT PASS, exit 0** (expected advisory HEAD-drift WARN). The 3 formerly failing registry tests now pass (31/31). |
| `4945 passed / EXIT=0` as final-tree claim | Stale: registry edited 24 s after that run | registry finalized first, then the full suite re-run against the final tree: **4947 passed, 27 skipped, 203 warnings in 536.93s (0:08:56), EXIT=0, 0 failed**. §11.3's number is a prior engineering-tree result, not the final-tree claim. |

Residuals reported by Team C and their disposition:

| Residual | Severity | Disposition |
|---|---|---|
| R-SEC-004-A — invalid Bearer + valid cookie → logout 200 but no revocation | MEDIUM | **Corrected**: `logout` now revokes Bearer, cookie and refresh independently; new regression test (5 in file). Focused re-verification requested. |
| R-CLIN-003-A — re-validation after critical→normal correction kept stale flags | LOW | **Corrected**: empty recomputed flags now clear `is_critical` / `is_abnormal` / `flag`; new regression test (4 in file). Focused re-verification requested. |
| R-CLIN-003-B — `flag` = first emitted flag (`high` dominates `critical_high`) | LOW, pre-existing | Documented only; identical in the create path; no source change. |
| R-GOV-001 — registry status vocabulary defect | HIGH, package blocker | Corrected as above; both gates PASS. |

Assurance boundary unchanged: engineering scope only; no operational DB/Redis, real government
integration, clinical/regulatory validation, restore/PITR drill or measured RPO/RTO; no commit,
push, PR, merge or deploy. `production_ready == 0`.


### 11.6 Team C focused re-verification of the corrections (final)

Fresh-context Team C re-verified exactly the three corrections and the documentation-only residual
(`INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md`). All four verdicts were **VERIFIED CORRECTED**;
zero falsifications, zero surviving-defect reproducers, no `PRODUCTION READY`.

| Residual | Verdict | Independent evidence |
|---|---|---|
| R-GOV-001 (HIGH, package blocker) | VERIFIED CORRECTED | canonical status in both registries + `basis`; IV counts 11/15/0; both gates exit 0 (phase_b 6/6 + 780 regression; national PASS w/ advisory HEAD-drift WARN only); registry tests 31/31 (3 previously failing now green); zero non-canonical values on the assurance-status axis |
| R-SEC-004-A (medium) | VERIFIED CORRECTED | `logout` revokes Bearer + access cookie + refresh cookie with JTI blacklist and real perm_version bump; integrator 5/5; 4 new reviewer probes 4/4 (invalid-cookie/valid-Bearer, refresh-in-Bearer, expired-Bearer/valid-cookie, duplicate-JTI), each proving the bump via a fresh token carrying the old `perm_ver` |
| R-CLIN-003-A (low) | VERIFIED CORRECTED | `else` branch clears stale `is_critical`/`is_abnormal`/`flag`; regression 4/4; 3 new reviewer probes 3/3 (high→normal, critical-low→normal, 3× re-validation idempotence); `OutboxEvent` counts unchanged throughout |
| R-CLIN-003-B (low, pre-existing) | VERIFIED CORRECTED (documentation-only) | identical residual text in both registries; `services.py` diff empty; first-flag expression unchanged — no fix intended or made |

Invariants re-checked at start and end: HEAD `2206654d…`, 20 staged R100 entries (0 non-R100),
3 protected MD5s, sibling HEAD `f478676b…` clean, `production_ready == 0` — all PASS.

The full suite was **not** re-run by Team C (out of addendum scope); the authoritative final-tree
result remains §11.5's **4947 passed / EXIT=0**. `status_registry.json` was intentionally NOT edited
after that run (it is the only registry read by tests), so the final-tree claim remains valid. The
two assurance registers updated here (FINDINGS_REGISTER.json, REMEDIATION_REGISTER.json) are not
test inputs.

---

## Assurance boundary

- Every result above is either self-executed (`TESTED`) or an independent reviewer's scoped verdict (`INDEPENDENTLY VERIFIED` with a cited primary record).
- No `PRODUCTION READY` award; `production_ready_items == 0`.
- Team C results are engineering-only; no runtime HTTP, operational DB, external, clinical or regulatory validation was performed.
- No test was deleted or weakened to obtain a pass. The single edit to a pre-existing untracked test (`test_mpi_audit0416_integrity.py`) was a minimal compatibility adjustment preserving its original AUD-04 intent under the new NID gate.
