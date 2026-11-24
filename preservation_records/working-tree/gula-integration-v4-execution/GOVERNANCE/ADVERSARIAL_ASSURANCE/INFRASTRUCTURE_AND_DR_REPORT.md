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


### Infrastructure-specific coverage summary

- Container builds: **15** Dockerfiles; Compose topologies: **12** files
- Kubernetes: **37** YAML files; Helm: **37** YAML files
- Terraform: 5 environments / 12 modules; Cloudflare, DigitalOcean, nginx/TLS configuration
- Backup/DR scripts and `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md` (untracked, different HEAD)
- Observability/health surfaces: `backend/app/main.py`, `routes/metrics.py`,
  `services/metrics_service.py`, `health_core/*`
- CI/CD deploy/canary/rollback workflows among **33** total workflows


## 4. Infrastructure & Disaster Recovery findings (10)

Severity breakdown for this domain: CRITICAL 0, HIGH 5,
MEDIUM 4, LOW 1.

### AUD-INF-001 — scripts/validate-restore.sh can return PASS and exit 0 even when pg_restore fails

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- scripts/validate-restore.sh:2 set -euo pipefail
- scripts/validate-restore.sh:27 pg_restore -d "$DB_NAME" /tmp/restore.dump 2>&1 | tee -a "$LOG_FILE" || true
- scripts/validate-restore.sh:31-35,59-68,71-73 psql ... 2>/dev/null discards all query errors
- scripts/validate-restore.sh:76 VALIDATION_RESULT="PASS"
- scripts/validate-restore.sh:77-84 only greps for "CHAIN BROKEN" and uppercase "ERROR"; pg_restore reports failures in lowercase 'error:' form
- scripts/validate-restore.sh:91 exit $([ "$VALIDATION_RESULT" = "PASS" ] && echo 0 || echo 1)

**Reproduction / falsification:** Static control-flow falsification: supply a corrupt or truncated dump. pg_restore exits non-zero, but the pipeline's `|| true` forces step success; subsequent psql queries fail with stderr discarded; the summary grep never sees uppercase ERROR; VALIDATION_RESULT stays PASS and the script exits 0. No database was touched in this audit. Falsified if pg_restore failure is propagated and structural checks require non-empty expected data.

**Root cause:** Error suppression (`|| true`, `2>/dev/null`) combined with a substring-based verdict instead of verifying restore exit status and expected state.

**Impact:** A backup that cannot be restored can be labelled validated. This is false assurance in the control intended to prove recoverability, and it directly undermines any DR claim.

**Recommended remediation:** Remove `|| true` from pg_restore; use `set -o pipefail` with explicit status capture; compare expected table counts/checksums rather than grepping text; ensure any query failure fails the script; add a negative test with a corrupt dump.

**Alternatives considered:**

- Use `pg_restore --exit-on-error` plus a dedicated disposable database and schema/data fingerprint comparison.
- Replace the script with a tested restore harness that emits structured pass/fail JSON.

### AUD-INF-002 — No restore/PITR drill and no measured RPO/RTO; the only rehearsal report is untracked and pinned to a different HEAD

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md:5 Date 2026-11-17 and HEAD `2827c1ff` (audited HEAD is 2206654d); file is untracked
- GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md:288 release criterion MIG-EXISTING = NOT MET
- GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md:398 strict-schema suite 753 passed / 119 failed / 0 skipped (exit 1)
- GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md:441-443 strict suite not passing; T1-T4 conclusions scoped to disposable clones
- GOVERNANCE/STABILIZATION_PHASE_L_M_N_ASSESSMENT.md:94-98 RPO/RTO UNMEASURED / NOT VERIFIED; prior 'RPO 1hr / RTO 4hr' quoted only as an unadopted claim
- GOVERNANCE/STABILIZATION_PHASE_L_M_N_ASSESSMENT.md:110 W-062 BLOCKED / NOT VERIFIED; no drill, no script executed, no number published
- GOVERNANCE/GECS/WORK_REGISTRY.md:62 W-034 rollback/restore drill + RPO/RTO measurement = NOT_STARTED
- GOVERNANCE/GECS/BLOCKER_REGISTRY.md:41 B-016 OPEN - RPO/RTO unmeasured
- GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:35 'No restore/PITR drill; RPO/RTO UNMEASURED'

**Reproduction / falsification:** No dated drill artifact with end-to-end restore timing or WAL-age measurement exists in the audited tree; the available report is a migration rehearsal on disposable clones, not a backup/restore drill. Falsified by a dated, reproducible drill record at the audited HEAD with measured RPO and RTO.

**Root cause:** Recovery work stopped at policy and script existence (D-004 approved, scripts present); the operational drill requires separate authorisation (W-034) that has not been granted.

**Impact:** Recovery objective is unknown. No availability or data-loss guarantee can be made. Any RTO/RPO number would be fabricated and is explicitly prohibited by owner decision.

**Recommended remediation:** Execute the owner-gated W-034 drill on disposable clones only: restore the latest backup, verify schema/data fingerprints, measure wall-clock restore time and WAL age, record date/HEAD/tool versions, and publish measured values or retain the literal string UNMEASURED.

**Alternatives considered:**

- Retain UNMEASURED and keep release status HOLD (immutable owner decision).
- Use a cloud-native snapshot restore test in an isolated account if authorised, with cost analysis under the free/self-hosted-first constitution.

### AUD-INF-003 — Rollback is manual-only despite the 'auto-rollback' name; canary has no error-rate/latency gate and ignores its declared traffic input

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- .github/workflows/auto-rollback.yml:2-13 trigger is `workflow_dispatch` only; no workflow_run, repository_dispatch or Alertmanager webhook trigger exists
- .github/workflows/auto-rollback.yml:19 default reason string 'Auto-rollback triggered by monitoring alert' despite manual-only trigger
- .github/workflows/canary-deploy.yml:9-11 declares input `canary_percent` (10-50) but the value is never referenced in any step
- .github/workflows/canary-deploy.yml:49-66 hardcodes 10%/90% and uses `|| true` / `|| echo "TrafficSplit not available"`
- .github/workflows/canary-deploy.yml:76-78,100-102 promotion decision is `curl -sf /health` only; no error-rate, latency or business-metric threshold
- .github/workflows/canary-deploy.yml:57 kubectl set image ... || true swallows deployment failure

**Reproduction / falsification:** Grep the workflow triggers and inputs: no automated alert trigger; canary_percent has exactly one occurrence (its declaration); the only health signal is an HTTP 200 from /health; several failures are swallowed. Falsified if an alert-driven trigger and SLO-based analysis gate are present and inputs are honoured.

**Root cause:** Workflows were authored as manual operator runbooks and named as if they were automated safety mechanisms.

**Impact:** There is no automatic rollback on production signal degradation, and canary promotion can proceed while error rates are elevated. Recovery claims based on these workflows are false assurance.

**Recommended remediation:** Add an Alertmanager/webhook or workflow_run trigger with explicit authorisation, implement SLO-based canary analysis (error rate + latency) with automatic abort, honour `canary_percent`, and remove failure-swallowing `|| true` on traffic-changing steps.

**Alternatives considered:**

- Rename the workflow to `manual-rollback.yml` to make the control honest if automation is not authorised.
- Use a digest-pinned Argo Rollouts/Kraken analysis template rather than bespoke shell loops.

### AUD-INF-004 — Compose configuration allows empty signing secrets and ships a development-mode Vault bound to all interfaces

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | MEDIUM |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- docker-compose.yml:114 comment 'No hardcoded fallback - SECRET_KEY must be set in .env' followed by :115 `SECRET_KEY: ${SECRET_KEY:-}` (empty default)
- docker-compose.yml:214-216 same empty default for REFRESH_TOKEN_SECRET and ENCRYPTION_KEY in the worker service
- docker-compose.yml:217-220 additional empty defaults for NID_HMAC_KEY, AUDIT_ANCHOR_KEY, DEVICE_HMAC_KEY
- docker-compose.full.yml:414-421 Vault `command: vault server -dev -dev-root-token-id=${VAULT_TOKEN:?...}` with comment 'Dev mode is INSECURE - data is in-memory only'
- docker-compose.full.yml:424-428 VAULT_DEV_LISTEN_ADDRESS 0.0.0.0:8200 and ports '8200:8200'
- docker-compose.full.yml:719 uses the stricter `${SECRET_KEY:?SECRET_KEY must be set in .env}` form, proving the safer pattern is known

**Reproduction / falsification:** Start a configuration resolution with the named variables unset: `${VAR:-}` expands to empty rather than failing. The full compose file explicitly declares the Vault mode insecure. Falsified if all secret variables use `:?` and the Vault service runs in server mode with auto-unseal.

**Root cause:** Two generations of compose configuration coexist; the base/worker files use permissive expansion while the full file uses fail-fast expansion.

**Impact:** Services may boot with empty cryptographic keys, weakening token signing/encryption/audit anchoring. The dev Vault stores secrets only in memory, is rooted by a token from .env, and is reachable on every host interface on port 8200.

**Recommended remediation:** Replace all `${VAR:-}` secret expansions with `${VAR:?...}`; remove dev-mode Vault from production compose and use server mode with auto-unseal and loopback-bound port; validate the resolved configuration in CI without printing values.

**Alternatives considered:**

- Use External Secrets Operator with k8s Secrets (k8s/base/secrets.yaml already declares this intent).
- Use a self-hosted Vault with file/KMS auto-unseal per the free/self-hosted-first policy.

### AUD-INF-005 — Production compose template binds admin, monitoring and data-plane services to all host interfaces

| Attribute | Value |
|---|---|
| Severity | HIGH |
| Likelihood | MEDIUM |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- docker-compose.full.yml:174 26379:26379 (Redis Sentinel); :191-192 8123 and 9001:9000 (ClickHouse/MinIO console)
- docker-compose.full.yml:283-284 9092:9092 and 9101:9101 (Kafka); :305 11434:11434 (Ollama)
- docker-compose.full.yml:329 9000:9000 (MinIO); :355-356 9003:9000 and 9002:9002
- docker-compose.full.yml:382 9100:9100 (node exporter); :405 8081:8080 (Keycloak); :428 8200:8200 (Vault)
- docker-compose.full.yml:455 9090:9090 (Prometheus); :471 3000:3000 (Grafana); :487 3100:3100 (Loki); :513-516 16686/14268/4317/4318 (Jaeger/OTLP)
- docker-compose.full.yml:564-588 service ports 8001-8006 and 8010 published on all interfaces
- By contrast docker-compose.full.yml:529-530 and docker-compose.demo.yml:86 correctly use 127.0.0.1 bindings for nginx/demo

**Reproduction / falsification:** Read the port mappings: two-component forms bind 0.0.0.0; the repository itself demonstrates the loopback form elsewhere. Falsified if all non-edge services are loopback-bound or placed on an internal-only network.

**Root cause:** Local-development port publishing was carried into a file named 'full' without a network-boundary review.

**Impact:** Monitoring consoles, admin UIs, model inference, message brokers and stores are directly reachable from the host network, bypassing the nginx/TLS boundary and any application authentication not enforced by those services.

**Recommended remediation:** Bind every non-edge port to 127.0.0.1 or remove host publication in favour of an internal compose network; expose only the TLS-terminating gateway; publish a network-boundary matrix and verify with a port scan in an isolated environment.

**Alternatives considered:**

- Place internal services in a compose network with `internal: true` and reach them via a bastion.
- Keep the current file explicitly labelled development-only and create a separate hardened production compose.

### AUD-INF-006 — Container and workload hardening is inconsistent: frontend image runs as root, Helm Postgres pod sets runAsNonRoot=false, Redis uses ephemeral storage

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- frontend-v3/Dockerfile:13-23 runtime stage has no USER directive; :15 comment claims 'unprivileged nginx user where supported'
- k8s/base/frontend/deployment.yaml:21-22 and helm/gula-platform/templates/frontend/deployment.yaml:34-35 do set runAsNonRoot: true / runAsUser: 101
- helm/gula-platform/templates/postgres/statefulset.yaml:125 securityContext runAsNonRoot: false
- helm/gula-platform/values.yaml:49 readOnlyRootFilesystem: false
- k8s/base/redis/deployment.yaml:63-68 volumeMount /data backed by `emptyDir: {}`
- nhop-platform/Dockerfile:23, platform/Dockerfile:12, services/device_bridge/Dockerfile:12 set USER but have no HEALTHCHECK

**Reproduction / falsification:** Compare the Dockerfile instruction set (no USER) with the comment; inspect the Helm securityContext at line 125 and the Redis volume source. Falsified if the frontend image declares USER, the Helm pod runs non-root, and Redis data uses a persistent volume.

**Root cause:** Hardening was applied per-file without a repo-wide image/workload baseline or lint rule.

**Impact:** The frontend container process may run as root if the image is used outside K8s; one database workload explicitly opts out of non-root; Redis data is lost on pod restart even though the platform uses Redis for queues/caching.

**Recommended remediation:** Add `USER 101` to the frontend runtime stage, justify or remove `runAsNonRoot: false` with an owner decision, set readOnlyRootFilesystem where feasible, replace Redis emptyDir with a PVC unless explicitly cache-only, and add a Hadolint/checkov gate for all images and manifests.

**Alternatives considered:**

- Run nginx as an unprivileged user on a high port behind a loopback proxy.
- Use a managed Redis-compatible service (cost/licence assessment required) or Redis with an append-only PVC.

### AUD-INF-007 — Availability coverage is partial: no PodDisruptionBudget in k8s/base and only backend has one in Helm

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | MEDIUM |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- grep across 37 k8s YAML files: PodDisruptionBudget definitions = 0
- grep across 37 Helm YAML files: PodDisruptionBudget definitions = 1 (helm/gula-platform/templates/backend/pdb.yaml)
- HPA definitions: k8s = 4 (k8s/base/backend/hpa.yaml, k8s/base/microservices/hpa.yaml and overlays), Helm = 3
- Liveness/readiness probes present in 7 k8s workload files and 8 Helm workload files; stateful data services are covered but frontend/gateway/microservices coverage is not uniform in Helm

**Reproduction / falsification:** Enumerate `kind: PodDisruptionBudget` across both trees. Falsified if every replicated workload has a PDB and HPA/probe coverage is complete.

**Root cause:** Availability primitives were added to selected Helm templates first; the parallel k8s/base tree was not updated.

**Impact:** Voluntary disruptions (node drains, cluster upgrades) can take down all replicas of unprotected workloads; no owner-approved availability target exists to size those PDBs against.

**Recommended remediation:** Add PDBs for every replicated workload in both trees, align minAvailable/maxUnavailable with an owner-approved availability target, and add a manifest lint gate asserting probe/limit/PDB/HPA presence.

**Alternatives considered:**

- Declare availability BLOCKED/NOT VERIFIED until the target is approved rather than choosing arbitrary values.
- Consolidate on Helm and delete the duplicate k8s/base tree after evidence-based verification (ADR-028).

### AUD-INF-008 — Deployment in this repository is verification-only; duplicate CodeQL workflows and no automated production deployment gate

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- .github/workflows/deploy.yml:1 name 'Verify Railway Deployment'; :3-4 workflow_dispatch only; steps perform HTTP verification only
- .github/workflows/codeql.yml:14-20 and .github/workflows/codeql-analysis.yml:3-9 both scan python + javascript-typescript on main push/PR with different schedules and different query sets (:79 default vs :42 +security-and-quality)
- .github/workflows/blue-green-deploy.yml:164-201 smoke test checks HTTP status only before traffic switch
- .github/workflows/canary-deploy.yml and auto-rollback.yml also require workflow_dispatch

**Reproduction / falsification:** Inspect workflow names/triggers and the two CodeQL matrices. Falsified if a single canonical deploy workflow with an approval gate and a single CodeQL configuration exist.

**Root cause:** Repository merge left duplicate security workflows and split deploy verification from actual deployment.

**Impact:** Duplicate analysis uploads and inconsistent query coverage; no repository-controlled production deploy approval or post-deploy verification gate; readiness claims based on 'deploy workflow present' are unsupported.

**Recommended remediation:** Keep one CodeQL workflow with the stronger query set, convert deploy.yml into a gated deployment with environment approval and post-deploy assertions, and document which workflow is authoritative.

**Alternatives considered:**

- Keep deployment external (Railway/Render) and state deployment as MANUAL / NOT VERIFIED in readiness documentation.
- Merge the two CodeQL workflows into a reusable workflow.

### AUD-INF-009 — TLS certificate handling could not be verified: divergent cert paths and no renewal automation; monitoring/logging claims not independently confirmed

| Attribute | Value |
|---|---|
| Severity | LOW |
| Likelihood | MEDIUM |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- nginx.conf:45-46 references /etc/letsencrypt/live/gula-platform.org/fullchain.pem and privkey.pem
- config/nginx/system/gula-platform-ssl.conf:60-61 references /etc/letsencrypt/live/gula-platform.org-0001/fullchain.pem and privkey.pem
- config/nginx/nginx-performance.conf:117-118 references /etc/nginx/ssl/fullchain.pem and privkey.pem
- grep for certbot in .github/workflows/ returns no matches
- backend/app/main.py:35-54,63-92,144 exposes /health, /health/ready, /health/live, /health/status, /health/deep; backend/app/routes/metrics.py:129 exposes /metrics/prom; no alerting rule/receiver definition was found in the reviewed workflow/config set

**Reproduction / falsification:** Diff the certificate paths and search workflows for renewal. Falsified if a single canonical cert path, automated renewal and a tested alerting rule set are present. Live TLS state is NOT SCANNED (no network).

**Root cause:** Multiple inherited nginx configurations reference different certificate layouts; observability exposes metrics/health but the alerting half is not present in-repo.

**Impact:** Renewal or rotation may update one configuration while another points at a stale suffix (-0001), causing TLS failure. Absence of in-repo alert rules means 'monitoring/alerting' cannot be claimed beyond endpoint exposure.

**Recommended remediation:** Define one canonical certificate location (preferably a mounted secret), add automated renewal/reload with a dry-run test, and commit versioned alert rules with a tested notification receiver; verify live TLS only with owner authorisation.

**Alternatives considered:**

- Use cert-manager with Let's Encrypt in K8s (free, self-hosted) instead of host certbot.
- Record the current state explicitly as NOT VERIFIED rather than asserting TLS readiness.

### AUD-INF-010 — Backup scripts exist but are not scheduled, attested or wired into any CI/operations workflow

| Attribute | Value |
|---|---|
| Severity | MEDIUM |
| Likelihood | HIGH |
| Status | DISCOVERED |
| Owner-gated | yes |

**Evidence (exact file:line):**

- scripts/backup.sh:15 RETENTION_DAYS default 30; :28 timestamped logging; :53,86-87 gzip dumps and retention deletion
- scripts/continuous-backup.sh:18-22 pg_dump -Fc daily; :29 WAL sync to S3; :36,43 weekly/monthly uploads; :57-58 metrics push with `|| true`
- scripts/dr_recovery.sh:52-66 creates a disposable DB, restores and compares counts; :73-99 manual failover path requires typed CONFIRM FAILOVER
- config/postgres-ha/backup-config.sh:41-43 retention defaults 30/7/60 days with pgBackRest-style repository configuration
- grep across .github/workflows/ for backup.sh, validate-restore, restore-test, dr_recovery, continuous-backup or backup-verification returns ZERO matches
- GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:35 'No restore/PITR drill; RPO/RTO UNMEASURED'

**Reproduction / falsification:** Search all 33 workflows for the backup/restore scripts (zero hits); inspect scripts for execution evidence. Falsified if scheduled jobs with run logs, retention assertions and a dated restore drill are produced at the audited HEAD.

**Root cause:** Backup capability was delivered as shell tooling without operational scheduling, monitoring of job success, or evidence retention.

**Impact:** Existence of scripts is not evidence that a backup has ever run. Combined with AUD-INF-001 and AUD-INF-002, backup posture is IMPLEMENTED (scripts) but NOT VERIFIED (execution and recovery).

**Recommended remediation:** Schedule backups through an owner-authorised mechanism, emit success/failure metrics without `|| true`, alert on age/failure, retain run attestations, and pair the first scheduled cycle with a restore drill that measures RPO/RTO.

**Alternatives considered:**

- Use the repository's self-hosted pgBackRest configuration (config/postgres-ha/backup-config.sh) with a tested cron/Kubernetes CronJob in an isolated environment.
- Keep backups manual and state recovery as BLOCKED / NOT VERIFIED in release documentation.



## 5. Findings summary table

| ID | Severity | Likelihood | Status | Owner-gated | Title |
|---|---|---|---|---|---|
| AUD-INF-001 | HIGH | HIGH | DISCOVERED | yes | scripts/validate-restore.sh can return PASS and exit 0 even when pg_restore fails |
| AUD-INF-002 | HIGH | HIGH | DISCOVERED | yes | No restore/PITR drill and no measured RPO/RTO; the only rehearsal report is untracked and pinned to a different HEAD |
| AUD-INF-003 | HIGH | HIGH | DISCOVERED | yes | Rollback is manual-only despite the 'auto-rollback' name; canary has no error-rate/latency gate and ignores its declared traffic input |
| AUD-INF-004 | HIGH | MEDIUM | DISCOVERED | yes | Compose configuration allows empty signing secrets and ships a development-mode Vault bound to all interfaces |
| AUD-INF-005 | HIGH | MEDIUM | DISCOVERED | yes | Production compose template binds admin, monitoring and data-plane services to all host interfaces |
| AUD-INF-006 | MEDIUM | HIGH | DISCOVERED | yes | Container and workload hardening is inconsistent: frontend image runs as root, Helm Postgres pod sets runAsNonRoot=false, Redis uses ephemeral storage |
| AUD-INF-007 | MEDIUM | MEDIUM | DISCOVERED | yes | Availability coverage is partial: no PodDisruptionBudget in k8s/base and only backend has one in Helm |
| AUD-INF-008 | MEDIUM | HIGH | DISCOVERED | yes | Deployment in this repository is verification-only; duplicate CodeQL workflows and no automated production deployment gate |
| AUD-INF-009 | LOW | MEDIUM | DISCOVERED | yes | TLS certificate handling could not be verified: divergent cert paths and no renewal automation; monitoring/logging claims not independently confirmed |
| AUD-INF-010 | MEDIUM | HIGH | DISCOVERED | yes | Backup scripts exist but are not scheduled, attested or wired into any CI/operations workflow |

## 6. Domain conclusion

The infrastructure and disaster-recovery posture of the audited tree is **NOT INDEPENDENTLY
VERIFIED**. The control intended to prove recoverability can emit a false PASS
(AUD-INF-001), no restore/PITR drill exists and RPO/RTO are `UNMEASURED` (AUD-INF-002),
rollback is manual-only and canary promotion has no SLO gate (AUD-INF-003), and backup
scripts are not scheduled, attested or CI-wired (AUD-INF-010). No availability target,
RPO or RTO number is published by this audit; recovery remains
`BLOCKED / NOT VERIFIED`. Live TLS posture, deployed cluster state and actual backup job
execution are **NOT SCANNED (no network)** and are never reported as clean.

**Release recommendation:** Maintain HOLD. Remediate AUD-SUP-001 and AUD-INF-001 first; neither dependency security nor disaster recovery is independently verified.

No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded. Remediation and any
change to an immutable owner decision are owner-gated and out of scope for this audit.
