# Notifications — Alert & Messaging System

This module handles outbound notifications for the GULA Platform. Includes:
`service.py` (core notification dispatch), `telegram.py` (Telegram bot
integration for critical alerts), and the Resend-backed production email
provider (`shared/notifications/resend.py`). Supports multi-channel delivery
for lab results, critical value alerts, and system health notifications.

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
