# Staging Runbook

## Purpose and deployment boundary

The permanent **Staging** environment is the promotion gate between reviewed code and the production environment. It must be a complete but isolated copy of the runtime topology: one API service, one PostgreSQL instance, one Redis instance, and a separately hosted frontend. Staging must not read, write, replicate, or reference production databases, Redis instances, secrets, domains, third-party webhooks, or patient data.

> **Safety rule:** only synthetic, de-identified, or specifically approved test data may enter Staging. Do not restore a production database into this environment.

Railway persistent environments are intended for this purpose: they isolate services and configuration, and can deploy a dedicated branch independently of production.[1]

| Layer             | Required setting                                                   | Prohibited setting                                                   |
| ----------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Source control    | Persistent `staging` branch, promoted from reviewed `main` commits | Direct force-pushes or unreviewed changes                            |
| API               | `ENV=staging`, `RUNTIME_MODE=api`, HTTPS-only public URL           | `DEMO_MODE=true`, permissive CORS, production callback URLs          |
| Database          | Fresh Railway Postgres service scoped to Staging                   | Production `DATABASE_URL` or backup restores containing patient data |
| Cache             | Fresh Railway Redis service scoped to Staging                      | Production Redis URL or degraded in-memory fallback                  |
| Frontend          | Dedicated staging domain and `VITE_API_URL`                        | Production API endpoint                                              |
| Secrets           | New random values generated separately for Staging                 | Copied production secret values                                      |
| Data integrations | Sandbox/test credentials or disabled integrations                  | Live SMS, payment, clinical, device, or notification credentials     |

## One-time Railway setup

Create a persistent `staging` environment in the existing Railway project. The recommended approach is **Duplicate Environment**, followed by review of its staged changes; Railway requires review and approval before those copied services deploy.[1] This creates the topology without altering the production environment.

1. In Railway, select the production environment and create a new persistent environment named `staging`.
2. Duplicate the service topology, then **replace** every data service and every secret with an independently provisioned Staging equivalent before approving the deploy.
3. Configure the API service to deploy the repository's `staging` branch, with root directory `.` and the existing Dockerfile path `backend/Dockerfile`.
4. Configure the frontend service to deploy the same `staging` branch, with root directory `frontend-v3`, build command `npm ci && npm run build`, and publish directory `dist`.
5. Assign Railway-provided domains first. A custom staging domain can be attached after health verification, for example `api.staging.gula-platform.org` and `staging.gula-platform.org`.
6. Create the GitHub **staging** environment and add the deployment team as required reviewers before use. The included verification workflow targets that environment.

## Staging variables

Set these variables in the **Railway Staging environment only**. Generate all secret values in Railway or another approved secret manager; do not commit values to Git, GitHub Actions logs, or issue comments.

| Variable                   | Required value or source                                                     |
| -------------------------- | ---------------------------------------------------------------------------- |
| `ENV`                      | `staging`                                                                    |
| `RUNTIME_MODE`             | `api`                                                                        |
| `FEATURE_BACKGROUND_TASKS` | `false` for the API service                                                  |
| `BASE_URL`                 | Exact HTTPS staging API URL, such as `https://api.staging.gula-platform.org` |
| `CORS_ORIGINS`             | Exact HTTPS staging frontend origin only                                     |
| `TRUSTED_HOSTS`            | Comma-separated staging API hostname(s) only                                 |
| `GULA_DATABASE_URL`        | Reference to the dedicated Staging PostgreSQL service                        |
| `REDIS_URL`                | Reference to the dedicated Staging Redis service                             |
| `SECRET_KEY`               | Fresh, cryptographically random value, 32+ characters                        |
| `REFRESH_TOKEN_SECRET`     | Fresh, cryptographically random value, 32+ characters                        |
| `ENCRYPTION_KEY`           | Fresh Staging encryption key                                                 |
| `NID_HMAC_KEY`             | Fresh Staging HMAC key, distinct from other keys                             |
| `AUDIT_ANCHOR_KEY`         | Fresh Staging HMAC key, distinct from other keys                             |
| `VITE_API_URL`             | Exact HTTPS Staging API base URL, on the frontend service only               |

The backend intentionally treats `ENV=staging` with production-grade safeguards: it requires HTTPS, hardened secrets, Redis, secure cookies, explicit CORS origins, and explicit trusted hosts. A configuration that falls back to production web origins fails instead of deploying.

## Promotion procedure

| Stage       | Required evidence                                                                              | Owner         |
| ----------- | ---------------------------------------------------------------------------------------------- | ------------- |
| 1. Review   | Pull request approved and CI checks green                                                      | Maintainer    |
| 2. Promote  | Fast-forward or merge the reviewed commit to `staging`                                         | Release owner |
| 3. Deploy   | Railway shows only Staging services changing                                                   | Release owner |
| 4. Verify   | Run **Verify Staging Deployment** with the API `/health` URL                                   | Release owner |
| 5. Validate | `/health`, `/health/ready`, and `/health/deep` all pass; manual smoke test uses synthetic data | QA owner      |
| 6. Release  | Open/approve a PR from the tested commit to `main`                                             | Maintainer    |

Railway also supports ephemeral pull-request environments for isolated integration and manual checks. These are complementary to, not a replacement for, the persistent Staging environment.[2]

## Rollback and incident response

If readiness or deep-health fails, stop promotion immediately. In Railway, redeploy the last known-good Staging deployment or previous staging commit; do not change production as a corrective action. Capture the failing commit, health response, and service logs without including secrets or patient data. Rotate any Staging secret suspected of exposure, invalidate sessions where appropriate, and rerun the verification workflow before allowing a new promotion.

## Regular checks

Review Staging configuration after every material integration or infrastructure change. At minimum, verify the service branch, domains, database and Redis service references, CORS allowlist, trusted-host allowlist, webhook sandbox mode, deployment approvers, and the absence of production credentials.

## References

[1]: https://docs.railway.com/environments "Railway Environments"
[2]: https://docs.railway.com/guides/preview-deployments-with-pr-environments "Railway Preview Deployments with PR Environments"
