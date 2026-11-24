# Independent Adversarial Verification — Team C

**Artifact:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C.md`
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` (HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`)
**Read-only sibling:** `/home/samertts/workspace/projects/gula-platform` at pinned `f478676b6fc375338648dde46fbf076c015a3f91` (confirmed via `git rev-parse HEAD`; no git write commands issued there)
**Date:** 2026-11-18
**Role:** Independent, fresh-context verification engineer. Not involved in implementing any of the four remediations. Method: attempt to falsify, not confirm.

## Scope and constraints observed

- Worked exclusively in the integration repo; sibling repo was only read for its pinned Python interpreter.
- No source file, config, test, dependency file, or git index was modified. No `git add`/`commit`/`checkout`/`reset`/`clean`/force-push. The 20 pre-existing staged `R100` renames and the large pre-existing Team A modified/untracked surface were left untouched.
- Only new file created is this report. One scratch artifact was written outside the repo, at `/tmp/opencode/teamc-uv-export.txt`, as explicitly instructed for the `uv export` inspection.
- Interpreter: `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12.13, pytest 9.1.1). `uv`: `/home/samertts/.local/bin/uv` (uv 0.11.26 — identical to the CI pin in `security-hardening.yml`).
- All data synthetic/in-memory (SQLite). No network installs, no DB writes to any persistent/external database, no deployment, no external integration calls.

---

## 1. FK target-integrity remediation (NR-011 / co-collection failure)

**Verdict: INDEPENDENTLY VERIFIED — engineering scope only, static inspection + targeted and co-collection tests + forced FK-resolution probe; not runtime/DB/external validation.**

### Exact commands run and observed results

1. Read `backend/app/identity/adaptive_auth/models.py`, `backend/app/identity/models/__init__.py`, `backend/app/identity/models/identity_authority.py`, `backend/tests/unit/test_fk_target_integrity.py`, `backend/tests/unit/test_nr011_metadata_discovery.py`, `backend/migrations/versions/20260723_0002_niam_completion_tables.py`, `backend/migrations/versions/20261114_0001_unify_foundation.py`, `backend/migrations/env.py`.

2. Targeted test (from `backend/`):
   ```
   ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
     /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
     -m pytest tests/unit/test_fk_target_integrity.py -q --tb=short
   ```
   Observed: `collected 5 items` → `5 passed, 1 warning in 11.60s`, `EXIT_CODE=0`.

3. Original failure reproduction — co-collection of NR-011 discovery with `tests/identity` (the exact scenario previously documented as raising `NoReferencedTableError`):
   ```
   ... -m pytest tests/unit/test_nr011_metadata_discovery.py tests/identity -q --tb=short
   ```
   Observed: `185 passed, 4 skipped, 1 warning in 6.73s`, `EXIT_CODE=0`. (The 4 skips are pre-existing migration tests; they are not skips introduced by this remediation. `test_cross_metadata_foreign_keys_resolve` ran and passed.)

4. Forced FK resolution on the *real Alembic merged metadata* (execute `env.py`'s literal `# BEGIN NR-011 MERGE` block against all 17 bases, then access `fk.column` on every FK; `app.main` imported first to load route-only model modules as in the failing order):
   Observed: `merged tables: 756`, `single MetaData: True`, `FKs force-resolved on merged (Alembic) metadata: 1174`, `niam_adaptive_mfa_sessions.session_id -> ['niam_sessions.id'] | resolves: True`, `OK: zero NoReferencedTableError on merged Alembic surface`, `EXIT_CODE=0`.

### Falsification attempts and findings

- **Repo-wide grep for `niam_user_sessions`:** 12 matches. Zero active FK declarations. All remaining hits are prose: historical comment in `adaptive_auth/models.py:76`, docstrings in `test_fk_target_integrity.py:7`, older Team A governance reports, and a stale table listing in `docs/niam/SESSION_GOVERNANCE.md:114`. No model or migration defines/uses it as a live target. Could not falsify.
- **Model/migration drift check:** `20260723_0002:1240` already declares `sa.ForeignKey("niam_sessions.id", ondelete="SET NULL")`; the corrected ORM model now matches byte-for-byte in target/ondelete/nullability. The old `niam_user_sessions` target was genuinely absent from all models and migrations. Could not falsify.
- **ORM mirror completeness:** `IdentityAuthorityRecord` (`__tablename__ = "niam_identity_authorities"`) defines uuid, authority_id, name_en, name_ar, authority_type, jurisdiction, status, is_active and inherits `id`/`created_at`/`updated_at` from `IdentityBaseEntity` — matches the `20261114_0001` DDL. It is imported and listed in `__all__` of `app/identity/models/__init__.py`, and `migrations/env.py:103` imports `app.identity.models`, so Alembic autogenerate sees it. Forced resolution over 1174 merged FKs covers the three `*_id -> niam_identity_authorities.id` references. Could not falsify.
- **Two deliberately flawed probes (reported honestly):** an inline `.column` walk over only `Base.metadata + IdentityBase.metadata`, and again over all 17 bases but still resolving against each FK's *owning* MetaData, both raised `NoReferencedTableError` for a **different**, pre-existing cross-metadata FK: `niam_assignments.clinical_facility_resource_id -> facilities.id`. This is an artifact of probing below NR-011's merge layer — `.column` resolves within the owning MetaData, and `facilities` lives in another base. Re-running through the actual Alembic merge path (the check above) resolved all 1174 FKs with zero error. This is not a defect in the fix; it confirms why the merge exists.

### Residual limitations

- No PostgreSQL/DDL execution, no `alembic check` against a live database, no application boot with real schema; all evidence is metadata/static plus SQLite-backed tests.
- `docs/niam/SESSION_GOVERNANCE.md:114` still lists `niam_user_sessions` as a table (stale documentation, outside the four remediated files). It is documentation drift, not a functional FK defect.
- Pre-existing cross-metadata FKs (e.g. `niam_assignments -> facilities`) only resolve through the NR-011 merged metadata; they are outside this remediation's scope.

---

## 2. AUD-CLIN-001 (CRITICAL) — critical-result alert

**Verdict: INDEPENDENTLY VERIFIED — engineering scope only, static inspection + 4 targeted tests + event/subscriber census; not runtime/DB/external/clinical validation.**

### Exact commands run and observed results

1. Read `backend/app/lims/workflows.py`, `backend/app/lims/routes.py` (lines 2170–2200), `backend/app/lims/events.py`, `backend/app/services/outbox_service.py`, `backend/tests/unit/test_lims_critical_result_outbox.py`.

2. Targeted test (from `backend/`):
   ```
   ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
     /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
     -m pytest tests/unit/test_lims_critical_result_outbox.py -q --tb=short
   ```
   Observed: `collected 4 items` → `4 passed, 3 warnings in 83.42s`, `EXIT_CODE=0`. Warnings: one Starlette `TestClient` deprecation and two pre-existing `datetime.utcnow()` deprecations from `app/lims/events.py:24`; no failures.

### Falsification attempts and findings

- **Search for any remaining false-success path:** repo-scoped grep over `backend/app/lims` for `["']alerted["']`, `status.*alerted`, `clinician_notified.*True`, `delivery_status.*(sent|delivered)` returned only three hits, all in the explanatory docstring at `workflows.py:230–240` describing the *old* defect and the "NEVER alerted" rule. No live code path returns `alerted`.
- **Single call path:** grep for `process_critical_result|CriticalResultDetected|lims.result.critical` across `backend/app` found exactly one production caller (`routes.py:2182–2183`) and one emitter (`workflows.py:295`). No alternate route or background path invokes the workflow.
- **Route commit semantics:** `routes.py:2188` commits only when `outcome.get("status") == "notification_pending"`; error/skipped paths return without a write. The workflow itself calls `emit_to_outbox(...)` which does `db.add(event); db.flush()` inside the caller's transaction — no internal commit, so event and business state stay atomic. Could not falsify the durability claim.
- **No actual notification sent:** `outbox_service.emit_to_outbox` is pure persistence (constructs `OutboxEvent(status="pending", attempts=0)`, `db.add`, `db.flush`, return). Dispatch exists only in `OutboxWorker.run_once`, which is not invoked by this request path. A repo-wide census of `subscribe(`/`events.emit` found no subscriber for `lims.result.critical` (only docs/catalog/test/definition references), so even a separately started worker has no clinician-delivery handler for this event. The response fields `clinician_notified=False`, `delivery_status="pending_dispatch"`, `acknowledgement_status="NOT_CONFIGURED"` are honest. Could not falsify.
- **Event-type correctness:** `LIMSEvent` subclasses set `event_type` as a class attribute, so `asdict()` would carry the base default `""`; the code explicitly overwrites `envelope["event_type"] = CriticalResultDetected.event_type` before emission, and uses the same class attribute for `emit_to_outbox(event_type=...)`. The test asserts `event.event_type == "lims.result.critical"` and the nested payload value. This closes an otherwise easy falsification.

### Residual limitations

- SQLite/in-memory test only; no PostgreSQL, no real outbox worker run, no dispatch/acknowledgement flow exercised.
- Recipient, escalation policy and acknowledgement are deliberately owner-gated and remain `None`/`NOT_CONFIGURED`; actual clinician delivery is **BLOCKED** pending that owner decision and a configured delivery worker/adapter. This report does not assess clinical safety or whether a 15/60-minute window is clinically correct.
- Pre-existing `datetime.utcnow()` deprecation in the shared event base was observed but not part of this remediation.

---

## 3. AUD-MPI-001 (HIGH) — unverified NID auto-claim

**Verdict: INDEPENDENTLY VERIFIED — engineering scope only, static inspection + 13 targeted tests + custom synthetic bypass probes; not runtime/PostgreSQL/concurrency/external validation.**

### Exact commands run and observed results

1. Read `backend/app/services/mpi/resolver.py` (all 1027 lines), `backend/app/services/mpi/matcher.py`, `backend/tests/unit/test_mpi_unverified_nid_gate.py`, `backend/tests/test_mpi_audit0416_integrity.py`.

2. Targeted tests (from `backend/`):
   ```
   ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
     /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python \
     -m pytest tests/unit/test_mpi_unverified_nid_gate.py tests/test_mpi_audit0416_integrity.py -q --tb=short
   ```
   Observed: `collected 13 items` (4 + 9) → `13 passed, 1 warning in 80.18s`, `EXIT_CODE=0`.

3. Custom synthetic bypass probe (in-memory SQLite via `python -c`, no files created) exercising the resolver directly with `nid_verified=False`:
   - First genesis: `created=True`, `nid_verified=False`, `method=new`, `score=None`.
   - Re-resolve with same unverified NID + identical demographics + matching family_id: `method=probabilistic`, `score=1.0`, features `{phone, dob, name_jw, gender, family}` — **no `nid_hash` feature**; `nid_exact? False`.
   - Re-resolve with same unverified NID + conflicting demographics + matching family_id (lock-reconciliation branch): `method=pending_review`, `score=0.0`, features `{nid_hash: True, nid_verified: False, nid_not_authoritative: True, nid_reconciled_under_lock: True}`; `nid_exact? False`, `score==1.0? False`.
   - Direct matcher call with `nid_hash` in profile: `1.0 nid_exact` (short-circuit still present in the pure matcher).
   `EXIT_CODE=0`.

### Falsification attempts and findings

- **Fast path:** `resolver.py:431–449` checks `canonical_hit.nid_verified`; only that branch sets `best_method="nid_exact"`, `best_score=1.0`. On an unverified hit it rebuilds the profile **without** `nid_hash`, specifically to remove the matcher's 1.0 short-circuit. Could not falsify.
- **Auto-match decision:** `resolver.py:495–506` requires `best_method == "nid_exact" and best_candidate.nid_verified` to persist `claim_method="nid_exact"`/`score=1.0`; otherwise it downgrades to `"probabilistic"`. Two independent conditions must both hold. Could not falsify.
- **Lock-reconciliation path:** `resolver.py:528–563` re-reads under `acquire_audit_chain_lock`, then gates on `locked_citizen.nid_verified`; unverified → `pending_review`, `score=0.0`, `nid_not_authoritative=True` provenance. My custom probe drove this exact branch and confirmed the gate. `test_mpi_audit0416_integrity.py:74–109` sets `nid_verified=True` explicitly before asserting `nid_exact`, and `test_locked_nid_reread_is_present_in_create_branch` structurally pins the lock/reconciliation code. Could not falsify.
- **Can any write path set `nid_verified=True` from lab input?** Repo-wide grep for `nid_verified` assignments found only `False` in resolver genesis (`568`), detach (`748`) and `routes/register.py:94`; model/migration defaults are `False`; the only `= True` assignments are in the two test files exercising the verified-NID control case. No production path promotes an untrusted NID to verified. Could not falsify.
- **Alternate caller of the short-circuit:** `app/health_data/mdm/service.py:140` calls `mpi_build_profile` with a `national_id_hash`, but only returns the profile for display — it never calls `score()`. The only production `score()` caller is the resolver, which strips `nid_hash` when unverified. Could not falsify an alternate app-level entry to the short-circuit.

### Residual limitations (honest findings, not blockers)

- **A 1.0 score is still reachable without any NID gate violation:** fully concordant phone + exact DOB + name JW 1.0 + gender + family hash sums the documented weights to exactly 1.00 and is labelled `method="probabilistic"` / `claim_method="probabilistic"` (confirmed by my probe). This is pre-existing matcher saturation, independent of `nid_verified`, and the fix's claim is specifically that the *NID-driven 1.0 short-circuit* is excluded — which held. Flagged for owner awareness, not assessed as a new defect.
- The NID short-circuit still exists in `matcher.py:108–114`; the defence currently lives at the resolver layer (profile stripping + dual `nid_verified` checks). A future caller that passes an untrusted `nid_hash` directly to `score()` would reintroduce the hazard. No such caller exists today.
- No PostgreSQL advisory-lock/concurrency interleaving test was executed; the single-process probe cannot reproduce two concurrent registrations. No external identity authority or NID verification service was contacted — whether a stored `nid_verified=True` is itself trustworthy is out of scope.

---

## 4. AUD-SUP-001 (CRITICAL) — stale uv.lock

**Verdict: INDEPENDENTLY VERIFIED — engineering scope only, read-only `uv lock --check`/`uv export` + YAML parse + cross-file pin inspection; no package installation, no `pip-audit` execution, no network.**

### Exact commands run and observed results

1. From `backend/`, hash before and after the check:
   ```
   md5sum uv.lock
   /home/samertts/.local/bin/uv lock --check
   md5sum uv.lock
   ```
   Observed: `172b5d0a8797f60bcd9ddcb89620ca00  uv.lock` both before and after; `Using CPython 3.12.13` / `Resolved 66 packages in 2ms`; `UV_LOCK_CHECK_EXIT=0`. The lock was **not** mutated. Local `uv --version` = `0.11.26`, matching the CI pin.

2. Frozen export (from `backend/`):
   ```
   /home/samertts/.local/bin/uv export --frozen --no-hashes --format requirements-txt \
     --no-emit-project -o /tmp/opencode/teamc-uv-export.txt
   ```
   Observed: `UV_EXPORT_EXIT=0`. Extracted pins:
   ```
   certifi==2026.10.23   dnspython==2.9.2   idna==3.20      joserfc==1.8.0
   pillow==13.0.0        pyasn1==0.6.5      urllib3==2.8.0
   ```
   All seven meet or exceed the claimed floors (`certifi>=2026.10.18`, `dnspython>=2.9.2`, `idna>=3.20`, `joserfc>=1.8.0`, `pillow>=13.0.0`, `pyasn1>=0.6.5`, `urllib3>=2.8.0`).

3. YAML structural parse with PyYAML from the pinned interpreter:
   - `.github/workflows/security-hardening.yml` jobs: `secret-scan`, `python-dependency-audit`, **`python-uv-lock-consistency`**, `dependency-review`. The job is present with **no `continue-on-error`** (hard gate), `timeout-minutes: 20`, pinned `uv==0.11.26`, step `Enforce backend/uv.lock is in sync with pyproject.toml` → `uv lock --check`, and a step that exports with `uv export --frozen ... -o /tmp/gula-uv-requirements.txt`, asserts the file is non-empty, greps the seven `==` pins, and runs `pip-audit -r ... --strict`.
   - `.github/dependabot.yml` now contains, for `/backend/`, both `package-ecosystem: pip` and `package-ecosystem: uv` (weekly, Monday 09:00 Asia/Baghdad, limit 10, production/development minor+patch groups), plus docker and github-actions entries.

4. Read `backend/pyproject.toml`: transitive floors present at lines 33–41; `Pillow>=13.0.0` at line 26 (capitalised — an initial case-sensitive grep missed it; confirmed present on re-read). Read `requirements.txt` and `requirements-lock.txt` for cross-path consistency.

### Falsification attempts and findings

- **Did `--check` silently rewrite the lock?** No — md5 identical before/after; no git write operations performed.
- **Do the floors actually exist in the resolver manifest?** Yes; the export (derived from `uv.lock`, not from `requirements.txt`) satisfies all seven. The concern that pip-path remediation left the uv path stale is addressed: pyproject now carries the floors and uv.lock was regenerated.
- **Is the CI gate a real hard gate?** Yes in the YAML: the job has no `continue-on-error` and its own failing commands (`uv lock --check`, empty-export check, `grep`, `pip-audit --strict`) will fail the job. I did not find a workflow-level `if:` on that job that would skip it.
- **Cross-path exact-pin differences:** `requirements-lock.txt` pins `joserfc==1.7.6` and `certifi==2026.10.18`, whereas the uv export pins `joserfc==1.8.0` and `certifi==2026.10.23`. Both sets satisfy every declared floor; the difference is normal independent-resolver behaviour, and the `joserfc` comment in `requirements.txt` explicitly cites `>=1.7.6` as the CVE fix floor. Noted as a residual, not a falsification.

### Residual limitations

- `pip-audit` was **not** executed (requires network / vulnerability-DB access, prohibited here). Only the deterministic consistency/export checks were run; the CI audit step's live result is unverified.
- No package install, no build from the exported manifest, no CVE database cross-check, no test that the exported set is runtime-compatible beyond the repo's existing interpreter versions.
- **Residual risk (not a blocker):** adding both `pip` and `uv` dependabot ecosystems on `/backend/` may generate **duplicate pull requests** for the same dependency updates, because both ecosystems discover the same `backend/pyproject.toml`/`backend/requirements*.txt` surface. Owner should consider grouping/ignoring one ecosystem or deduplicating; this does not invalidate the security floors.

---

## Summary table

| # | Fix | Verdict (permitted vocabulary) | Evidence executed | Could not falsify | Key residual |
|---|-----|--------------------------------|-------------------|-------------------|--------------|
| 1 | FK target integrity (NR-011) | **INDEPENDENTLY VERIFIED** — engineering scope only | 5/5 targeted; 185 passed + 4 pre-existing skips co-collection; 1174 FKs force-resolved on merged metadata | Yes | Stale `SESSION_GOVERNANCE.md` table name; no live PG/DDL |
| 2 | AUD-CLIN-001 critical alert | **INDEPENDENTLY VERIFIED** — engineering scope only | 4/4 targeted; static emit/route/subscriber census | Yes | Delivery/acknowledgement owner-gated → **BLOCKED**; no real worker run |
| 3 | AUD-MPI-001 NID gate | **INDEPENDENTLY VERIFIED** — engineering scope only | 13/13 targeted; custom synthetic bypass probes | Yes | Matcher 1.0 short-circuit still present but unreachable from resolver; no PG concurrency |
| 4 | AUD-SUP-001 uv.lock | **INDEPENDENTLY VERIFIED** — engineering scope only | `uv lock --check` exit 0 (lock md5 unchanged); frozen export exit 0 with all 7 pins; YAML parsed | Yes | `pip-audit` not run; pip+uv dependabot duplicate-PR risk |

## Explicit closing statements

- **No `PRODUCTION READY` status is awarded to any fix.** Every verdict is narrowly scoped to engineering/static/targeted-test verification; the permitted word is used only where I personally re-ran the relevant command and could not falsify the claim.
- **Owner-gated decisions were untouched:** HOLD, MPI REJECT, MP-001, ODR-001..004, D-020/D-021, ADR-A..J, AUD-02/07/16 were neither reviewed for reversal nor modified. Recipient/escalation/acknowledgement for critical alerts, MPI chain-fork response under D-MPI-3/4, and unmerge policy remain owner decisions.
- **No external, human, clinical, or regulatory validation was performed.** No clinician was contacted, no real national ID authority was queried, no CVE database/network audit was run, no external integration or deployment was executed. Clinical safety, regulatory acceptance, and production operability remain outside this report's scope.
- No repository file other than this report was created or modified by Team C; no git index changes were made.
