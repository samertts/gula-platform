# RELIABILITY AUDIT — PROGRAM-GULA-PARALLEL-001 (AGENT 08)

**Platform:** GULA National Healthcare Platform | Iraq
**Wave:** A — READ-ONLY AUDIT. No build, deploy, rollback, scale, restore, migration, git-state or server command was executed.
**Date:** 2026-11-19
**Companion reports:** `DEVOPS_AUDIT.md`, `PERFORMANCE_AUDIT.md`

---

## 0. Executive summary

Reliability controls are **extensive on paper and defective in execution**:

- **One P0 process/safety issue:** `emergency-recover.sh` performs `git reset --hard` + `git clean -fd` against a stale branch and would destroy the 378 paths of protected user work if run in the current working tree. It must be quarantined with a warning, not executed.
- **Four P1 logic defects** in the deployment/recovery workflows: the blue-green automatic trigger references a workflow name that does not exist; blue-green rollback selects the wrong slot; canary health monitoring never evaluates probe results (promotion is unconditional); and auto-rollback verification can never succeed because it compares an HTTP body to the literal `"200"`.
- Backup/restore assets are numerous but fragmented; the strongest script (`scripts/backup.sh`) is sound, while the Makefile target and full-stack cron container bypass it. Restore is not exercised in CI.
- Kubernetes/Helm manifests are generally well formed (probes, HPA, PDB, ServiceMonitors), but readiness uses the liveness endpoint, base image is `:latest`, resource sizing conflicts with the worker model, and prod Redis remains a single replica despite an existing Sentinel configuration.
- Backup/DR documentation makes **commercial SaaS recommendations** and asserts RTO/RPO and encryption claims not evidenced in the repository — Constitution (`AGENTS.md:9-24`) requires free/self-hosted alternatives to be evaluated first. Existing self-hosted MinIO (`config/minio-ha/`, `docker-compose.full.yml:344-365`) is the documented free alternative.

No new service, licence, or operational cost is recommended.

---

## 1. Scope reviewed

| Area | Key paths |
|---|---|
| Deploy/rollback workflows | `auto-rollback.yml`, `blue-green-deploy.yml`, `canary-deploy.yml`, `rollback.yml`, `deploy.yml`, `staging-verify.yml`, `preview-deploy.yml`, `release.yml` |
| Recovery scripts | `emergency-recover.sh`, `scripts/backup.sh`, `scripts/continuous-backup.sh`, `scripts/dr_recovery.sh`, `scripts/backup-verification.sh`, `scripts/dr-failover.sh`, `scripts/dr-failback.sh`, `scripts/dr-test.sh`, `scripts/validate-restore.sh`, `scripts/pitr-recover.sh`, `scripts/manage-snapshots.sh`, `tests/recovery/recovery-test.sh`, `config/postgres-ha/backup-config.sh` |
| Docs | `gula_backup_guide.md`, `gula_disaster_recovery_playbook.md`, `docs/constitution/data_preservation/{backup_strategy,disaster_recovery_guide}.md`, `docs/production/DISASTER_RECOVERY_GUIDE.md`, `docs/adr/ADR-015-disaster-recovery.md`, `CLAUDE.md` |
| Orchestration | `Makefile`, `docker-compose.yml`, `docker-compose.full.yml`, `docker-compose.scale.yml`, `docker-compose.demo.yml` |
| IaC | `k8s/base/**`, `k8s/overlays/{dev,prod,region-*}/*`, `helm/gula-platform/**`, `terraform/environments/{dev,staging,prod,dr,pilot}/**`, `terraform/modules/**`, `config/dr/cross-region-replication.yml`, `config/minio-ha/**`, `config/redis-sentinel/**` |

Approximate files inspected: **48**.

---

## 2. Findings

### A08-R001 — P0 — `emergency-recover.sh` would irreversibly destroy protected user work

- **Evidence:**
  - `emergency-recover.sh:15-21` — self-description: "Hard-resets to the remote (discards ALL local changes)".
  - `:34` — `TARGET_BRANCH="claude/fix-bugs-vulnerabilities-Y6mGU"` — **not present** in the 12 local or 4 remote branches recorded in `PROGRAM_CONTROL.md:87-99`.
  - `:53-67` — `git fetch origin`, then aborts if that remote branch does not exist (a guard, but the branch is stale/absent).
  - `:71` — `git checkout -B "${TARGET_BRANCH}" "${TARGET_REMOTE}"`.
  - `:76` — `git reset --hard "${TARGET_REMOTE}"`.
  - `:81` — `git clean -fd` (deletes all untracked files, including the 232 untracked paths and 17 top-level untracked trees).
  - `:122-153` — also performs `sudo cp` into `/etc/nginx/...` and reloads/restarts nginx.
  - `PROGRAM_CONTROL.md:49-75` — 126 modified + 20 staged renames + 232 untracked paths are protected.
- **Affected components:** Entire repository working tree; system nginx configuration.
- **Root cause:** A field-repair script written for a different branch/time, left executable in the repository root with no confirmation prompt or dirty-tree guard.
- **Safe-fix possible?** Yes — add a hard `git status --porcelain` dirty-tree guard + explicit `--i-really-mean-it` flag and update/remove the stale branch; **do not run it**. (File is clean in `git status`.)
- **Approval required?** **Yes — P0 halt.** Orchestrator approval plus explicit user release of the protected paths; a safe fix adds a guard only, never executes recovery.

### A08-R002 — P1 — Blue-green automatic deployment trigger names a workflow that does not exist

- **Evidence:**
  - `.github/workflows/blue-green-deploy.yml:3-8` — `workflow_run.workflows: ["CI - Build, Test & Security Scan"]`, `types: [completed]`, `branches: [main]`.
  - `.github/workflows/ci.yml:1` — actual name is `name: CI Pipeline`. No workflow in the 32-file inventory has the name `CI - Build, Test & Security Scan`.
  - `blue-green-deploy.yml:44-51` — the check job would set `should_deploy=true` on any successful triggering run, but no such run can occur.
- **Affected components:** Automated blue-green deployment; release pipeline.
- **Root cause:** Workflow renamed without updating the dependent `workflow_run` trigger.
- **Safe-fix possible?** Yes — change the trigger name to `CI Pipeline` (or add a `push: branches: [main]` trigger), after confirming CI actually builds/pushes an image (note: `ci.yml` currently has no image build/push job, so fixing the name alone may start deploys of a non-existent tag — label: **speculation requiring orchestrator/A08 verification**).
- **Approval required?** **Yes** (deployment semantics; P1).

### A08-R003 — P1 — Blue-green failure path can restore the *new* (bad) slot; post-switch health failure is only a warning

- **Evidence:**
  - `blue-green-deploy.yml:205-236` — traffic switched to `${TARGET_SLOT}` and the `blue-green/active-slot` annotation updated.
  - `:239-256` — post-switch verification: on non-200 it only `echo "WARNING: Active slot health check returned HTTP $STATUS"` and the step **succeeds**.
  - `:275-278` — rollback job runs only `if: failure() && needs.blue-green-deploy.result == 'failure'`, which cannot happen from the warning-only path.
  - `:293-301` — even if it runs, it reads the *current* annotation (`PREV=$(kubectl get svc gula-backend-active … active-slot)`) and then patches to that same value at `:308-314` — a no-op that "rolls back" to the slot that just failed.
  - `:151-160` — a single `deployment/gula-backend` is patched with a slot label while the smoke test port-forwards `svc/gula-backend-${target}` (`:176-179`); true two-slot isolation is not established by this workflow.
- **Affected components:** Production traffic recovery; blue/green guarantee.
- **Root cause:** Rollback state derived from mutable post-switch state instead of captured pre-switch state; health verification not treated as a gate.
- **Safe-fix possible?** Yes — capture `active` before switching (already output at `:56` and `:126`), pass it to the rollback job, fail the verification step on non-200, and verify both slot deployments exist.
- **Approval required?** **Yes** (production rollback semantics).

### A08-R004 — P1 — Canary "monitor" steps never evaluate health; promotion to 100% is unconditional

- **Evidence:**
  - `canary-deploy.yml:70-79` and `:94-104` — loops run `curl … || echo "FAIL"`, print `$STATUS`, sleep, and **never count failures or exit non-zero**.
  - `:83,107,119` — promotion steps guarded only by `if: success()`, which is always true after the above monitors.
  - `:9-12` — input `canary_percent` (10–50) is declared but ignored; `:49,64` hard-code 10%.
  - No Prometheus/error-rate query appears anywhere in the workflow.
- **Affected components:** Canary safety; automated progressive delivery.
- **Root cause:** Monitoring implemented as a sleep loop rather than an analysis gate.
- **Safe-fix possible?** Yes — accumulate failed probes, fail after a threshold, and use the `canary_percent` input; wire an existing Prometheus error-rate query (no new service).
- **Approval required?** **Yes** (deployment semantics).

### A08-R005 — P1 — Auto-rollback verification can never succeed; the workflow is manual-only despite documentation

- **Evidence:**
  - `auto-rollback.yml:85-100` — `STATUS=$(curl -sf --max-time 5 http://localhost:18000/health 2>/dev/null || echo "000")` then `if [ "$STATUS" = "200" ]`. With `-s` (no `-w '%{http_code}'`), a successful curl returns the **response body**, not `200`; the condition is therefore never true. Contrast the correct pattern at `blue-green-deploy.yml:185-187` (`-o /tmp/health.json -w "%{http_code}"`).
  - `:4` — trigger is `workflow_dispatch` only; no `workflow_run`, `schedule`, webhook or monitoring trigger.
  - `CLAUDE.md:405` — documentation claims "`auto-rollback.yml` — Automatic rollback on health check failure".
  - `:73-81` — TrafficSplit weights are patched to backend 0 = 100 / backend 1 = 0 without mapping to the actual previous slot.
- **Affected components:** Automated recovery; operator trust in rollback verification.
- **Root cause:** Copy/paste divergence between workflows plus documentation drift.
- **Safe-fix possible?** Yes — use `-o /dev/null -w "%{http_code}"`; document as manual or add an alert-triggered path (no new service required — existing ntfy/Alertmanager at `docker-compose.yml:311-356`).
- **Approval required?** **Yes** (rollback semantics).

### A08-R006 — P1 — Deployment and rollback steps systematically swallow failures with `|| true`

- **Evidence:**
  - `blue-green-deploy.yml:154` (`kubectl set image … || true`), `:233` (TrafficSplit patch `|| echo …`), `:314` (rollback patch `|| echo "manual intervention required"`).
  - `canary-deploy.yml:58,66,91,115,127,144` — every image/traffic patch suppressed.
  - `auto-rollback.yml:80` — TrafficSplit patch suppressed.
  - `preview-deploy.yml:22` — `npm install … || true` (see DevOps A08-011).
- **Affected components:** All four deployment workflows; truthfulness of "success" status.
- **Root cause:** Defensive error suppression applied uniformly, including to actions whose failure must be fatal.
- **Safe-fix possible?** Yes — make traffic/image patch failures fatal, keep only optional CRD checks non-fatal.
- **Approval required?** **Yes** (CI/deploy semantics).

### A08-R007 — P2 — No metrics-driven rollback and no integration between monitoring alerts and deploy workflows

- **Evidence:** All deploy/rollback workflows are `workflow_dispatch` or a single `workflow_run` (`blue-green-deploy.yml:4-9`; `auto-rollback.yml:3-4`; `canary-deploy.yml:3-4`; `rollback.yml:3-4`; `deploy.yml:3-4`). `config/prometheus/rules/` is mounted into Prometheus (`docker-compose.yml:376`) but no workflow queries Prometheus for error rate/latency. Alertmanager routes to ntfy/Slack only (`docker-compose.yml:311-356`).
- **Affected components:** Mean-time-to-recover; clinical availability.
- **Root cause:** Monitoring and deployment planes are disconnected.
- **Safe-fix possible?** Yes, without new infrastructure: add a `workflow_dispatch` call from an existing alert path or a scheduled query against existing Prometheus.
- **Approval required?** **Yes** (automated production action; orchestrator + A04).

### A08-R008 — P2 — Three divergent backup paths; only one has integrity verification; no restore drill in CI

- **Evidence:**
  - Strong path: `scripts/backup.sh:12` `set -euo pipefail`; `:53-58` pg_dump | gzip + `sha256sum` sidecar; `:66-75` `verify` action; `:87-92` retention.
  - Weak path 1: `Makefile:184-189` `docker exec gula-postgres pg_dump … | gzip > …` — no `pipefail`, no checksum, no verification, no off-site copy.
  - Weak path 2: `docker-compose.full.yml:767-785` `backup-cron` shell writes two `pg_dump | gzip` crontabs with `find … -delete`; no `set -o pipefail`, no checksum, no healthcheck, no encryption; backups land in `./backups` bind mount only.
  - `scripts/backup-verification.sh` and `scripts/validate-restore.sh` exist (verified) but grep shows no workflow reference; `Makefile:394-396` exposes them manually.
  - `gula_backup_guide.md:36-39` documents `./scripts/backup.sh verify`; `:41-48` documents manual `gunzip … | psql` restore.
- **Affected components:** clinical data recoverability, RPO confidence.
- **Root cause:** Backup capability reimplemented independently in Makefile, compose and scripts directory; no single canonical path.
- **Safe-fix possible?** Yes — make `make backup` delegate to `scripts/backup.sh`, add a comment in `backup-cron` pointing to the canonical script, and add a scheduled *documentation* drill (no production data touched).
- **Approval required?** **Yes** (operational semantics; orchestrator + data owner).

### A08-R009 — P2 — Backup/DR documentation recommends paid SaaS and asserts unverified RTO/RPO and encryption claims

- **Evidence:**
  - `gula_backup_guide.md:7-14` proposes `DigitalOcean Spaces`, `Supabase / Managed DB` (commercial SaaS) as the off-site/managed tiers; `:30-33` requires `aws-cli` + AWS keys.
  - Existing free/self-hosted alternative in-repo: `config/minio-ha/docker-compose.minio-ha.yml`, `config/minio-ha/replication-rules.json`, `docker-compose.full.yml:344-365` (MinIO) — no cost analysis documented anywhere for the SaaS choices.
  - `gula_disaster_recovery_playbook.md:17-19` claims RTO < 5 s / < 2 min and RPO 0 / < 4 h; `:31-33` claims AES-256-GCM backup encryption and automated restore drills. No implementation evidence was found for the encryption at rest or scheduled drills (label: **speculation** — a wider search may reveal external runbooks).
  - Stale paths in docs: `gula_backup_guide.md:55-56` references `gula-platform/docs/...` and `:25-26` `/home/ubuntu/gula-platform/...`, which do not match this repository root.
  - `AGENTS.md:9-24` — Free First / Self-Hosted First / Zero Paid Dependency / No Vendor Lock-In.
- **Affected components:** Procurement/compliance, disaster-recovery credibility.
- **Root cause:** Arabic guidance authored as strategy narrative, not mapped to implemented tooling; Constitution not applied to documentation.
- **Safe-fix possible?** Yes — documentation-only: add a "free/self-hosted first" section naming existing MinIO + `mc` replication, downgrade aspirational RTO/RPO to "target (not yet verified)", and correct stale paths. Both docs are clean in `git status`.
- **Approval required?** **Yes** (clinical/DR claims require data owner + A04 review before wording changes).

### A08-R010 — P2 — `make restore` is advertised but has no target

- **Evidence:** `Makefile:11` lists `restore` in `.PHONY`; grep for `^restore:` returns no match. `Makefile:184-189` defines `backup` only. `scripts/dr_recovery.sh`, `scripts/pitr-recover.sh` exist but are reachable only via other targets (`Makefile:386,401`).
- **Affected components:** Operator recovery procedure; MTTR.
- **Root cause:** Target removed/renamed without updating `.PHONY` help.
- **Safe-fix possible?** Yes — either add a `restore` target that calls the canonical restore script with explicit confirmation, or remove it from `.PHONY`/help.
- **Approval required?** **Yes** (restore is a destructive operational action; do not add a silent one).

### A08-R011 — P2 — HA claims vs single points of failure in committed orchestration

- **Evidence:**
  - `docker-compose.full.yml:418-421` — Vault runs `-dev` (in-memory), despite a `vault-data` volume at `:430`.
  - `docker-compose.full.yml:256-275` — Kafka single broker with `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1` and a comment at `:256` "single-node dev", yet this is the *full* stack file.
  - `docker-compose.full.yml:341-345` — MinIO single-node; comment at `:342-343` says production needs 4+ nodes / erasure coding (a separate `config/minio-ha/` compose exists).
  - `k8s/overlays/prod/patch-replicas.yaml:31-33` — Redis `replicas: 1`, while `config/redis-sentinel/docker-compose.redis-ha.yml` and `docker-compose.full.yml:162-184` implement Sentinel.
  - `docker-compose.full.yml:300-314` — Ollama has only a memory reservation, no CPU limit or healthcheck.
- **Affected components:** Claimed HA posture for secrets, events, object storage and cache.
- **Root cause:** Multiple reference topologies without a declared canonical production profile.
- **Safe-fix possible?** Partial — align documentation to actual state (safe, doc-only). Enabling HA services would add operational cost and is **not** recommended without proven need.
- **Approval required?** **Yes** for any topology change; No for honest documentation.

### A08-R012 — P2 — Kubernetes backend uses mutable `:latest` image and readiness probes the liveness endpoint

- **Evidence:**
  - `k8s/base/backend/deployment.yaml:54-55` — `image: ghcr.io/samertts/gula-platform/backend:latest`, `imagePullPolicy: Always`.
  - `:99-114` — `livenessProbe` and `readinessProbe` both use `httpGet.path: /health`; no `startupProbe`.
  - `CLAUDE.md:142-150` — `/health` is liveness only; `/health/ready` is the documented readiness endpoint used by Docker healthcheck and gateway.
  - Helm divergence: `helm/gula-platform/templates/backend/deployment.yaml:65-80` includes liveness + readiness + startup probes and a `preStop` sleep hook; `helm/gula-platform/values.yaml:76-77` leaves image `tag: ""` / `pullPolicy: ""`.
- **Affected components:** Zero-downtime rollouts; early traffic routing to uninitialised pods.
- **Safe-fix possible?** Yes — set readiness path to `/health/ready`, add a startupProbe, replace `:latest` with a release tag/digest (k8s base files are clean).
- **Approval required?** **Yes** (deployment semantics; version source must be decided).

### A08-R013 — P3 — Terraform state backends use commercial cloud; no state versioning declared in-repo

- **Evidence:** `terraform/environments/{prod,dr,pilot}/provider.tf:76-82` (prod shown) — `backend "s3"` with `encrypt = true`, `dynamodb_table = "gula-terraform-locks-prod"`; `staging/provider.tf:44-48` similar. No `versioning` configuration appears in the committed modules (verified by grep in `terraform/`); bucket versioning may be configured out-of-band — **speculation**.
- **Affected components:** IaC state durability; Constitution (Self-Hosted First / No Vendor Lock-In).
- **Root cause:** Cloud-specific backend chosen without documented free alternative analysis; MinIO (S3-compatible, self-hosted, already in repo) exists.
- **Safe-fix possible?** Yes — documentation/addendum evaluating MinIO S3 backend as the free alternative; **no** migration recommended in Wave C.
- **Approval required?** **Yes** for any backend change; No for documentation.

### A08-R014 — P3 — Rollback workflow is coupled to Vercel SaaS while preview deployment is a no-op

- **Evidence:** `.github/workflows/rollback.yml:22-48` — job `rollback-vercel` using `amondnet/vercel-action` with `VERCEL_TOKEN/ORG_ID/PROJECT_ID`; `preview-deploy.yml:19-23` only attempts `npm install` and echoes a message (no preview deployment).
- **Affected components:** Vendor lock-in, rollback credibility for frontend previews.
- **Root cause:** Two disconnected SaaS-era workflows.
- **Safe-fix possible?** Yes — documentation or orchestrator decision; do not add cost. Existing self-hosted frontend/nginx path is in `docker-compose.yml:243-264`.
- **Approval required?** **Yes** (deployment semantics + Constitution).

### A08-R015 — P3 — Fragmented, partly stale DR documentation and script families

- **Evidence:** Backup/DR guides exist at `gula_backup_guide.md`, `gula_disaster_recovery_playbook.md`, `docs/constitution/data_preservation/{backup_strategy,disaster_recovery_guide}.md`, `docs/production/DISASTER_RECOVERY_GUIDE.md`, `docs/adr/ADR-015-disaster-recovery.md`, `docs/freeze/pi-004/DISASTER_RECOVERY_GUIDE.md`, `platform/reports/pi-004/DISASTER_RECOVERY.md`. Script families: `scripts/backup.sh` vs `scripts/continuous-backup.sh` vs `scripts/dr_recovery.sh` vs `scripts/dr-failover.sh`/`dr-failback.sh`/`dr-test.sh` vs `tests/recovery/recovery-test.sh`. No file declares which set is canonical.
- **Affected components:** Operator cognitive load during incidents.
- **Root cause:** Parallel documentation tracks retained across program phases.
- **Safe-fix possible?** Yes — add a single index doc under `docs/production/` pointing to canonical scripts (doc-only).
- **Approval required?** No for doc-only index; Yes if declaring a canonical destructive procedure.

---

## 3. Positive controls observed

- `docker-compose.yml` and `docker-compose.demo.yml` use readiness-gated `depends_on`, restart policies, `no-new-privileges`, resource limits and healthchecks throughout (e.g. `docker-compose.yml:170-187, 231-264, 290-300`; `docker-compose.demo.yml:19-24,39-44,87-99`).
- `scripts/backup.sh:12,53-58,66-75` implements `pipefail` + SHA-256 integrity + verification — a sound canonical backup primitive.
- `k8s/base/` includes HPA, PDB (Helm), PVC for audit anchors, topology-spread overlays for `region-eu`/`region-me`, and ServiceMonitors in Helm templates (`helm/gula-platform/templates/*/servicemonitor.yaml`).
- `terraform/environments/*/provider.tf` use remote state with encryption and DynamoDB locking; a dedicated `dr` environment exists (`terraform/environments/dr/`).
- `config/dr/cross-region-replication.yml` and `config/minio-ha/` provide existing self-hosted replication primitives (no new cost required).
- Blue-green workflow uses a shared `concurrency` group with `cancel-in-progress: false` (`blue-green-deploy.yml:20-22`, `auto-rollback.yml:15-17`) — correct for slot switches.
- `staging-verify.yml:26-77` validates URL shape and checks `/health`, `/health/ready`, `/health/deep` with a GREEN/YELLOW gate — the strongest verification workflow in the repo.

---

## 4. Wave C — SAFE standalone remediation candidates (NOT applied)

All candidates below are **proposals only**. Each must still pass `FILE_OWNERSHIP_MATRIX §5` (clean file, approved finding in `MASTER_REMEDIATION_REGISTER`, no open P0 on the component, no CI/clinical/security semantic change without approval). `git status --porcelain` was checked for the listed paths: all are clean unless explicitly flagged.

| # | Finding | Path | Proposed change | Why safe / scope note |
|---|---|---|---|---|
| C1 | R001 | `emergency-recover.sh` | Add a dirty-tree guard (`git status --porcelain` → refuse if non-empty) and require an explicit `CONFIRM_DESTRUCTIVE_RECOVERY=1` flag; update stale branch reference. | Adds a guard only; never executes recovery. Clean file. P0 must be acknowledged by orchestrator first. |
| C2 | R010 | `Makefile` | Remove `restore` from `.PHONY` (line 11) **or** document `make dr-failover` / `scripts/dr_recovery.sh` as the recovery entry point. | Documentation/metadata only; no destructive target added. Clean file. |
| C3 | R008 | `Makefile:184-189` | Replace inline `pg_dump | gzip` with a call to `scripts/backup.sh` (which already has `pipefail` + SHA-256). | Reuses existing canonical script; no new dependency/service. Verify `BACKUP_DIR` compatibility first. |
| C4 | R009 | `gula_backup_guide.md` | Append a "Free/self-hosted alternatives" section citing existing `config/minio-ha/` + `scripts/backup.sh`; replace stale `gula-platform/...` and `/home/ubuntu/...` paths with repository-relative ones; mark RTO/RPO as targets pending drill. | Doc-only; does not alter clinical behaviour or weaken controls. Requires data-owner wording approval. Clean file. |
| C5 | R009 | `gula_disaster_recovery_playbook.md` | Add a "current implementation status" column/table distinguishing implemented vs aspirational controls; cite concrete scripts. | Doc-only, increases honesty; no new cost. Clean file. |
| C6 | R012 | `k8s/base/backend/deployment.yaml:105-114` | Change readiness probe path from `/health` to `/health/ready` (documented in `CLAUDE.md:148`); add startupProbe mirroring Helm. | Aligns k8s with the existing documented readiness contract; no new service. Clean file; requires deployment approval. |
| C7 | R012 | `k8s/base/backend/deployment.yaml:54` | Replace `:latest` with a release tag/digest sourced from a single variable — **documentation/PR note only in Wave C**, no value invented. | Prevents unpinned prod images; needs release-tag decision, so propose not apply. |
| C8 | R005 | `.github/workflows/auto-rollback.yml:89` | Change curl to `-o /dev/null -w "%{http_code}"` and compare to `200`. | One-line correctness fix; no new permission. Clean file; deployment semantics → approval required. |
| C9 | R004 | `.github/workflows/canary-deploy.yml:70-104` | Count failed probes and fail the monitor step after a threshold before `if: success()` promotions. | Uses existing probes only; no new infra. Clean file; approval required. |
| C10 | R003 | `.github/workflows/blue-green-deploy.yml:239-256,275-314` | Pass pre-switch `active` slot output to rollback job; make post-switch non-200 fatal. | Restores correct slot semantics; clean file; approval required. |
| C11 | R002 | `.github/workflows/blue-green-deploy.yml:6` | Correct trigger name to `CI Pipeline` **only after** CI image-push job exists (currently absent). | Fixing the name alone could deploy a missing tag — hold until C12. |
| C12 | — | `.github/workflows/ci.yml` | Add an image build-and-push job (GHCR) and export the tag as an artifact for downstream deploy workflows. | Larger CI change; **not a "standalone safe" candidate** — listed for completeness, requires full design approval. |
| C13 | R007 | `docs/production/` (new index doc) | Document that alert→rollback is **manual today** and name the operator runbook (existing ntfy/Alertmanager). | Doc-only; honest, no automation added. |
| C14 | R014 | `docs/architecture/` (short ADR addendum) | Record the free/self-hosted frontend deployment alternative (existing nginx/Traefik) vs Vercel; no change to workflow. | Doc-only; supports Constitution compliance. |

### Explicitly INELIGIBLE for Wave C (USER-MODIFIED / protected — report only)

- `.github/workflows/frontend-pwa.yml` — verified ` M`.
- `.github/workflows/security-hardening.yml` — verified ` M`.
- `.github/dependabot.yml` — protected per `PROGRAM_CONTROL §2.2` / `FILE_OWNERSHIP_MATRIX §4`.
- `services/lab/Dockerfile` — protected per program brief.
- `frontend-v3/package.json`, `frontend-v3/package-lock.json`, `frontend-v3/vite.config.ts` — USER per `PROGRAM_CONTROL §2.2`.
- 20 staged renames into `archive/legacy/**`, 8 untracked migrations, all of `GOVERNANCE/**`, `GLOSI/**`, `backend/app/health_core/**`, `backend/app/domain_platform/**`, `backend/app/communication/**` — protected; no remediation.

---

## 5. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A08-R01 (P0):** Orchestrator decision to quarantine `emergency-recover.sh` (C1) and communicate a "do not run" notice to all agents/operators.
2. **SCOPE_REQUEST-A08-R02 (P1):** Orchestrator + release owner decision on the canonical deploy pipeline (C11/C12) — blue-green trigger cannot be safely fixed in isolation today.
3. **SCOPE_REQUEST-A08-R03 (P1):** A04 + orchestrator approval for rollback/canary workflow correctness fixes (C8–C10).
4. **SCOPE_REQUEST-A08-R04:** Data owner approval for backup/DR wording changes (C4/C5) and for defining a canonical restore path (C3).
5. **SCOPE_REQUEST-A08-R05:** Infrastructure owner confirmation on intended HA topology (Vault, Kafka, MinIO, Redis Sentinel, prod overlay) before any topology change; no new cost authorised.
