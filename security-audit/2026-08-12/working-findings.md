# GULA — findings working notes

Assessment basis: authorized owner confirmation in conversation; safe, read-only review of https://www.gula-platform.org and local review of repository `samertts/gula-platform` at HEAD f1a3cc3a23594983857722b13b757a852fa60c8a. No credential submission, destructive action, persistence, data extraction, privilege escalation, or exploit execution was performed.

## Confirmed / strongly evidenced findings

### F-01 — Historical secret-bearing `.env` files in Git history — High pending rotation; Critical if any credential remains active
- The current checkout no longer tracks `.env` or `.env.production`; only example files remain.
- Git history contains multiple commits that tracked `.env` / `.env.production`, including recent security-remediation commits.
- Redacted historical scan found 5 unique blobs: `.env` (2) and `.env.production` (3); some blobs contained many non-placeholder assignments (25 and 79 in classified production blobs).
- Exact secret values were not printed or retained in this notes file. Active validity was not tested.
- Required action: revoke/rotate every credential/key that ever appeared; audit cloud/IAM/database/API logs; purge history after rotation; enable secret scanning and push protection.

### F-02 — Production deep-link routing mismatch — Medium/High operational security impact
- Live `https://www.gula-platform.org/login` returned 404 from Vercel, while the SPA source defines `/login` and `/register` as browser-history routes.
- `frontend-v3/src/routes/index.tsx` lines 104–112 defines client routes; line 201 is only a client catch-all and cannot fix a server-side direct request.
- `frontend-v3/vite.config.ts` lines 109–121 contains only a local dev proxy, no production history fallback.
- `.github/workflows/frontend-pwa.yml` lines 160–164 and 203–207 deploy the downloaded PWA artifact under `frontend-v2/build/`, while the current route evidence is in `frontend-v3`, indicating deployment drift that must be resolved.
- Impact: direct login/register links, refreshes, password-manager links, and bookmarked protected routes can fail or route inconsistently; this can create auth-flow confusion and bypass assumptions if different artifacts are served.

### F-03 — Security headers inconsistent on live 200 page — Medium hardening gap
- Live homepage response had `Access-Control-Allow-Origin: *` and HSTS, but no CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, or Permissions-Policy in the captured headers.
- A Vercel 404 response did include several of those headers and a CSP, demonstrating inconsistent application of the policy.
- Homepage was static and did not expose sensitive data in this review; CORS `*` on a static document is not independently a data exposure finding. Treat as header consistency/hardening issue unless API responses also allow wildcard origins.
- Required action: configure headers at hosting/CDN layer for all responses and verify API CORS separately; use a strict CSP appropriate to the deployed assets.

### F-04 — Frontend/API/deployment contract needs reconciliation — Medium/High until tested in a real environment
- `frontend-v3/src/api/client.ts` uses `VITE_API_BASE_URL` (fallback `/api`), `withCredentials: true`, and POSTs an empty JSON body to `/auth/refresh` using cookies.
- Backend legacy routes include `/login`, `/session`, `/logout` and `/auth/refresh`; refresh accepts cookies and returns rotated cookies plus JSON tokens.
- Backend also mounts a separate NIAM router under `/niam` with `/niam/auth/login`, `/niam/auth/refresh`, etc.
- Therefore the earlier concern is not a proven total auth failure; the confirmed risk is duplicated auth contracts and deployment ambiguity, which can cause inconsistent cookie/token behavior and bypass testing gaps. Must map the deployed API base and CI artifact to one canonical auth contract.

## Stale or not independently confirmed

- Existing `security-audit/executive-summary.md` reports 12 Critical / 34 High etc. It is dated 2026-07-24 and is a secondary artifact, not proof of all items.
- Current K8s manifests contain `runAsNonRoot: true` for backend, frontend, gateway, microservices, Redis, RabbitMQ, and Postgres; the summary claim “pods running as root” is not currently confirmed for these manifests.
- Terraform modules visibly use `random_password` and AWS Secrets Manager for DB/RabbitMQ, so the summary claim “no secrets management solution” is not current as stated. Terraform state protection still needs verification.
- No active exploit, credential validation, authenticated test, or privilege-escalation test was performed.

## References
- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- OWASP Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Content Security Policy Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html

### F-05 — Mobile certificate pinning uses placeholder pins and inconsistent domains — High release blocker
- Android `AndroidManifest.xml` line 33 enables `@xml/network_security_config`.
- Android `network_security_config.xml` lines 17–27 pins `api.gulaplatform.com`, `staging.gulaplatform.com`, and `staging-api.gulaplatform.com` with placeholder SHA-256 values consisting of repeated `A`/`B` characters.
- Android `CertificatePinningInterceptor.kt` lines 10–14 repeats the same placeholder pins, and `NetworkModule.kt` wires the pinner into OkHttp.
- Android release `build.gradle.kts` lines 48–55 points production to `https://api.gulaplatform.com/api/v1/`, while the live website/API evidence uses a different domain family (`api.gula-platform.org` was observed in published frontend connection policy). The domain contract must be unified.
- iOS uses a separate domain family (`api.gula.iq`, `analytics.gula.iq`) and another set of static pin strings. No release build was installed, so runtime failure was not executed; source evidence is sufficient to mark this as a release-blocking configuration defect until real pins and one canonical API domain are verified.
- Required action: remove placeholder pins from release branches, obtain real SPKI pins with a documented backup pin/rotation plan, align domains across web/Android/iOS/backend/DNS, and run a staging smoke test on physical/emulated devices before release.

### F-06 — Mobile permissions and operational surface require least-privilege review — Low/Medium pending product justification
- Android declares camera, Bluetooth, foreground service/data sync, boot completed, notifications, biometric, and legacy external storage permissions.
- `allowBackup=false` is correctly set and production cleartext is disabled by the base network config.
- The permissions are not individually proven exploitable, but camera/Bluetooth/boot/foreground-service capabilities should be justified per flavor and removed from builds that do not need them; verify exported components and runtime permission prompts in a signed release build.

### F-07 — Production build injects the wrong Vite API variable — High deployment/configuration risk
- `.github/workflows/frontend-pwa.yml` lines 80–92 inject `REACT_APP_API_BASE_URL` with `https://api.gulaplatform.com/api/v1/` (and staging equivalent).
- `frontend-v2/src/api/client.ts` line 1 reads `import.meta.env.VITE_API_BASE`, not `REACT_APP_API_BASE_URL`; the client therefore falls back to `/api` unless another `VITE_API_BASE` is supplied.
- The same workflow builds frontend-v2 and uploads `frontend-v2/build/`, while the Vite config has no `build.outDir` override, so Vite's default output is `dist/`. This can fail artifact publication or deploy a stale artifact.
- The live site did load an SPA shell, but the specific backend endpoint used by the shipped artifact was not authenticated or modified during this review. Treat as a confirmed release-pipeline contract defect with potentially high availability/authentication impact, not as proven data exposure.
- Required action: choose one frontend version; use `VITE_API_BASE`/`VITE_API_BASE_URL` consistently; set explicit `build.outDir` or correct artifact path; add CI assertions that the built JS contains the intended API origin and that direct `/login` returns the SPA shell.
