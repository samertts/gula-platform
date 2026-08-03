# ADR-012: Telegram Bot as Production Notification Provider

- **Status:** Accepted
- **Date:** 2026-08-03
- **Deciders:** Platform Engineering
- **Related:** ADR-011 (Resend email provider), `docs/architecture/FREE_FIRST_POLICY.md`

## Context

The GULA Platform needs a production-grade notification channel for critical
alerts, monitoring, and operational messages that reach operators without
email infrastructure dependencies. Requirements: official Bot API, env-only
secrets, dynamic `chat_id` (no default recipient configured at startup),
fail-fast startup validation, retries, structured logging, and no secret
leakage.

## Decision

Use the **official Telegram Bot API** (`https://api.telegram.org/bot<token>/…`)
directly over HTTPS with `httpx` (already a platform dependency) as the
production Telegram notification provider, implemented as
`TelegramNotificationService` in `shared/notifications/telegram.py`.

- **No vendor SDK wrapper**: the raw Bot API is stable, well documented, and
  directly usable; adding `python-telegram-bot` or similar would pull in a
  large framework (handlers, webhooks, job queues) the platform does not
  need. This keeps dependencies minimal (Free First / Reuse Before Build).
- **Env-only secrets**: `TELEGRAM_BOT_TOKEN` is read from the environment
  (`backend/app/config.py`, `shared/config/loader.py`). Never hardcoded.
- **Dynamic chat_id**: `chat_id` is a required parameter of every send method
  — there is no `TELEGRAM_DEFAULT_CHAT_ID` config value, so one bot can
  target any channel/group/username per notification.
- **Startup validation**: `startup_guard.validate_config()` fails fast in
  production when `TELEGRAM_BOT_TOKEN` is missing or placeholder-like while
  `TELEGRAM_NOTIFICATIONS_ENABLED=true`.
- **Transport guarantees**: bounded per-request timeout, exponential-backoff
  retries for transient failures only (HTTP 408/429/5xx and network errors),
  permanent errors (400/401/403/404) fail immediately.
- **Secrecy**: bot tokens are redacted from all logs, exception messages, and
  result strings (`redact_secrets`).

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| `python-telegram-bot` library | Full framework with webhook handlers and job queues — far more than needed; adds a heavy dependency |
| Telegram Gateway API (official SMS-send product) | Targets SMS-to-Telegram delivery, not bot-to-user messaging; paid-tier oriented |
| Self-hosted IRC/Matrix bridge | No mobile-first reach comparable to Telegram; higher ops cost |
| Webhook-based incoming bots | Cannot initiate messages to users without first contacts; wrong direction |

Telegram itself is a free, self-hostable-friendly consumer platform; the bot
API has no per-message cost, satisfying Free First and Zero Paid Dependency.

## Consequences

### Positive

- Critical alerts and monitoring reach operators instantly on mobile.
- One bot token + dynamic `chat_id` covers all operational channels without
  redeploys.
- Fail-fast startup guard prevents silent alert loss in production.
- No new third-party SDK dependency; `httpx` is already in `requirements.txt`.

### Negative

- Delivery depends on Telegram availability (acceptable for an alerting
  channel; email remains the durable fallback via `NotificationSender`).
- Bot tokens are long-lived credentials; they must be rotated via
  @BotFather if ever exposed.

## Compliance

- PROGRAM-CONSTITUTION-001 (Free First, Open Source First, No Vendor
  Lock-In, Zero Paid Dependency): Telegram Bot API is free; the client
  abstraction mirrors the Resend/SMTP pattern so the provider is
  replaceable.
- Security policy: token env-only, redacted from logs, never committed.
