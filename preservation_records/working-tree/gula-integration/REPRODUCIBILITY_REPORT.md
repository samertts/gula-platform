# Reproducibility Report

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19; pinned interpreter `gula-platform/backend/.venv/bin/python` (Python 3.12.13).
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. No `PRODUCTION READY` awarded.

## 1. This execution — `TESTED` (test reproducibility)

| Item | Evidence |
|---|---|
| Interpreter / env | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`, Python 3.12.13 |
| Focused step-up suite re-runnable | **37 passed / 1 warning / EXIT=0** (repeat executions of the focused suite produced stable counts) |
| Full-suite chain | first run `4973 passed/1 failed` (benchmark timing flake); clean re-run `4974 passed/27 skipped/EXIT=0 (17m09s)`; **final current tree `4984 passed/27 skipped/203 warnings/EXIT=0 (15m04s)`** — `/tmp/opencode/step_up_final_full_suite.log` |
| Flake classification | `test_cosine_similarity_throughput` failed once at `1680/s < 2000/s`; three isolation runs passed at `7796/s`, `3885/s`, `5992/s`; assertion **not** weakened |
| Ruff | clean `EXIT=0` on all changed scope |
| Boot / OpenAPI | `app.main.app` boots (`ENV=test`); **1815 paths / 132 route objects**; step-up endpoint present with body `code`+`method` (`required=[code]`); artifact `/tmp/opencode/team_c_openapi_probe.py`. Bare `create_app()` = 1808/125 (7 integration routes added in `app.main`). |
| Migration graph | single head `20261119_0001`, 98-revision chain |

## 2. Prior dependency reproducibility evidence (reported, not re-run this session)

`GOVERNANCE/EXECUTION_LEDGER.md` records:
- `uv 0.11.26 pip compile requirements.txt … --python-platform linux --python-version 3.12` —
  exit 0, **72 pins**, byte-identically reproducible across two runs.
- `npm ci` (frontend-v3) — exit 0, 609 packages reproducible from lockfile.
- Lock audit, fresh-resolution audit and installed-set audit all exit 0 ("No known vulnerabilities found").
- 33/33 behavior-only compatibility tests pass on both old and new dependency sets.

## 3. Gaps — `BLOCKED`

Clean-room rebuild from an empty environment, Docker image build, CI pipeline execution, health
checks, and frontend `tsc`/ESLint/Vite re-run were **not** executed this session. No CI result is
claimed. Two prior `pip` wheel-download attempts failed at the network layer (throttling) and are
recorded as `BLOCKED`, not as a resolution failure.

**Final decision:** Python test reproducibility `TESTED`; dependency-resolution evidence historical;
clean-environment reproducibility and CI `BLOCKED`. No production claim.
