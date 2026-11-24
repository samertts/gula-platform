# Final Report 05 — Client Integration (WS-E) + F-04 remediation

**Report ID:** PR-FINAL-05 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** HOLD / REJECT unchanged. Development evidence only. Read-only inspection of client trees; **no client app tree was modified**.

## 1. Classification

| Deliverable | Classification | Basis |
|---|---|---|
| Manifest validation, layer-status derivation, fail-closed claim guards | **VERIFIED** | 30 focused tests incl. new caller-observation regressions |
| Client manifests + declarative auth boundaries + offline/conflict/RTL-A11y contracts | **VERIFIED (contract-level)** | Static/manifest evidence only; no running client |
| WEB / Android / Flutter / Desktop / Expo platform implementations | **BLOCKED** | Projects/layers present but `implementation_status` blocked; no adapter bound; `end_to_end_verified = False` |
| iOS platform | **NOT IMPLEMENTED** | Xcode project absent from checkout — reported, not fabricated |
| True end-to-end client↔backend verification | **NOT IMPLEMENTED** | No running client/backend integration; owner-gated environment |

Overall workstream classification: **PARTIALLY VERIFIED** — contracts fail closed and are verified; real platforms remain BLOCKED/NOT IMPLEMENTED by design.

## 2. The MEDIUM finding — F-04

**Finding (`ADVERSARIAL_REVIEW_CORRECTNESS.md` §F-04):** `validate_all_manifests(manifests, observations, *, repo_root)` silently **ignored** its `observations` argument per manifest — it called `validate_manifest(manifest, repo_root=repo_root)` without `observation=`, so every manifest was validated against the module-global default filesystem observation. A caller supplying a materially different scenario observation got identical (clean) errors.

**Fix (`client_integration/validators.py`):**
- Replaced the unused `observed_platforms` set with an `observations_by_platform` map.
- Each manifest is validated with `validate_manifest(manifest, observation=observation, repo_root=repo_root)`, using the caller-supplied observation matched by `.platform`.
- A missing observation emits `NO_OBSERVATION_FOR_PLATFORM` **exactly once** and still validates against the recorded default observation (historical fail-closed fallback), so no caller scenario can be silently masked by defaulting.
- `DUPLICATE_PLATFORM_MANIFEST` preserved; no error code duplicated. Default call path remains byte-for-byte equivalent.

## 3. Regression tests added (strict, no skips)

In `test_client_integration_manifests.py`:
- A materially different custom WEB observation (`project_present=False`, all layers `ABSENT`) now produces `LAYER_STATUS_MISMATCH` and `ABSENT_PROJECT_WITH_PRESENT_LAYER` while the default run does not, scoped only to WEB.
- Missing observations yield `NO_OBSERVATION_FOR_PLATFORM` exactly once (partial, empty and duplicate-manifest scenarios).
- The default run still returns the clean result shape as before.

`test_client_integration_guards.py` was reviewed but required no change.

## 4. Files changed (this cycle)

`backend/app/health_core/client_integration/validators.py`, `backend/tests/health_core/test_client_integration_manifests.py`.

## 5. Verification

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_client_integration_manifests.py \
  tests/health_core/test_client_integration_guards.py -q --tb=short
# 30 passed, 1 warning in 0.64s   (manifests 25 + guards 5)
```
Ruff: `All checks passed!`. Demo output confirms all six clients fail closed: `end-to-end claims -> none (contracts only; absent layers NOT IMPLEMENTED)`.

## 6. Residual / blocked

- All real client platforms remain BLOCKED/NOT IMPLEMENTED; the demo reports `web/android/flutter/desktop/expo: blocked`, `ios: not_implemented`.
- No client app tree modified, no adapter bound, no `end_to_end_verified` claim. These are deliberate, disclosed limitations — not defects to be silently "fixed".

**End of final report 05.**
