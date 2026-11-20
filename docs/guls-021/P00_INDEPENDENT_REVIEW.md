# P00 — Independent Review of PR #308

Program: GULA-GULS-021
Review target: Draft PR #308, `execution/gula-guls-020` at `8097a55849769c4f17e0cc731da1c180e5bc9305`
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Purpose and boundary

This is an independent correction review of the GULS-020 foundation before any further GULS-021 work is built on it. The PR branch was not modified. All work was performed in `/tmp/opencode/gula-guls-021` on `execution/gula-guls-021`, with `/tmp/opencode/gula-guls-021-baseline` used only for comparison.

The review covered the full PR diff, backend localization modules and tests, frontend registry/runtime/i18n/build setup, shared registry and schemas, language-pack delivery, user preferences, clinical governance, offline behavior, Android/iOS/Desktop clients, database compatibility, CI checks, security findings, and documentation/evidence claims.

No merge, deployment, production database access, production key use, or human approval was performed.

## 2. Repository state and isolation evidence

| Check               | Command                                                                                                                                      | Exit | Result                                                                                                                                                                               |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PR #308 state       | `gh pr view 308 --json number,state,isDraft,baseRefName,headRefName,headRefOid,mergeable,mergeStateStatus,mergedAt,updatedAt,url`            |    0 | `OPEN`, draft, base `main`, head `execution/gula-guls-020`, head OID `8097a55849769c4f17e0cc731da1c180e5bc9305`, `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`, `mergedAt=null` |
| PR #308 checks      | `gh pr checks 308`                                                                                                                           |    1 | 10 failing checks listed in `TEST_EVIDENCE.md`                                                                                                                                       |
| PR #307 state       | `gh pr view 307 --json number,state,isDraft,headRefName,headRefOid,url`                                                                      |    0 | `OPEN` draft `execution/gula-national-completion-013`; untouched                                                                                                                     |
| Protected workspace | `git branch --show-current; git rev-parse HEAD; git worktree list \| wc -l; git stash list \| wc -l; git status --porcelain=v1 \| sha256sum` |    0 | `remediate-security-001`, `f478676b6fc375338648dde46fbf076c015a3f91`, 6 worktrees, 2 stashes, status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`      |

The protected workspace result is byte-identical to the value recorded before execution.

## 3. Baseline CI interpretation

`gh pr checks 308` is red with 11 failing entries: 10 named gates (Backend Tests, Backend identity unit and compile gates, Constitution Compliance, Frontend v3 contract/type/build gates, Migration Check, PostgreSQL migration and schema gate, Prettier, Python Dependency Audit (`backend/requirements-lock.txt`), Ruff Format, Security and tenant isolation regression) plus the generic `test` job.

Earlier baseline runs on `main` reproduced the same failures (main run `43702721641`, formatting `43702721605`, constitution `43702721533`, IAM hardening `43702721450`, security hardening `43856373523`, PR-head security run `44816092797`). Therefore these failures are **not evidence of a GULS-021 regression**, but they do prevent any claim of a green merge gate.

The full frontend suite was also reproduced at both revisions:

| Revision        | Command    | Exit | Files                        | Tests                        |
| --------------- | ---------- | ---: | ---------------------------- | ---------------------------- |
| GULS-021 branch | `npm test` |    1 | `1 failed \| 17 passed (18)` | `2 failed \| 76 passed (78)` |
| Baseline `main` | `npm test` |    1 | `1 failed \| 15 passed (16)` | `2 failed \| 54 passed (56)` |

The failures are confined to `src/components/navigation/MobileBottomNav.test.tsx`; the component and test hashes are identical at both revisions. This is pre-existing and unrelated to GULS localization, but it keeps the aggregate gate red.

## 4. Controls verified as already correct

The following PR #308 controls were confirmed and were not duplicated:

- Ed25519 verification is fail-closed; no private key is present in the repository.
- Archive extraction rejects path traversal, symlinks, absolute paths, executable/script suffixes, and oversized members.
- Manifest file set, per-file SHA-256 digests, and content hash are checked together.
- Installation is atomic and preserves the previous version; version downgrade is rejected.
- English is the mandatory fallback and raw translation keys are not leaked to users.
- Download tokens are short-lived and compared in constant time.
- Data-saver, metered-network, and roaming checks are present in the delivery API.
- User and lab preference scopes are isolated.

## 5. Findings and corrections

### 5.1 Critical

| ID  | Finding                        | Reproduction / impact                                                                                                                                                                                      | Correction                                                                                                                                                                            |
| --- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | Hidden clinical catalog bypass | A pack declaring `catalogs: ["common"]` could include `catalogs/clinical.json`; the declared catalog list was trusted instead of the archive contents. This could install unapproved clinical terminology. | `clinical.py` now derives actual catalogs from archive files, rejects declared/actual mismatch, and applies the clinical gate to archive contents. Regression tests cover both cases. |

### 5.2 High

| ID  | Finding                                                      | Reproduction / impact                                                                                                                                                                                                                               | Correction                                                                                                                                                                                                                                            |
| --- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | Blocked language accepted as preferred language              | `PUT /api/v1/users/me/preferences/language` accepted `fa` even though it is blocked and unpublishable.                                                                                                                                              | Preference update now requires `is_active`, `is_publishable`, assigned locale, `approval_status="approved"`, and `linguistic_approval_status="approved"`. `fa` now returns `409 LANGUAGE_NOT_ACTIVE`.                                                 |
| H2  | Stable GULS error codes discarded in production HTTP handler | `public_http_detail({"code":"DOWNLOAD_BLOCKED_BY_DATA_SAVER","message":"..."}, status_code=409)` produced `("Request failed.", {})`; the factory emitted generic `CONFLICT` plus Arabic `detail_ar`. Clients could not rely on the documented code. | Added `stable_http_detail()` accepting only exact `{code,message}` details with validated uppercase codes and safe one-line messages. `factory.py` passes the explicit code to `build_error_payload()` and keeps fixed English messages untranslated. |
| H3  | Synthetic flag disabled all approval gates                   | With `GULS_ALLOW_SYNTHETIC_PACKS=1`, a signed `synthetic_test_only` pack could reach `READY` for blocked languages.                                                                                                                                 | Production/staging startup now refuses the flag; synthetic packs require a dedicated `GULS_SYNTHETIC_SIGNER_KEY_ID`; `PackManager` rejects synthetic packs signed by any other key; default root moved away from `/tmp`.                              |
| H4  | L4 role separation not enforced in pack governance           | Clinical terminology could be installed through the governance path without validating translator, linguistic reviewer, and clinical reviewer separation.                                                                                           | `validate_pack_governance()` validates `terminology/clinical.json` entries through `ApprovalRecord`; invalid L4 approval is rejected.                                                                                                                 |

### 5.3 Medium

| ID  | Finding                                             | Reproduction / impact                                                                                  | Disposition                                                                                                                                             |
| --- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M1  | `ROLLBACK_REQUIRED` dead-end                        | State machine allowed transition only to `READY`/`DISABLED`, preventing a clean retry.                 | Fixed: `ROLLBACK_REQUIRED -> NOT_INSTALLED` is now permitted and regression-tested.                                                                     |
| M2  | Archive member-count DoS                            | A small ZIP with thousands of tiny members could exhaust CPU/memory during extraction.                 | Fixed with `MAX_PACK_MEMBERS = 256` in builder and extractor.                                                                                           |
| M3  | Partial download reported `READY`                   | `Range: bytes=400-` on a 500-byte pack set status `READY` despite zero useful contiguous coverage.     | Fixed: coverage is tracked as contiguous prefixes; transport status is `COMPLETE`/`DOWNLOADING`. `READY` remains reserved for verified installed packs. |
| M4  | Shared preference key, no optimistic concurrency    | GULS and legacy accessibility share `preferences["language"]`; in-memory store has no ETag/`If-Match`. | Residual risk. No schema migration was introduced; multi-writer deployments require concurrency control before production.                              |
| M5  | In-memory delivery/lifecycle state                  | Download sessions and pack lifecycle state are process-local.                                          | Residual risk. Multi-replica production requires shared persistent state.                                                                               |
| M6  | Unsigned local state under a temporary default path | Default root was `/tmp/gula-language-packs`.                                                           | Mitigated by a service-account home default. Cryptographic state integrity and OS-level protection remain deployment responsibilities.                  |
| M7  | Dead clinical/quota checks                          | Governance checks did not reflect archive contents; Web quota was not checked before download.         | Fixed by archive-driven clinical gating and conservative `2 * requiredBytes` browser quota check.                                                       |
| M8  | Unvalidated signed fields                           | Manifest content size and approval metadata were not fully validated.                                  | Fixed with content-size consistency and approval-record validation.                                                                                     |
| M9  | Unreachable expired-token branch                    | Expired records were purged before the explicit expired-token error could be returned.                 | Fixed with a five-second expiry grace and explicit expired-token handling.                                                                              |

### 5.4 Low and informational notes

Non-blocking review notes retained for follow-up: documentation claimed client offline support before implementation; legacy `tk`/`syr` identifiers normalize to English; no dynamic-pack UI installation flow existed in any client; only ephemeral test keys were used; and no versioned client cache invalidation existed before this pass. These do not change the gate outcome but are addressed or explicitly carried into `BLOCKERS_AND_RISKS.md`.

## 6. Verification of the corrections

| Check                             |                                                                                                                                             Command | Exit | Result                              |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------: | ---: | ----------------------------------- |
| Focused backend, Python 3.12      |       `PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization backend/tests/test_error_contract.py` |    0 | 81 passed, 1 warning                |
| Focused backend, Python 3.11      |                                        `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization backend/tests/test_error_contract.py` |    0 | 81 passed, 1 warning                |
| Touched-file Python compile, 3.11 |                                                                                                                      `python3.11 -m py_compile ...` |    0 | all touched Python files compile    |
| Ruff lint                         |                                                                                               `/tmp/opencode/gula-guls-020-venv/bin/ruff check ...` |    0 | All checks passed                   |
| Registry schema                   |                                                                              `python3.11 -c 'import json,jsonschema; ... jsonschema.validate(...)'` |    0 | `registry_schema=PASS languages=14` |
| Focused frontend                  |    `npx vitest run --passWithNoTests --exclude 'e2e/**' src/guls/guls.test.ts src/guls/offline/offline.test.ts src/i18n/mobileNavResources.test.ts` |    0 | 3 files, 21 tests passed            |
| Typecheck / lint / Prettier       | `npx tsc --noEmit -p tsconfig.json --pretty false`, `npm run lint -- --max-warnings=0`, `npx prettier --check src/guls/offline/*.ts vite.config.ts` |    0 | all clean                           |

`ruff format --check` on the touched Python set exits 1 for one pre-existing toolchain conflict: Ruff 0.16.10 configured with `target-version=py314` rewrites `except (ValueError, TypeError):` into Python 3.14 syntax that is invalid on Python 3.11/3.12. The parenthesized form was intentionally retained for runtime compatibility. This is recorded as a residual CI/toolchain blocker, not hidden.

## 7. Review conclusion

The PR #308 foundation contains real, reproducible, high-severity defects that would have allowed unapproved clinical content into the system and broken the stable error contract. Those defects have been corrected in the isolated GULS-021 branch with regression tests. However, the repository-wide CI gate remains red, native client build tooling is unavailable locally, and human linguistic/clinical approvals are still absent.

Therefore PR #308 is **not accepted as a merge-ready foundation**. GULS-021 continues as an isolated, preserved branch and no stacked Draft PR is opened because the coherent green-gate condition is not met.
