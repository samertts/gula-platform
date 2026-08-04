# PROGRAM-COMM-002A — Final Report: Enterprise Telegram Delivery

**Status:** ✅ Complete
**Date:** 2026-08-04
**Program:** PROGRAM-COMM-002A (telegram-notification-provider enterprise hardening, approved gap-analysis follow-up)
**Related:** ADR-012 (Telegram provider), ADR-011 (Resend/email), `docs/architecture/FREE_FIRST_POLICY.md`

## Executive summary

The GULA Platform Telegram provider (`shared/notifications/telegram.py`) was
upgraded from a single-message service to an enterprise-grade Telegram gateway
while preserving the canonical transport, the existing public API, and the
"primitive-reuse" rule from the approved gap analysis:

- Webhook mode: set/delete/get-info management, signed ingress, replay
  protection, flood + rate limiting, auto mode switching (polling/webhook).
- Broadcast/batch/scheduled delivery orchestrated over the existing
  `TaskPayload`/TaskWorker infra (no new background machinery).
- Media groups, rich messages, edit/delete, arbitrary attachments with MIME
  auto-detection, keyboard builders, channels/forums/topics support.
- Circuit breaking, delivery metrics, guaranteed redacted logging, and a
  Prometheus exposition endpoint.
- Sixteen enterprise tests (becoming 62 with the latent enterprise suite),
  plus the health/deep and Prometheus integration.

All hard validation gates PASS; ruff baseline preserved (379).

## What was delivered

| Component | Location | Notes |
|---|---|---|
| Enterprise provider (canonical transport) | `shared/notifications/telegram.py` | All legacy methods preserved; no signature break |
| Orchestration + circuit breaker | `backend/app/notifications/telegram_enterprise.py` | Delegates to shared; task `telegram.deliver` + `telegram.scheduled` |
| Webhook ingress | `backend/app/routes/telegram_webhook.py` | `POST /webhooks/telegram/update`, `GET /webhooks/telegram/health` |
| Communication-platform branch | `backend/app/notifications/service.py` | `channel == "telegram"` routes to enterprise provider |
| Platform wrapper | `backend/app/platform/notifications.py` | Health exposure for observability |
| Deep health + Prometheus | `backend/app/services/metrics_service.py` | `telegram` component + metrics append |
| Config + guards | `backend/app/config.py`, `shared/config/loader.py`, `backend/app/core/startup_guard.py`, `.env.example` | Env-only secrets; production fail-fast webhook validation |
| Rich-message pass-through | `shared/notifications/sender.py` | reply_markup / reply_to / thread / coords / contact |
| Enterprise test suite | `backend/tests/notifications/test_telegram_enterprise.py` | 62 computed tests (Bot API boundary patched) |

## Verification

### Local / unit

```
backend/tests/notifications/      141 passed
backend/tests/unit/               757 passed, 0 failed
backend/tests/unit/test_metrics_service.py included
backend/tests/unit/test_integration_parity.py  deep-health shape incl. telegram
```

Enterprise suite breakdown (10 classes, 62 tests):

- Keyboard builders: inline / reply / force-reply / remove
- Media groups (album, JSON + multipart bytes), MIME detection, attachments
- Groups/super-groups/topics/channels via `chat_id`
- Rich messages: reply_to, message_thread_id, silent flag, parse modes
- Edit/delete messages
- Webhook lifecycle: set/delete/getWebhookInfo/getMe/switch_mode
- Webhook URL + `X-Telegram-Bot-Api-Secret-Token` secret validation
- Broadcasting/batching with pacing + dedupe
- Scheduling: `delay_seconds`, absolute `deliver_at`, broadcast scheduling,
  worker TaskHandler `telegram.deliver`
- Security: replay dedup, flood guard, rate limiting, redaction
- Prometheus-like metrics exposition (deps-free)

### Validation engine
```
ruff (hard):                379 violations (baseline 379)  PASS
tsc (hard):                 0 type errors                   PASS
eslint (hard):              0 errors                        PASS
frontend-unit-tests (hard): 122 passed, 0 failed            PASS
unit-tests (hard):          757 passed, 0 failed            PASS
brain-freshness (hard):     PASS
VERDICT: PASS
```

## Configuration (production)

```ini
# .env (gitignored) or platform Secrets — never committed
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_NOTIFICATIONS_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://<host>/webhooks/telegram/update   # optional, webhook mode
TELEGRAM_WEBHOOK_SECRET_TOKEN=<openssl rand -hex 32>            # required when URL set
TELEGRAM_WEBHOOK_MAX_CONNECTIONS=40
TELEGRAM_MODE=auto          # auto | polling | webhook
TELEGRAM_RATE_PER_MINUTE=30
```

Startup guard fails production boot when `TELEGRAM_WEBHOOK_URL` is set but the
secret token is missing/weak.

## Delivery paths

```
NotificationSender.send_telegram(...)
  └─ TelegramNotificationService.send()/…  (shared/notifications/telegram.py)
       └─ https://api.telegram.org/bot<token>/<method>

EnterpriseTelegramService (backend/app/notifications/telegram_enterprise.py)
  ├─ send / broadcast / batch            → immediate CircuitBreaker-bound delivery
  └─ schedule / schedule_broadcast        → TaskPayload("telegram.deliver") via TaskWorker

Webhook ingress:
  POST /webhooks/telegram/update
    → X-Telegram-Bot-Api-Secret-Token (constant-time) → replay guard → rate limit
    → 200 {ok, update_id}   (ingest only; outbound goes through the platform)
```

## Security

- Secrets only from env; startup fail-fast; redacted everywhere.
- Constant-time secret compare (`hmac.compare_digest`).
- Replay dedup by `update_id`; per-IP rate limiting; per-chat flood guard.
- No log includes the token/URL; error strings redacted.
- OWASP ASVS-aligned; no structural secrets added to the repo.

## Production readiness

- Offline-safe: queue fallback to in-process when Redis is down.
- Non-blocking: webhook ingest never performs outbound sends.
- Replaceable: transport stays in `shared`; orchestrator only composes
  existing primitives (task queue, CircuitBreaker, audit). Mirror of
  ADR-011/012 provider pattern.

## Recommended production db-check for operators
Deploy, then: set webhook via `set_webhook`, POST a synthetic update with the
secret header, confirm `200` (403 on bad signature) and counters increment,
check `/metrics`.