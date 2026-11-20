# GULA-GULS-020 Test Evidence

Date: 2026-11-20  
Program: GULA-GULS-020  
Branch: `execution/gula-guls-020`  
Base revision: `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`

This document records exact commands and observed results. All commands were executed in the isolated clone at `/tmp/opencode/gula-guls-020`. No production database, deployment, or protected workspace was accessed.

## 1. Environment

| Item | Value |
|---|---|
| Isolated clone | `/tmp/opencode/gula-guls-020` |
| Primary Python | `python3.11` (system, pytest 9.1.1) |
| Verification Python | `/tmp/opencode/gula-guls-020-venv/bin/python` (3.12.13, pytest 9.2.0, ruff 0.16.10) |
| Frontend Node packages | Installed with `npm install --ignore-scripts --no-audit --no-fund` (608 packages) |
| Supported runtime | Python >= 3.12 (project `pyproject.toml`); 3.11 used for focused compatibility |
| Schema checker | `jsonschema` available in system Python 3.11; used only for one-off verification, not added as a project dependency |

## 2. Focused backend tests (Python 3.11)

Command:

```bash
PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization
```

Result:

```
67 passed, 1 warning in 1.22s
```

Warning: `StarletteDeprecationWarning` from `fastapi/testclient.py` regarding `httpx` with `starlette.testclient`; pre-existing dependency warning, not a GULS failure.

## 3. Focused backend tests (Python 3.12 verification venv)

Command:

```bash
PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization
```

Result:

```
67 passed, 1 warning in 1.17s
```

Per-file distribution:

| File | Tests |
|---|---:|
| `test_clinical_governance.py` | 6 |
| `test_delivery_api.py` | 10 |
| `test_existing_runtime_compat.py` | 2 |
| `test_pack_manager.py` | 20 |
| `test_preference_compat.py` | 2 |
| `test_registry_runtime.py` | 25 |

## 4. Legacy accessibility regression (Python 3.12)

Command:

```bash
PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/test_user_preferences.py --tb=short
```

Result:

```
5 passed, 1 warning in 84.43s
```

This confirms the shared-key compatibility fix (`AccessibilityResponse` ignores GULS keys; legacy PUT preserves `fallback_language` and `auto_download`) does not regress the existing accessibility API.

Note: the venv initially lacked `greenlet`; `pip install greenlet` (3.5.6) was required for SQLAlchemy asyncio imports in this regression file. Focused GULS tests do not import SQLAlchemy asyncio.

## 5. Static checks

Python compile (3.12):

```bash
PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m py_compile \
  backend/app/localization/*.py backend/app/routes/localization.py \
  backend/app/platform/i18n.py backend/app/routes/user_preferences.py \
  backend/app/factory.py tools/guls_sign_pack.py backend/tests/localization/*.py
```

Result: `py312_compile=PASS`.

Ruff:

```bash
/tmp/opencode/gula-guls-020-venv/bin/ruff check \
  backend/app/localization backend/app/routes/localization.py \
  backend/app/platform/i18n.py backend/app/routes/user_preferences.py \
  backend/app/factory.py backend/tests/localization tools/guls_sign_pack.py
```

Result: `All checks passed!` (0 errors after resolver-compliant fixes).

TypeScript typecheck:

```bash
cd frontend-v3 && npx tsc --noEmit -p tsconfig.json --pretty false
```

Result: exit 0, no diagnostics.

Frontend lint:

```bash
cd frontend-v3 && npm run lint
```

Result: exit 0, zero warnings (`eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`).

## 6. Focused frontend tests

Command:

```bash
cd frontend-v3
npx vitest run --passWithNoTests --exclude 'e2e/**' \
  src/guls/guls.test.ts src/i18n/mobileNavResources.test.ts
```

Result:

```
Test Files  2 passed (2)
     Tests  11 passed (11)
```

A Vite config notice is emitted (`configLoader: 'native'` unsupported features in `vitest.config.ts` and `vite.config.ts`); it is non-fatal and pre-existing.

## 7. Schema validation

Registry schema:

```bash
PYTHONPATH=backend python3.11 - <<'PY'
import json, pathlib, jsonschema
reg = json.loads(pathlib.Path('shared/guls/language_registry.json').read_text())
schema = json.loads(pathlib.Path('shared/guls/language_registry.schema.json').read_text())
jsonschema.validate(reg, schema)
print('registry_schema_validation=PASS languages=%d' % len(reg['languages']))
PY
```

Result: `registry_schema_validation=PASS languages=14`.

Pack schema (synthetic fixture manifest):

```
pack_schema_validation=PASS approval_status=synthetic_test_only
```

## 8. Full frontend suite and pre-existing failures

Command:

```bash
cd frontend-v3 && npm test
```

Result:

```
Test Files  1 failed | 16 passed (17)
     Tests  2 failed | 63 passed (65)
```

Failing tests:

```
FAIL  src/components/navigation/MobileBottomNav.test.tsx > MobileBottomNav > uses translated labels and marks a nested route as current
FAIL  src/components/navigation/MobileBottomNav.test.tsx > MobileBottomNav > announces an open menu state
```

Observed DOM: the button has `aria-label` from `t("mobileNav.more")` = `"More"` and `title` from `t("mobileNav.openAllSections")` = `"Open all sections"`. The accessible name is `"More"`; the test expects `"Open all sections"`.

Pre-existing determination:

- An attempted clean-HEAD extraction to `/tmp/opencode/gula-guls-020-baseline` via `git archive HEAD frontend-v3` failed with `fetch-pack: unexpected disconnect while reading sideband packet` / `fatal: early EOF` because the isolated clone is a partial clone and required blob fetches. The determination therefore relies on direct byte-identity against HEAD, which is sufficient.
- `git diff HEAD -- frontend-v3/src/components/navigation/MobileBottomNav.tsx` is empty.
- `git diff HEAD -- frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` is empty.
- The test mocks `react-i18next` locally with a fixed key-to-string map; it does not import the changed `src/i18n` modules.
- No Vitest/Vite config or test setup file differs from HEAD.
- Therefore the two failures reproduce from unmodified HEAD sources and are unrelated to GULS changes.

Gate posture: focused GULS tests and all static checks are green. Full frontend suite is red only on the pre-existing, file-identical MobileBottomNav accessible-name mismatch. This is recorded as a known baseline failure, not a GULS regression, and not fixed because modifying that component/test is outside this program's scope.

## 9. Adversarial and review-driven tests

| Test | Finding addressed |
|---|---|
| `test_preference_rejects_pending_language` | Blocked/unpublishable language must not be selectable |
| `test_legacy_accessibility_response_accepts_guls_keys` | Shared JSON key must not cause HTTP 500 in legacy endpoint |
| `test_retired_language_identifiers_are_normalized_instead_of_failing` | `ku`/`tk`/`syr` must not break legacy schema |
| `test_approved_pack_for_blocked_language_is_rejected` | `verify()`/`install()` must enforce registry governance, not only `download()` |
| `test_clinical_catalog_cannot_be_signed_without_clinical_approval` | L3/L4 clinical catalogs blocked in signed-pack path |
| `test_expected_hash_mismatch_is_rejected` | `expected_hash` must be honored |
| `test_install_recovers_from_stale_target_directory` | Partial `_write_pack` must not leave retry-blocking directories |
| `test_malformed_public_key_does_not_break_startup` | Malformed `GULS_PACK_PUBLIC_KEY_B64` fails closed without import crash |
| `test_registry_load_rejects_malformed_entries` | Registry loader validates structure without adding a dependency |
| `test_download_progress_resumes_from_byte_range` | Progress must advance and resume from byte range |
| `test_download_can_be_cancelled` | Cancellation must remove the download session |
| `test_unknown_language_is_not_ready` | Unknown language returns `404 LANGUAGE_NOT_FOUND`; pending returns `404 PACK_NOT_AVAILABLE` |
| `stableMessage` invalid-code test | Stable codes must match the uppercase pattern |
| Empty localized value test | Empty translations must fall back to English |

## 10. Protected workspace invariant

Rechecked at program end:

| Property | Expected | Observed |
|---|---|---|
| Branch | `remediate-security-001` | `remediate-security-001` |
| HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | `f478676b6fc375338648dde46fbf076c015a3f91` |
| Status manifest SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | unchanged |
| Worktrees | 6 | 6 |
| Stashes | 2 | 2 |

No change was made to the protected workspace.

## 11. Evidence limitations

- No production key, database, deployment, or registry authority was accessed.
- No human linguistic or clinical approval is claimed. Turkmen, Syriac, and all L4 clinical translations remain blocked.
- No signed production pack was built or published; only ephemeral test keys and synthetic fixtures were used.
- Web Service Worker/IndexedDB caching and mobile/desktop dynamic pack storage are not implemented and are not claimed as verified.
