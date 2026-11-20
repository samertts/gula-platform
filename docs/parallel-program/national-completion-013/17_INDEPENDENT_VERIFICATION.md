# 17 — Independent Verification — GULA-NATIONAL-COMPLETION-013

## Scope

Independent adversarial verification of the locally implemented fixes. The verifier ran in a fresh child session with read-only scope; it did not trust the implementer's summary, read the actual code and logs, and reproduced targeted checks.

**Verifier session:** `ses_e073cf6fcffed7ZotQIcyHLKBX`  
**Workspace reviewed:** `/tmp/opencode/gula-national-completion-013` (docs commit `5079d67d`, product changes uncommitted)  
**Protected workspace:** `/home/samertts/workspace/projects/gula-platform` (read-only)

## Methodology

1. Reproduce the original defect against the pre-fix code where practical.
2. Re-run the same reproduction against the fixed code.
3. Attempt negative proof by perturbing/disabling the fix where practical.
4. Record exact command, environment, output, exit code, and limitations.
5. No agent may approve its own work as sole acceptance authority.

## First pass — classifications

| #   | Claim                                   | Classification         |
| --- | --------------------------------------- | ---------------------- |
| 1   | Critical-result identity contract       | **PARTIALLY VERIFIED** |
| 2   | NIAM mount/handler guard + HTTP 404     | **VERIFIED**           |
| 3   | gRPC gateway fail-closed                | **VERIFIED**           |
| 4   | Self-registration / MPI NID fail-closed | **VERIFIED**           |
| 5   | Python 3.10 shims + migration repairs   | **PARTIALLY VERIFIED** |
| 6   | Fresh PostgreSQL 16 migration chain     | **VERIFIED**           |
| 7   | Test counts                             | **VERIFIED**           |
| 8   | Static/security scans                   | **VERIFIED**           |
| 9   | Delivery gates / posture                | **VERIFIED**           |

No hidden secret, PHI, unsafe Git action, or protected-workspace mutation was found.

### Protected-workspace invariants (verified, exit 0)

```text
branch    remediate-security-001
HEAD      f478676b6fc375338648dde46fbf076c015a3f91
status    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
remote    ssh://git@ssh.github.com:443/samertts/gula-platform.git
worktrees 6
stashes   2
```

### Verifier-reproduced results

- Critical-result focused tests: `6 passed`, exit 0 (`PYTHONDONTWRITEBYTECODE=1 ... pytest -p no:cacheprovider tests/test_critical_result_contract_nc013.py`).
- NIAM focused tests: `5 passed`, exit 0.
- gRPC focused tests: `3 passed`, exit 0.
- NID focused tests: `3 passed`, exit 0.
- Python 3.10 focused tests: `14 passed`, exit 0 (pre-closure count).
- Migration graph: `heads ['20260908_0001']`, `bases ['20250322_0000']`, 102 revisions, no duplicate revision IDs; `3 passed`, exit 0.
- Surrounding regression: `471 passed, 4 skipped`, exit 0 (before and after dependency upgrades).
- Ruff, Bandit `-ll`, Semgrep `p/python`: exit 0, no findings.
- `pip-audit`: initial `Found 55 known vulnerabilities in 6 packages`; final `No known vulnerabilities found`, exit 0.
- Trivy vulnerability DB download failed (documented as NOT COMPLETED); secret/misconfig scan `0 secrets`, `490` misconfigurations in pre-existing infra manifests.
- `git ls-remote --heads origin 'execution/gula-national-completion-013'` empty; `gh pr list --head ... --state all` returned `[]`. No push or PR under 013.

### Gaps raised by the first pass

- **IND-01 — HIGH — Contract drift:** `backend/app/contracts/events.py` still required bare `result_id`; `critical_alerts.py` still returned bare `result_id`; no live `RESULT_CRITICAL` subscriber; order-time critical event had been removed.
- **IND-02 — HIGH — Python 3.10:** three app files still contain Python 3.12-only syntax (`clinical_gateway/contracts.py`, `identity/repositories/base.py`, `engineering/generators/capability.py`); one is in the change set. Focused 3.10 tests pass only because they do not import those modules.
- **IND-03 — MEDIUM — Migration history:** `20260815_0023` was repaired in place; existing-deployment upgrade compatibility is unproven and requires a separate owner-approved ALTER migration.
- **IND-04 — MEDIUM — Infrastructure:** 490 open misconfigurations (34 CRITICAL); vulnerability scan incomplete.
- **IND-05 — HIGH — Governance:** all OD-001…OD-025 remain `BLOCKED`; `production_ready=0`; the final report was still a placeholder at review time.

## Closure of IND-01 (implemented, locally re-tested)

- Event registry schemas for `ResultPublished`, `ResultAmended`, `CriticalAlertTriggered` bumped to `1.1.0`: bare `result_id` forbidden, `result_store` required, conditional `lab_result_id`/`lims_result_id` via `oneOf`.
- `get_critical_alerts()` emits `result_store` + `lab_result_id`.
- Order-time `RESULT_CRITICAL` emission restored with a namespaced reference and all original notification fields.
- `app/contracts/generator.py` uses `app._compat.UTC` so Python 3.10 can import the registry.
- Three new regression tests added.

Evidence: `evidence/test_logs/focused_nc013_py312_driftclosed.log` (exit 0, **22 passed**), `focused_nc013_py310_driftclosed.log` (exit 0, **17 passed**), `regression_identity_lims_mpi_py312_driftclosed.log` (exit 0, **471 passed, 4 skipped**), `ruff_changed_nc013_driftclosed.log` (exit 0), `bandit_changed_nc013_driftclosed.log` (exit 0), `semgrep_changed_nc013_driftclosed.log` (exit 0).

### Second independent pass — results

The same verifier re-reviewed only the closure edits, read-only:

| Prior gap                                                 | Classification                                                                                                                                                                                              |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event registry bare `result_id` / namespaced schema drift | **PARTIALLY VERIFIED** — bare `result_id` removed; schema valid; but `oneOf` did not reject payloads carrying both `lab_result_id` and `lims_result_id`, and `correlation_id: "result_store"` is non-unique |
| Alert API bare `result_id`                                | **VERIFIED**                                                                                                                                                                                                |
| Order-time critical event restored/namespaced             | **VERIFIED**                                                                                                                                                                                                |
| Python 3.10 collection via `generator.py`                 | **VERIFIED**                                                                                                                                                                                                |

The verifier also reproduced: focused suites `22 passed` / `17 passed`, `tests/test_lims_tenant_isolation.py` `5 passed`, tenant-alert isolation `1 passed`, `test_contract_generator.py` `1 passed`, Ruff exit 0, protected-workspace invariants unchanged. It confirmed no live `RESULT_CRITICAL` subscriber and classified that as a deliberate safety non-activation, not a code-fix blocker.

**Final closure of the remaining schema gap:** the three event schemas now use `not.anyOf` to reject both bare `result_id` and the simultaneous presence of `lab_result_id` + `lims_result_id`. Validation with `jsonschema` `Draft202012Validator` (system Python 3.10, exit 0) reports for all three events: `schema_ok=True single_accepted=True bare_rejected=True dual_rejected=True`. Focused suites re-run after this change: `22 passed` (3.12), `17 passed` (3.10); Ruff/Bandit/Semgrep exit 0.

Evidence: `evidence/test_logs/focused_nc013_py312_schema_final.log`, `focused_nc013_py310_schema_final.log`, `event_schema_jsonschema_final.log`, `ruff_changed_nc013_schema_final.log`, `bandit_changed_nc013_schema_final.log`, `semgrep_changed_nc013_schema_final.log`.

## Items deliberately not closed

- **No live `RESULT_CRITICAL` subscriber.** `process_critical_result_from_event()` is tested and fails closed on ambiguous payloads, but is not wired to the event bus. Activating delivery would implement a clinical notification workflow while `AUD-CLIN-001` is `BLOCKED`. This is a documented safety non-activation, not a claimed fix.
- **Python 3.12-only syntax sites** in three app files remain as-is; they are outside the Python 3.10 compatibility claim and are not represented as fixed.
- **Historical migration repaired in place**; deployed-database upgrade paths remain owner approval items.
- **Infrastructure misconfigurations and incomplete vulnerability scan** remain open.
- **All human approvals remain `BLOCKED`.**

### Full-suite check (new pre-existing finding)

The complete backend suite was executed: `1 failed, 2,754 passed, 27 skipped`, exit 1 (`full_suite_nc013_driftclosed.log`). The failure is a safety-critical transfusion transition (`verified -> in_progress` rejected). It was reproduced identically on an untouched baseline worktree (`baseline_icu_transfusion_check.log`, exit 1), so it is pre-existing and **not** a NC013 regression. Recorded as NC013-C05 with `HUMAN APPROVAL REQUIRED`; not changed in this program.

### Post-delivery CI triage and environment restart

After the draft PR was published, GitHub Actions checks were inspected. `Secret Scan` initially failed on a gitleaks false positive and was fixed; the re-run reports `no leaks found`. Three jobs failed because `backend/requirements.txt` omitted `greenlet`, which is required by `sqlalchemy.ext.asyncio`; the dependency was declared with a free MIT-licensed package already pinned in the lock file. Remaining failures (repo-wide Ruff formatting, Prettier syntax error in a pre-existing JSON file, frontend-v3 test, ambiguous `alembic downgrade -1` at the pre-existing three-parent head, and the constitution checker crashing on Python 3.14 `ast.Str`) were triaged as pre-existing or outside NC013 scope. A local diff-mode constitution audit found no hardcoded-secret, vendor-lock-in, paid-dependency or SaaS violation introduced by this change; its failures are duplicate-code/dead-code heuristics and the already-documented Python 3.12-only syntax sites. Details: `evidence/test_logs/ci_failure_triage.md`.

The environment restarted during this work and removed the first isolated clone. It was recreated from the pushed branch at `a5c2a0de7bdf73a2aad4801a64c2df5aef49a684`; no approved work was lost, and the protected workspace invariants remained unchanged (`e3b0c44…`, branch `remediate-security-001`, HEAD `f478676b…`, 6 worktrees, 2 stashes).

Final independent CI observation at `a406cde1f991cd5cbb23676a7606ce1fcb600450`: `gh pr checks 307` → 23 PASS / 6 FAIL. The previously failing identity, security/tenant-isolation, secret-scan, dependency-audit and PostgreSQL schema checks now pass. The six remaining failures were read from raw GitHub job logs and confirmed pre-existing or out of scope; none is an NC013 code regression. `mergeable=MERGEABLE` is structural only. Full matrix: `evidence/test_logs/final_ci_summary.md`.

## Verification state

Two independent passes complete. The first found four contract gaps and five verified claims; the second verified three closures directly and one partially, and the remaining schema flaw was closed and re-validated with a JSON Schema engine. Independent verification is **not** release approval. Posture remains `NOT ACCEPTED FOR PRODUCTION — HOLD`.

The `correlation_id: "result_store"` observation remains: the registry already uses non-unique correlation fields elsewhere (e.g. `lab_id`, `order_id`), so this follows existing convention and does not affect fail-closed ID resolution. It is recorded as a minor design limitation, not a security finding.
