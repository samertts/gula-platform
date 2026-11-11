# IA-046 — the device bridge has no CI coverage, and the patch that would give it one

**STATUS: DISCOVERED, REPRODUCED. The fix is PREPARED, NOT APPLIED** — CLAUDE.md
lists "CI pipeline modifications (`.github/workflows/`)" under *Requires human
approval*, so the job below is written, reproduced locally, and left for someone
with that authority to apply.

## What is actually true today

Measured against every file in `.github/workflows/` (30 workflows):

| layer | covers `services/device_bridge`? | evidence |
|---|---|---|
| `ci.yml` → `syntax-gate` → "Check service Python syntax" | **yes**, `compile()` only | iterates `['services', 'nhop-platform', 'edge_agent', 'shared']` |
| `ci.yml` → `syntax-gate` → flake8 | no | `flake8 backend/app/ --select=E9,F ...` |
| `ci.yml` → `test` | no | `python -m pytest tests/` inside `backend/` only |
| `ci.yml` → `migration-check`, `data-preservation-gate`, `security-scan` | no | all scoped to `backend/` |
| any image build / GHCR push | **no such job exists** | `ci.yml` declares `REGISTRY: ghcr.io` at line 22 and no job consumes it; `grep -n "ghcr.io\|build-push-action\|matrix" ci.yml release.yml` returns only the two `REGISTRY:` lines |
| `grep -ln "device_bridge\|device-bridge" .github/workflows/*.yml` | **no match in any workflow** | — |

So the only gate this service passes is "the files parse".

**A correction to the IA-044 commit message**, which said the broken image was
one "CI builds and pushes to GHCR": it is not. No workflow builds it. The
defect IA-044 fixed was real — the import failed under the image's module path,
so the documented `docker compose --profile device-bridge up device-bridge`
could not come up — but it never reached a registry, because nothing publishes
it. CLAUDE.md's description of a `build-and-push` job with "a matrix of 8 images
(backend + 7 microservices) to GHCR" does not match `ci.yml` as it stands.

## Why it was absent — classified

Not a configuration impossibility, and not an architectural exclusion:

1. **Accidental omission at the test layer.** The `test` job hardcodes
   `backend/`. Twelve test modules under `services/device_bridge/tests/` were
   never collected by anything.
2. **The suite could not have run in CI before IA-044.** Four modules imported
   `backend.app._compat`, and `pyproject.toml` sets `pythonpath = ["."]`, so a
   job that checked out the repo and ran pytest from the service directory would
   have failed at collection. Every local run masked this by putting the
   repository root on `PYTHONPATH`. A CI job added before IA-044 would have been
   red on arrival, which is a plausible reason one was never kept.
3. **Two modules were uncollectable for an unrelated reason** — they imported a
   `DEFAULT_API_KEY` removed from `app.security.auth` — and that went unnoticed
   precisely because no job ran them (fixed in IA-039's commit).

Both blockers are now gone. Verified locally, with only the service directory
importable, which is what a CI job would have:

```
$ cd services/device_bridge
$ env -u PYTHONPATH LABLINK_API_KEY=x python3 -m pytest tests/ -q
61 passed
```

`61 passed` locally is **not** evidence that CI passes. It is evidence that the
precondition CI needs — a self-contained suite — now holds.

## The prepared patch

Append to `.github/workflows/ci.yml`. It mirrors the existing jobs' pinned
action SHAs and `needs: [syntax-gate]` dependency, adds no services (the suite
needs no database), and installs only what the suite imports.

```yaml
  device-bridge:
    name: Device Bridge (LabLink-Core)
    runs-on: ubuntu-latest
    needs: [syntax-gate]
    timeout-minutes: 10
    defaults:
      run:
        working-directory: services/device_bridge
    env:
      # app/security/auth.py reads this; with it unset every authenticated
      # endpoint raises SystemExit inside the request and answers 500.
      LABLINK_API_KEY: ci-device-bridge-key
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install "fastapi>=0.115.0" "uvicorn>=0.30.0" "pydantic>=2.8.0" \
                      "httpx>=0.27.0" "pyserial>=3.5" pytest pytest-timeout
      - name: Lint
        run: |
          pip install flake8
          flake8 app/ tests/ --select=E9,F --ignore=F401,F841 --count
      - name: Tests
        # No PYTHONPATH: pyproject sets pythonpath = ["."], and the suite must
        # pass with only its own tree importable — that is exactly the module
        # path the Docker image has, and IA-044 was a crash that only this
        # condition exposes.
        run: python -m pytest tests/ -q --timeout=60
      - name: Image builds and the app imports inside it
        # IA-044: the Dockerfile copies only app/, so an import that reaches a
        # sibling tree breaks the image and nothing else catches it.
        run: |
          docker build -t gula-device-bridge:ci .
          docker run --rm -e LABLINK_API_KEY=ci-device-bridge-key \
            gula-device-bridge:ci python -c "import app.main; print('import OK')"
```

### Expected result on this commit

- **Lint** — passes; `flake8 --select=E9,F821` is clean locally over `app/` and
  `tests/`.
- **Tests** — `61 passed`.
- **Image builds and the app imports inside it** — this step is the one with
  real uncertainty, and it is deliberately included rather than omitted. No
  Docker daemon is available in this environment, so neither the build nor the
  in-image import has been executed anywhere. It may fail on the `pyserial`
  line: `app/connectors/base.py` does `from serial import Serial` (lazy, so it
  breaks on first serial connection rather than at import), the package is now
  declared in `pyproject.toml`, and the **Dockerfile's explicit `pip install`
  list still omits it**. The in-image `import app.main` does not touch that
  import, so this step should pass; opening a serial analyzer in a real
  deployment would not. Correcting the Dockerfile is a one-line change that
  needs a build to verify.

### Rollback

Delete the `device-bridge` job. It is additive: no existing job's definition,
scope or dependency changes, and nothing else `needs:` it.

### Residual gap this job does NOT close

It runs the suite and builds the image. It does not start the compose profile,
exercise the healthcheck, or test against a real GULA backend — and per IA-041
the forward contract cannot succeed, so an end-to-end job would be red for a
reason no CI change can fix.
