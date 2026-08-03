# Notifications — Alert & Messaging System

This module handles outbound notifications for the GULA Platform. Includes:
`service.py` (core notification dispatch), the **Telegram Bot** provider for
critical alerts and monitoring (`shared/notifications/telegram.py`), and the
Resend-backed production email provider (`shared/notifications/resend.py`).
Supports multi-channel delivery for lab results, critical value alerts, and
system health notifications.

## Email Delivery (production provider: Resend)

Email is delivered through the **Resend API** using the official `resend`
Python SDK. A self-hosted SMTP fallback remains available for environments
without a Resend key.

### Configuration (environment variables ONLY)

| Variable | Purpose | Default |
|----------|---------|---------|
| `RESEND_API_KEY` | Resend API key (https://resend.com/api-keys) | *(required in production)* |
| `EMAIL_FROM` | Sender address (must be a verified domain) | `noreply@gula-platform.org` |
| `RESEND_TIMEOUT_SECONDS` | Per-request timeout for the SDK HTTP client | `30` |
| `RESEND_MAX_RETRIES` | Transient-failure retries (429 / 5xx / network) | `3` |

**Secrets policy:**

- `RESEND_API_KEY` is read **only** from the environment. Put it in `.env`
  for local development or in the hosting platform's
  Secrets/Environment Variables in production.
- It is **never** hardcoded, committed to Git, or written to logs.
- The backend **fails at startup with a clear error** if `RESEND_API_KEY` is
  missing in production (`startup_guard.validate_config()`).
- Never paste an API key into documentation, issues, or pull requests. If a
  key is ever exposed, revoke it immediately in the Resend dashboard and
  rotate to a new one.

### Behavior

- **DI / timeouts:** `ResendEmailClient(api_key, from_email, timeout_seconds,
  max_retries)` — injectable, with a bounded HTTP timeout applied to the SDK.
- **Retries:** exponential backoff for transient failures only (HTTP 429,
  HTTP ≥ 500, network errors). Permanent errors (4xx — invalid key,
  validation) fail immediately without retrying.
- **Logging:** structured — recipient, message id, error type. API keys are
  redacted even from error messages.
- **Graceful degradation:** without a key the client returns a typed
  failure result (no exception, no network call); `NotificationSender`
  falls back to SMTP when a key is absent.

## Telegram Bot (production notification provider)

Critical alerts, monitoring and operational notifications are delivered via
the official **Telegram Bot API** (`https://api.telegram.org`)
through `shared/notifications/telegram.py` — no third-party gateway or SDK
dependency beyond the ones already in the stack (`httpx`).

### Configuration (environment variables ONLY)

| Variable | Purpose | Default |
|----------|---------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) | *(required when enabled)* |
| `TELEGRAM_NOTIFICATIONS_ENABLED` | Master switch for Telegram delivery | `true` |
| `TELEGRAM_TIMEOUT_SECONDS` | Per-request timeout (seconds) | `30` |
| `TELEGRAM_MAX_RETRIES` | Transient-failure retries (428/429 / 5xx / network) | `3` |

> **chat_id is NOT a configuration value.** The recipient (chat, group,
> channel or username) is supplied **dynamically** on every send call, so a
> single bot can target many operational channels.

### Secrets policy

- `TELEGRAM_BOT_TOKEN` is read **only** from the environment (`.env` locally,
  platform Secrets in production). It is **never** hardcoded, committed to
  Git, or written to logs, exceptions, or structured-log fields.
- The backend **fails fast at startup** if `TELEGRAM_BOT_TOKEN` is missing in
  production while `TELEGRAM_NOTIFICATIONS_ENABLED=true`
  (`startup_guard.validate_config()`).
- Never paste a bot token into documentation, issues, or pull requests. If a
  token is ever exposed, revoke it via @BotFather → `/revoke` and re-create.

### Usage

```python
from shared.notifications.sender import NotificationSender

sender = NotificationSender()  # reads TELEGRAM_BOT_TOKEN from env

# chat_id is dynamic — any channel/group/user at any time
sender.send_telegram(chat_id=-1001234567890, text="Critical value: K=6.8 mmol/L",
                     alert_level="critical")
sender.send_telegram(chat_id=-1001234567890, text="All systems healthy",
                     monitoring_service="gula-platform")
sender.send_telegram(chat_id="@ops_channel", text="<b>Report</b> ready", parse_mode="HTML")
```

### Supported message types

| Type | Method | Notes |
|------|--------|-------|
| Plain text | `send_text(chat_id, text)` | No parse mode |
| HTML | `send_html(chat_id, html)` | `parse_mode=HTML` |
| MarkdownV2 | `send_markdown_v2(chat_id, text)` | `parse_mode=MarkdownV2` |
| Photo | `send_photo(chat_id, photo, caption)` | file_id / URL / bytes |
| Document | `send_document(chat_id, doc, caption)` | file_id / URL / bytes |
| File | `send_file(chat_id, file_path)` | reads local file, uploads |
| Alert | `send_alert(chat_id, msg, level)` | info / warning / critical |
| Monitoring | `send_monitoring(chat_id, msg, service)` | tagged health channel |

### Behavior

- **DI / timeouts:** `TelegramNotificationService(bot_token, timeout_seconds,
  max_retries, logger_obj)` — injectable; per-request bounded timeout.
- **Retries:** exponential backoff on transient failures — HTTP 408/429/5xx
  `httpx.HTTPStatusError` and network errors. Permanent (400/401/403/404)
  fail immediately.
- **Logging:** structured — method, chat_id, message_id, error type. Bot
  tokens are redacted from every log line and error/result string.
- **Graceful degradation:** without a token the service returns a typed
  failure (no exception, no network call); `NotificationSender.send_telegram`
  returns `False` and logs that the bot is unconfigured.
