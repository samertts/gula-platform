# GULA Extreme Adversarial Audit — Team A

> **Audit:** A6 — GULA Extreme Adversarial Audit - Team A: Dependency & Supply Chain + Infrastructure / Disaster Recovery
> **Team:** Team A (independent adversarial auditor)
> **Generated (UTC):** 2026-11-18
> **Target repository:** `/home/samertts/workspace/projects/gula-integration`
> **Branch:** `integration/gula-unification-v1`  **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
> **Sibling repository:** `/home/samertts/workspace/projects/gula-platform` @ `f478676b6fc375338648dde46fbf076c015a3f91` — treated READ-ONLY, not modified by this audit

## 0. Hard constraints observed

- **Source Git Config Db Writes:** NONE - only the three artifacts under GOVERNANCE/ADVERSARIAL_ASSURANCE/ were created
- **Git Add Commit Push:** NONE
- **Operational Db Access:** NONE
- **Network Access:** NONE
- **Package Installs:** NONE
- **Live Vulnerability Lookups:** NONE - local lockfiles/advisory files only
- **Secrets Read Or Reproduced:** NONE - .env existence/ignore status checked only, contents never read
- **Owner decisions unchanged:** HOLD, MPI REJECT, MP-001, ODR-001, ODR-002, ODR-003, ODR-004, D-020, D-021, ADR-A, ADR-B, ADR-C, ADR-D, ADR-E, ADR-F, ADR-G, ADR-H, ADR-I, ADR-J, AUD-02, AUD-07, AUD-16

## 1. Claim status (read this before any finding)

This audit is an **independent adversarial review**, not an acceptance authority.

- Audited work was awarded `INDEPENDENTLY VERIFIED`: **NO**
- Audited work was awarded `PRODUCTION READY`: **NO**
- Status vocabulary in force: `IMPLEMENTED, TESTED, INTEGRATED, INDEPENDENTLY VERIFIED, PRODUCTION READY, BLOCKED, NOT IMPLEMENTED`
- All immutable owner decisions remain unchanged: `HOLD, MPI REJECT, MP-001, ODR-001, ODR-002, ODR-003, ODR-004, D-020, D-021, ADR-A, ADR-B, ADR-C, ADR-D, ADR-E, ADR-F, ADR-G, ADR-H, ADR-I, ADR-J, AUD-02, AUD-07, AUD-16`

Findings below are status `DISCOVERED`. A `BLOCKED` or `NOT VERIFIED` label that appears
inside a finding's evidence/impact describes the *state of the evidence or the control*,
not a downgrade of the finding's own status. Recovery/DR claims are explicitly
`BLOCKED / NOT VERIFIED` and `RPO/RTO UNMEASURED`; this audit does not publish any number.

## 2. Scope, method and coverage

Method: static, read-only examination of on-disk manifests, lockfiles, container/compose/
CI/Helm/Kubernetes/Terraform configuration, local advisory artifacts and local git metadata
at the audited HEAD. No source, git, config, database, network or package-install operation
was performed. `.env` existence/ignore status was checked only; its contents were never read.

- Python manifests and lockfiles (backend/pyproject.toml, backend/uv.lock, backend/requirements*.txt, root pyproject.toml/requirements.txt, shared/pyproject.toml, edge_agent/nhop-platform/platform/hospital_desktop requirements, services/device_bridge/pyproject.toml)
- JS/TS manifests and lockfiles (19 package.json, 9 lockfiles incl. conflicting root pnpm-lock.yaml + package-lock.json)
- Container builds (15 Dockerfiles)
- Compose topologies (12 compose files incl. docker-compose.full.yml)
- CI/CD security gates (33 workflows: dependency-review, codeql x2, security-hardening, ci, nightly/trivy, deploy, canary, blue-green, rollback, auto-rollback, frontend-pwa, preview-deploy)
- Dependabot configuration (459 lines) and license/dependency-check configs
- SBOM artifacts and generators/validators
- Local advisory artifacts (.audit/*, security-audit/*, GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md)
- Kubernetes (37 YAML) and Helm (37 YAML) manifests
- Terraform (5 environments, 12 modules), Cloudflare, DigitalOcean, nginx/TLS configs
- Backup/DR scripts and GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md
- Observability/health surfaces (backend/app/main.py, routes/metrics.py, services/metrics_service.py, health_core/*)

## 3. Explicitly NOT SCANNED (no network)

Every item below is reported as **NOT SCANNED (no network)** and is never reported as clean:

- Live PyPI/npm/OSV/GHSA advisory lookup for current manifest versions
- Container registry image digest/tag resolution and runtime SBOM of built images
- Dependabot alert state (requires GitHub API)
- Branch-protection / required-check configuration (requires GitHub API)
- Live endpoint TLS posture, deployed K8s cluster state, and actual backup job execution

> Findings below are derived exclusively from on-disk files and local git metadata. Where a version could not be checked against a live advisory feed the report says NOT SCANNED (no network); it is never reported as clean.


### Dependency-specific coverage summary

- Python manifests reviewed: **13**
- JavaScript/TS manifests reviewed: **19**
  - with an adjacent lockfile: **8**
  - without an adjacent lockfile: **11**
  - JavaScript lockfiles on disk: **9** (includes conflicting root `pnpm-lock.yaml` + `package-lock.json`)
- Dockerfiles: **15**; Compose files: **12**; GitHub workflows: **33**

Provenance context at the audited HEAD: **209** untracked porcelain entries /
**472** individual untracked files, **109** modified
tracked files, **130** files in the HEAD diff (**+3779 / −2292**),
**144** untracked `GOVERNANCE/` files. Tracked files: **6514**.


## 4. Dependency & Supply Chain findings (10)

Severity breakdown for this domain: CRITICAL 1, HIGH 5,
MEDIUM 3, LOW 1.

### AUD-SUP-001 — Stale backend/uv.lock pins the pre-remediation vulnerable dependency set while the advisory report certifies only requirements-lock.txt

| Attribute | Value |
|---|---|
| Severity | CRITICAL |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- backend/uv.lock:131 certifi == 2026.7.22 (remediation floor 2026.10.18 at backend/requirements.txt:38)
- backend/uv.lock:436 dnspython == 2.8.0 (floor 2.9.2 at backend/requirements.txt:39)
- backend/uv.lock:710 idna == 3.18 (floor 3.20 at backend/requirements.txt:40)
- backend/uv.lock:728 joserfc == 1.7.4 (floor 1.7.6 at backend/requirements.txt:15)
- backend/uv.lock:838 pillow == 12.3.0 (floor 13.0.0 at backend/requirements.txt:19)
- backend/uv.lock:959 pyasn1 == 0.6.4 (floor 0.6.5 at backend/requirements.txt:41)
- backend/uv.lock:1414 urllib3 == 2.7.0 (floor 2.8.0 at backend/requirements.txt:42)
- backend/uv.lock:602 metadata still records joserfc specifier >=1.7.3; backend/uv.lock:604 pillow >=12.3.0; backend/pyproject.toml:19,25 now require >=1.7.6 / >=13.0.0
- GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md:9,20-25,51 limits scope to requirements.txt / requirements-lock.txt / pyproject.toml and explicitly names only requirements-lock.txt as scanned
- .github/workflows/security-hardening.yml:46-49 pip-audit matrix = backend/requirements-lock.txt, edge_agent/requirements.txt, nhop-platform/requirements.txt (uv.lock absent)

**Reproduction / falsification:** Static differential: compare each package version in backend/uv.lock against backend/requirements-lock.txt:1-70 and against the floors in backend/pyproject.toml:11-33 and backend/requirements.txt:1-43. Seven versions are below the recorded fix floors and the lock metadata itself records superseded specifiers, proving the lock was generated before remediation. Falsified only if uv.lock is regenerated and re-scanned; no network command was run in this audit.

**Root cause:** Three concurrent dependency representations (pyproject.toml, requirements-lock.txt, uv.lock) with no lock-consistency gate; .github/dependabot.yml contains no 'uv' ecosystem entry; the CI pip-audit matrix omits uv.lock.

**Impact:** Any uv-based sync/export path reinstalls the exact versions the local advisory report rates as 55 findings / 6 packages, including four CVSS 9.8 Pillow advisories. The 'VERIFIED - static scan clean' claim at GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md:6 is scope-limited and does not cover this tracked file.

**Recommended remediation:** Regenerate backend/uv.lock from the current backend/pyproject.toml; add `uv lock --check` (or equivalent lock-vs-manifest equality assertion) as a HARD CI gate; add backend/uv.lock to the pip-audit matrix; add a uv ecosystem entry to dependabot.yml; reconcile all backend dependency files through one canonical resolver.

**Alternatives considered:**

- Delete uv.lock if no supported workflow consumes it, after evidence-based confirmation (ADR-028 archive-first preference).
- Generate requirements-lock.txt and uv.lock from a single source in one scripted step; currently they are maintained by hand.

### AUD-SUP-002 — Eight production microservice images install completely unpinned Python packages at every build with no lockfile and no advisory gate

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- services/ai/Dockerfile:5 RUN pip install --no-cache-dir fastapi uvicorn[standard] requests pika prometheus-client pydantic
- services/autonomous_manager/Dockerfile:5 identical unpinned install
- services/lab/Dockerfile:5 unpinned fastapi/uvicorn/asyncpg/pika/prometheus-client/pydantic/passlib/bcrypt (only joserfc>=1.7.6 is floored)
- services/notification/Dockerfile:5, services/order/Dockerfile:5, services/patient/Dockerfile:5, services/result/Dockerfile:5, services/sample/Dockerfile:5 all unpinned
- services/device_bridge/Dockerfile:8 uses lower bounds only (fastapi>=0.115.0, uvicorn>=0.30.0, pydantic>=2.8.0, httpx>=0.27.0)
- .github/workflows/security-hardening.yml:46-49 audits none of these service dependency sets

**Reproduction / falsification:** Inspect the cited lines: no version specifier, no hash file, no adjacent requirements/lock file in those service directories, and no CI job that resolves or scans them. Two builds at different dates can therefore install different code. Falsified if each image is shown to resolve from a pinned, scanned manifest.

**Root cause:** Microservice Dockerfiles were authored as standalone examples and were never folded into the dependency governance applied to backend/ and frontend-v3.

**Impact:** Non-reproducible images, unreviewed upstream code entering the trust boundary on every rebuild, and an unbounded advisory surface that no local or CI scan covers.

**Recommended remediation:** Introduce one pinned, hash-verified requirements lock per service (or a shared service requirements lock), change installs to `pip install --require-hashes -r <lock>`, and add each lock to the pip-audit matrix.

**Alternatives considered:**

- Consolidate the eight services onto the backend base image so they inherit one governed dependency set.
- Use a single distroless multi-service image if service separation permits.

### AUD-SUP-003 — Material provenance gap: the audited HEAD has a large uncommitted surface and the dependency/DR evidence reports are untracked

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- git status --porcelain at HEAD 2206654d: 209 untracked entries, 109 modified tracked files, plus staged renames
- git ls-files --others --exclude-standard | wc -l = 472 individual untracked files
- git status --porcelain --ignored | grep -c '^!!' = 319 ignored files
- git diff --stat HEAD: 130 files changed, 3779 insertions(+), 2292 deletions(-)
- git ls-files | wc -l = 6514 tracked files vs 9679 files on disk (excluding .git and node_modules)
- GOVERNANCE files untracked: 144; specifically GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md and GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md are NOT tracked by git
- GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md:5 names HEAD `2827c1ff`, which is not the audited HEAD `2206654d`

**Reproduction / falsification:** Run the read-only git commands above on the audited worktree. Falsified only if the surface is committed and the evidence reports are tracked at the audited HEAD.

**Root cause:** Unification work was performed on a long-lived integration branch without per-change commits; evidence artifacts are written as loose files rather than versioned, content-addressed records.

**Impact:** The audit target is a moving tree. No commit-level provenance or attestation binds the source, the lockfiles, or the rehearsal evidence to a reviewable state; the DR evidence cannot be tied to the audited HEAD.

**Recommended remediation:** Freeze the integration surface into atomic, conventional commits; commit the dependency and DR evidence reports or move them to a content-addressed evidence store referenced by commit hash; re-run and re-date the DR rehearsal at the new HEAD.

**Alternatives considered:**

- Generate a signed manifest (file paths + SHA-256 + HEAD) covering the untracked surface as an interim provenance record.
- Adopt git notes or an append-only evidence registry instead of loose markdown reports.

### AUD-SUP-004 — SBOM is stale relative to declared floors, generator ignores lockfiles, and the default validator path does not exist

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- docs/sbom/latest.sbom.json creationInfo.created = 2026-07-18T11:46:21Z; SPDX packages include fastapi 0.110.0, fastapi 0.115.0, Pillow 10.4.0, cryptography 42.0.0
- backend/pyproject.toml:12,24 require fastapi>=0.139.2 and cryptography>=49.0.0; backend/requirements.txt:19 requires Pillow>=13.0.0
- scripts/generate_sbom.py:3-4,316,321-322 scans backend/requirements.txt and package.json files, not uv.lock / requirements-lock.txt / lockfiles
- scripts/validate-sbom.sh:29 SBOM_DIR defaults to ${REPO_ROOT}/reports/sbom; that directory does not exist on disk and /reports/ is gitignored at .gitignore
- config/security/license-config.yml reporting.generate_notices = true and notice_output THIRD-PARTY-NOTICES.md; that file is MISSING at repo root
- assessment/brain/sbom-backend.xml describes 'requirements line 15: Pillow>=10.4.0' - superseded

**Reproduction / falsification:** Parse docs/sbom/latest.sbom.json and compare component versionInfo values to current manifest floors; check existence of reports/sbom and THIRD-PARTY-NOTICES.md. Falsified if the SBOM is regenerated from resolved locks and the validator's default directory is populated.

**Root cause:** SBOM is generated from declared ranges rather than resolved locks and is not regenerated or validated as part of the release/dependency remediation flow.

**Impact:** The SBOM cannot support accurate vulnerability response, license attestation or incident scoping; the validator fails closed only by accident (missing directory), not by design.

**Recommended remediation:** Regenerate the SBOM from resolved lockfiles (uv.lock / requirements-lock.txt / package-lock.json), wire generation + `validate-sbom.sh --all` into CI with an existing SBOM_DIR, and produce the required THIRD-PARTY-NOTICES.md.

**Alternatives considered:**

- Adopt an SPDX/CycloneDX tool that consumes installed environments or lockfiles directly.
- Store the SBOM as a CI artifact tied to each image digest.

### AUD-SUP-005 — Contradictory license policy: licenses allowed by config/security/license-config.yml are denied by dependency review and SBOM validator

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- config/security/license-config.yml:26-29 allowed list includes LGPL-2.1-only, LGPL-2.1+, LGPL-3.0-only, LGPL-3.0+
- config/security/license-config.yml allowed list includes BSL-1.0
- .github/workflows/dependency-review.yml:24-28 deny-licenses includes LGPL-2.1-only, LGPL-3.0-only, BSL-1.0, BSL-1.0, RPL-1.1, RPL-1.5
- scripts/validate-sbom.sh:42-47 BLOCKED_LICENSES includes BSL-1.0 while ALLOWED_LICENSES at :36-40 includes LGPL-2.1-only / LGPL-3.0-only
- .github/workflows/security-hardening.yml:74 deny-licenses = GPL-3.0,AGPL-3.0 only (a third, different list)

**Reproduction / falsification:** Diff the four license lists. A package licensed LGPL-3.0-only passes config/security/license-config.yml but fails .github/workflows/dependency-review.yml:27. Falsified if a single authoritative list is referenced by all gates.

**Root cause:** License policy duplicated in four places with no single source of truth or test asserting equivalence.

**Impact:** Non-deterministic compliance verdicts; a dependency can be merged through one path and blocked in another; copyleft obligations may be accepted without the intended review.

**Recommended remediation:** Make config/security/license-config.yml the single source of truth; have dependency-review.yml, security-hardening.yml and validate-sbom.sh consume it; add a unit test that fails on drift.

**Alternatives considered:**

- Adopt a single allowlist at the organisation level and remove local overrides.
- Introduce an explicit, documented exception register rather than duplicating allowlists.

### AUD-SUP-006 — Images are built from mutable base tags with range-resolved, hash-free installs and a Python version that differs from the tested version

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- backend/Dockerfile:7 FROM python:3.14-slim AS builder; backend/Dockerfile:18 FROM python:3.14-slim; backend/Dockerfile:14 pip install ... -r requirements.txt (no --require-hashes)
- Dockerfile:5,10,13 same pattern; docker/Dockerfile:1,12 same pattern; all 15 Dockerfiles use python:3.14-slim without digest
- frontend-v3/Dockerfile:3 node:22.13-alpine, :13 nginx:1.28-alpine (no digest pin)
- .github/workflows/ci.yml:18 PYTHON_VERSION: "3.12"; .github/workflows/nightly.yml:20 PYTHON_VERSION: '3.12'; .github/workflows/security-hardening.yml:54 python-version: '3.12'
- backend/pyproject.toml:9 requires-python = ">=3.12"; root pyproject.toml:24 ruff target-version = "py314" and :50 mypy python_version = "3.14"

**Reproduction / falsification:** Inspect the FROM lines and install commands: no @sha256 digest and no --require-hashes anywhere. Compare Python 3.14 image tag to the 3.12 CI matrix. Falsified if images are digest-pinned, hash-verified and built/tested on the same interpreter.

**Root cause:** Base image and interpreter drift accumulated across the merged repositories; the build path uses requirements.txt ranges rather than a pinned manifest.

**Impact:** Two builds of the same commit can produce different runtime code; production executes Python 3.14 while the full test suite and security audit run on 3.12; no integrity verification of downloaded artifacts.

**Recommended remediation:** Pin all base images by digest, build production images from requirements-lock.txt (or uv.lock) with --require-hashes, and align the image interpreter with the CI/tested interpreter (3.12 per current CI).

**Alternatives considered:**

- Standardise on Python 3.14 across CI, mypy, ruff and tests if owner approves the toolchain change.
- Use a minimal distroless base with a digest-pinned build stage.

### AUD-SUP-007 — Deploy/build workflows fetch unpinned tooling and swallow install failures

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | MEDIUM |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- .github/workflows/frontend-pwa.yml:156 npm install -g vercel@latest
- .github/workflows/frontend-pwa.yml:205 npm install -g vercel@latest
- .github/workflows/formatting.yml:37 npm install --no-save --no-package-lock prettier
- .github/workflows/preview-deploy.yml:22 npm install --ignore-scripts 2>/dev/null || true
- .github/workflows/security-hardening.yml:56 python -m pip install ... pip-audit (unpinned scanner)

**Reproduction / falsification:** Read the cited workflow lines. `vercel@latest` is a mutable tag executed in a deploy workflow; `|| true` converts a failed install into a successful step. Falsified if tools are pinned by version/digest and failures propagate.

**Root cause:** Convenience installs were added without applying the repository's own pinning rule for third-party actions (most actions are SHA-pinned).

**Impact:** Deploy-time arbitrary code execution risk from a mutable upstream package; failed dependency installation can be silently ignored, producing an unverifiable build.

**Recommended remediation:** Pin vercel/prettier/pip-audit to exact versions (and verify integrity where possible), replace `npm install` with `npm ci`, remove `|| true`, and use a dedicated pinned setup action.

**Alternatives considered:**

- Run deploy tooling in a digest-pinned container image.
- Vendor the CLI version used by the release into the repository.

### AUD-SUP-008 — Dependency-update and scanning automation has large blind spots; frontend declares pnpm scripts but ships only an npm lockfile

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- .github/dependabot.yml (459 lines) has no 'uv' ecosystem entry and no entries for /shared/, /services/device_bridge/ (pip), /mobile-expo/, /contracts/sdk/typescript/, /platform/ npm apps or the root npm workspace
- 11 of 19 package.json manifests have no adjacent lockfile, e.g. packages/uap/package.json, platform/ai/package.json, platform/apps/citizen|doctor|hospital|laboratory|ministry|nurse|radiology/package.json, platform/update/package.json, mobile-expo/vendor/image-size/package.json
- Both pnpm-lock.yaml and package-lock.json exist at repository root for the same package.json
- frontend-v3/package.json:21-31 check/test scripts call pnpm; frontend-v3 contains only package-lock.json and no pnpm-lock.yaml
- .github/workflows/ci.yml:198 and frontend-v3/Dockerfile:8 use npm ci
- .github/workflows/mobile-expo.yml:56 is the only workflow with npm audit; frontend-v3 has no npm audit gate

**Reproduction / falsification:** Grep dependabot.yml for 'uv' (zero hits), enumerate package.json vs adjacent lockfiles, and compare frontend-v3 scripts to its lockfile. Falsified if all manifests are covered by update and scan automation with a single package manager each.

**Root cause:** Partial unification: multiple package managers and inherited app trees were merged without harmonising update automation.

**Impact:** Dependency drift is structurally guaranteed (see AUD-SUP-001); unmanaged manifests receive no automated fixes or advisory checks; mixed npm/pnpm instructions make local and CI resolution differ.

**Recommended remediation:** Choose one package manager per workspace, generate/commit the missing lockfiles, extend dependabot to every manifest including uv, and run npm/pnpm audit plus pip-audit across all managed manifests in CI.

**Alternatives considered:**

- Adopt a monorepo-wide lockfile if the workspace tooling supports it.
- Generate lockfiles in CI and fail if the committed copy differs.

### AUD-SUP-009 — Local advisory artifacts are stale or internally inconsistent and cannot clear the current manifests

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- .audit/pip-audit.json records joserfc 1.7.4, pillow 12.3.0, urllib3 2.7.0, certifi 2026.7.22, pyasn1 0.6.4 each with "vulns": []
- GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md:67-73 rates those exact versions as 42 pillow advisories (4 CRITICAL), 2 joserfc, 3 urllib3, 1 certifi, 4 pyasn1, 2 dnspython
- security-audit/trivy.json records react-router@6.30.4 / react-router-dom@6.30.4 with CVE-2026-53666, CVE-2026-53669, CVE-2026-53668 (all MEDIUM)
- frontend-v3/package.json:38 declares react-router-dom ^7.18.2, which is not covered by that local artifact
- .audit/npm-audit-production.json metadata.vulnerabilities.total = 2 HIGH; .audit/npm-audit-production-after.json total = 0; neither artifact identifies the manifest scanned

**Reproduction / falsification:** Parse the cited local JSON artifacts and compare their installed versions to current manifest declarations. Falsified if each artifact is shown to cover the exact current lockfile with a dated, reproducible command.

**Root cause:** Advisory outputs are stored as undated snapshots with no manifest hash or command provenance, and are reused as evidence after dependencies change.

**Impact:** A reader can wrongly treat `vulns: []` as a clean result for vulnerable versions. Current manifest versions are NOT SCANNED (no network in this audit), so no clean claim is permitted.

**Recommended remediation:** Require every advisory artifact to record timestamp, manifest path + SHA-256, tool version and full command; re-scan current locks in CI; treat mismatched artifacts as invalid evidence.

**Alternatives considered:**

- Delete superseded artifacts after archiving them with provenance headers (ADR-028 archive-first).
- Store scan results as GitHub Actions artifacts attached to a specific run.

### AUD-SUP-010 — Unexplained transitive package 'annotated-doc 0.0.5' present in the resolved dependency graph with no declaration or local advisory evidence

| Attribute | Value |
|---|---|
| Severity | LOW |
| Likelihood | LOW |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- backend/uv.lock:20-21 name = "annotated-doc", version = "0.0.5"
- backend/uv.lock:485 { name = "annotated-doc" } listed as a dependency of a resolved package
- .audit/pip-audit.json and .audit/pip_audit_backend.json both list annotated-doc 0.0.5 with "vulns": []
- No manifest declares annotated-doc; backend/requirements-lock.txt:2 declares annotated-types==0.7.0 instead

**Reproduction / falsification:** Search all manifests for 'annotated-doc' (zero declarations) and inspect its lock entry. The name is not among declared direct requirements and is absent from the pinned requirements lock. Falsified if a declared, reviewed upstream dependency legitimately requires it and its provenance is documented.

**Root cause:** Resolved graph was accepted without reviewing newly introduced transitive packages against an allowlist; no package-name/provenance verification step exists.

**Impact:** Potential typo-confusion/provenance risk. This audit has NO local advisory evidence that the package is malicious and NO network access to verify it; the finding is a provenance question, not a compromise claim.

**Recommended remediation:** Identify the requiring package, verify publisher/provenance and source distribution, add a package-provenance allowlist to dependency review, and remove/replace if not justifiable.

**Alternatives considered:**

- Enforce a dependency-approval policy requiring review of every new transitive package (docs/architecture/DEPENDENCY_APPROVAL_POLICY.md already exists).
- Pin transitive packages by hash from a vetted internal mirror.



## 5. Findings summary table

| ID | Severity | Likelihood | Status | Owner-gated | Title |
|---|---|---|---|---|---|
| AUD-SUP-001 | CRITICAL | HIGH | DISCOVERED | yes | Stale backend/uv.lock pins the pre-remediation vulnerable dependency set while the advisory report certifies only requirements-lock.txt |
| AUD-SUP-002 | HIGH | HIGH | DISCOVERED | yes | Eight production microservice images install completely unpinned Python packages at every build with no lockfile and no advisory gate |
| AUD-SUP-003 | HIGH | HIGH | DISCOVERED | yes | Material provenance gap: the audited HEAD has a large uncommitted surface and the dependency/DR evidence reports are untracked |
| AUD-SUP-004 | HIGH | HIGH | DISCOVERED | yes | SBOM is stale relative to declared floors, generator ignores lockfiles, and the default validator path does not exist |
| AUD-SUP-005 | MEDIUM | HIGH | DISCOVERED | yes | Contradictory license policy: licenses allowed by config/security/license-config.yml are denied by dependency review and SBOM validator |
| AUD-SUP-006 | HIGH | HIGH | DISCOVERED | yes | Images are built from mutable base tags with range-resolved, hash-free installs and a Python version that differs from the tested version |
| AUD-SUP-007 | HIGH | MEDIUM | DISCOVERED | yes | Deploy/build workflows fetch unpinned tooling and swallow install failures |
| AUD-SUP-008 | MEDIUM | HIGH | DISCOVERED | yes | Dependency-update and scanning automation has large blind spots; frontend declares pnpm scripts but ships only an npm lockfile |
| AUD-SUP-009 | MEDIUM | HIGH | DISCOVERED | yes | Local advisory artifacts are stale or internally inconsistent and cannot clear the current manifests |
| AUD-SUP-010 | LOW | LOW | DISCOVERED | yes | Unexplained transitive package 'annotated-doc 0.0.5' present in the resolved dependency graph with no declaration or local advisory evidence |

## 6. Domain conclusion

The dependency and supply-chain posture of the audited tree is **NOT INDEPENDENTLY VERIFIED**.
A stale, tracked `backend/uv.lock` (AUD-SUP-001) reintroduces the exact versions the local
advisory report rates as vulnerable, while the clean-scan report is scoped only to
`requirements-lock.txt` and is itself untracked (AUD-SUP-003). Eight service images install
unpinned packages at build time (AUD-SUP-002), base images are mutable and hash-free
(AUD-SUP-006), the SBOM is stale and its validator points at a non-existent directory
(AUD-SUP-004), and update/scan automation has large blind spots (AUD-SUP-008). Current
manifest versions are **NOT SCANNED (no network)**; none is claimed clean.

**Release recommendation:** Maintain HOLD. Remediate AUD-SUP-001 and AUD-INF-001 first; neither dependency security nor disaster recovery is independently verified.

No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded. Remediation and any
change to an immutable owner decision are owner-gated and out of scope for this audit.
