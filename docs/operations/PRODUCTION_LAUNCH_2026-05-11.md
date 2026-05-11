# Production Launch — 2026-05-11 — Verification & Posture

Tonight's objective was the transition from infrastructure stabilization
to **operational medical-intelligence collection mode**. This document
records (a) the production verification carried out at launch time, and
(b) the deployment posture every flag is in as the system goes live.

## 1. Phase 1 verification

| Check                                  | Method                                  | Result |
|----------------------------------------|-----------------------------------------|--------|
| DNS — `gula-platform.org`              | curl HEAD via Cloudflare                 | ✅ resolves to Cloudflare (104.21.x.x) |
| DNS — `www.gula-platform.org`          | curl HEAD via Cloudflare                 | ✅ resolves to Cloudflare (172.67.x.x) |
| DNS — `api.gula-platform.org`          | curl HEAD via Cloudflare                 | ✅ resolves to Cloudflare (104.21.x.x) |
| TLS — apex                              | curl HEAD; HSTS surfaced in response     | ✅ `Strict-Transport-Security: max-age=63072000` |
| Vercel production deployment           | Vercel MCP `list_deployments`            | ✅ `dpl_4FEu9nZE…` state `READY`, target `production`, commit `04d8328` |
| Frontend HTML served                   | Vercel MCP `web_fetch_vercel_url`        | ✅ HTTP 200, Vite shell + PWA manifest |
| Frontend hardening headers             | response headers                         | ✅ X-Frame-Options DENY · X-Content-Type-Options nosniff · Referrer-Policy strict-origin-when-cross-origin · Permissions-Policy camera/mic/geo off |
| Cache posture                          | response headers                         | ✅ `x-vercel-cache: HIT` (edge-cached) |
| API reachability (`api.gula-platform.org`) | Vercel rewrite probe `/api/health`    | ⚠️ transient Cloudflare 502 at probe time (retry-after 60s) — not a hard fail; backend is fronted by Cloudflare → DO droplet and is **not** Vercel-hosted, so this MCP path cannot fully verify it. Operator must confirm via `make health-deep` from a droplet shell. |

### Items noted but **not fixed tonight** (per directive — freeze infra after deploy)

- Frontend `<title>` is still the template default `"My Google AI Studio App"`.
  Cosmetic; tracked for the next cosmetic-only PR.
- Supabase project `joohoukzkubgzbdzdfxr` is `INACTIVE`. The dataset chosen
  for Phase 3 storage is the **existing GULA Postgres**, so this is not a
  blocker. Re-activating Supabase is a separate decision.

## 2. Phase 2–6 deployment posture at launch

| Phase | Component                              | Flag / state                                  | Posture           |
|-------|----------------------------------------|-----------------------------------------------|-------------------|
| 2     | Backend structured JSON logging        | `core/logging_config.py` (already live)       | ✅ on              |
| 2     | Backend Sentry                          | `SENTRY_DSN`                                  | ⏳ wired, no DSN set — set to enable |
| 2     | Frontend PostHog                        | `VITE_POSTHOG_KEY`                            | ⏳ wired lazy, no key set — set to enable |
| 2     | Frontend Sentry                         | `VITE_SENTRY_DSN`                             | ⏳ wired lazy, no DSN set — set to enable |
| 3     | AI dataset tables (5 tables)            | migration `20260511_0001_ai_interactions_dataset.py` | 🟢 schema deployed on `alembic upgrade head` |
| 3     | AI dataset routes                       | `ENABLE_AI_DATASET`                           | 🔒 OFF — flip per § 4.2 of `IRAQI_HEALTHCARE_INTELLIGENCE.md` |
| 4     | Feedback endpoint                       | `ENABLE_AI_FEEDBACK`                          | 🔒 OFF — flip after AI dataset is on |
| 5     | AI architecture constraints             | `docs/ai/AI_ARCHITECTURE_CONSTRAINTS.md`      | 📄 in repo |
| 6     | Iraqi healthcare intelligence spec      | `docs/ai/IRAQI_HEALTHCARE_INTELLIGENCE.md`    | 📄 in repo |

## 3. New routes registered

```
POST /api/ai/interactions                — log interaction          (flag: ENABLE_AI_DATASET)
POST /api/ai/interactions/{id}/refs      — append retrieval refs    (flag: ENABLE_AI_DATASET)
POST /api/ai/feedback                    — submit feedback           (flag: ENABLE_AI_FEEDBACK)
POST /api/ai/unresolved                  — log unresolved question  (flag: ENABLE_AI_DATASET)
GET  /api/ai/dataset/summary             — per-lab counters          (flag: ENABLE_AI_DATASET)
GET  /api/ai/dataset/status              — flag-state readout        (always available)
```

All write routes require an authenticated `LabUser` and stamp `lab_id`
server-side.

## 4. Rollout plan

1. **Today (launch):**  PR merges. Migration runs. Flags remain OFF. Tables
   sit empty. Telemetry SDKs sit dormant (no env keys set).
2. **+24h:**  Operator sets `SENTRY_DSN` (backend) and the two `VITE_*`
   keys (Vercel project env). Redeploy frontend. Sentry begins capturing
   client + server exceptions. PostHog begins capturing autocapture + view
   events.
3. **+72h (pilot lab):**  Operator flips `ENABLE_AI_DATASET=true` for the
   pilot lab only (process-restart, or admin runtime override via the
   ai_dataset_flags module).
4. **+1 week:**  Flip `ENABLE_AI_FEEDBACK=true`. Surface the feedback UI in
   the citizen-assistant view (separate PR).
5. **+2 weeks:**  Review `GET /api/ai/dataset/summary` per pilot lab; if the
   feedback ratios look healthy, expand to the next 3 labs.

## 5. Rollback

- **Routes:** flip `ENABLE_AI_DATASET=false`. Routes immediately return
  `503 AI_DATASET_DISABLED`. No data is lost; existing rows remain queryable.
- **Migration:** `alembic downgrade -1` on `20260506_0001` removes the five
  AI tables. Idempotent — safe to run multiple times.
- **Frontend SDKs:** unset `VITE_POSTHOG_KEY` and `VITE_SENTRY_DSN`,
  redeploy. Both go dormant on next page load.

## 6. Open follow-ups

| # | Item                                                             | Owner    |
|---|------------------------------------------------------------------|----------|
| 1 | Frontend `<title>` is template default                           | Frontend |
| 2 | Backend-side prompt redactor (precondition for platform-wide AI dataset enablement) | Backend  |
| 3 | Qdrant provisioning (vector store)                                | Infra    |
| 4 | Decide whether to re-activate Supabase or retire the project      | Ops      |
| 5 | Feedback UI components in the citizen-assistant view              | Frontend |
| 6 | Decide on `lab_subscriptions.research_consent` schema             | Product  |
