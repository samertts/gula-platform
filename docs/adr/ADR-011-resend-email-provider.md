# ADR-011: Resend as Production Email Provider

**Status:** Accepted
**Date:** 2026-08-03
**Deciders:** Engineering Lead, DevOps Lead, Security Officer

## Context

The GULA Platform sends transactional email (test results, critical alerts,
password resets, public result notifications). Delivery historically used a
self-hosted SMTP gateway (`SMTP_*` env vars in `shared/notifications/sender.py`)
which had no retry policy, no structured logging, no dependency injection, and
relied on operators running their own MTA. For production reliability at
national scale, a managed transactional email provider was requested.

## Decision

Adopt **Resend** (`resend` Python SDK ≥ 2.35) as the production email provider,
integrated behind the existing notification abstraction:

- New module `shared/notifications/resend.py` — `ResendEmailClient` with
  dependency injection, bounded timeouts, transient-failure retries, structured
  logging, and redaction of API keys.
- `NotificationSender.send_email()` uses Resend when `RESEND_API_KEY` is set,
  and falls back to self-hosted SMTP otherwise (provider swappable — no lock-in).
- `RESEND_API_KEY` is read **only** from the environment; the startup guard
  fails with a clear error in production when it is missing or weak.
- SMTP remains available as the free/self-hosted fallback (constitution
  compliance: no vendor lock-in, self-hosted path preserved).

### Free First Evaluation (PROGRAM-CONSTITUTION-001)

| Alternative | Evaluation | Result |
|-------------|-----------|--------|
| **Self-hosted SMTP (Postfix/Exim)** | Free, but no built-in retries, bounce handling, deliverability monitoring, or SPF/DKIM tuning; requires 24/7 MTA ops at every national site | Rejected as sole production provider; **retained as fallback** |
| **Self-hosted Mailu/Mailcow** | Free OSS mail server suite; still requires domain/DNS/IP reputation management and MTA maintenance; heavier ops footprint | Rejected for transactional volume path; viable for internal mail |
| **LocalSend / in-house relay** | Free; adds a fragile custom component to a national health platform | Rejected — increases attack surface |
| **Resend (free tier)** | 3,000 emails/month free; official maintained SDK; industry-standard deliverability; webhook delivery events | **Accepted** |

**Cost:** free tier covers early production; paid tier is pay-as-you-go and
only engages beyond the free quota. **Migration plan:** provider is isolated
behind `ResendEmailClient`; switching back to SMTP is a configuration change
(`RESEND_API_KEY` unset), no code change.

## Alternatives Considered

### 1. Continue with Self-Hosted SMTP Only

**Pros:** Zero cost, no external dependency.
**Cons:** No retries/backoff, no delivery analytics, MTA maintenance per site,
high deliverability risk for national-scale transactional mail.
**Rejected because:** Not production-ready for the transactional email volume;
kept as fallback instead.

### 2. Other SaaS Providers (SendGrid, Mailgun, Postmark)

**Pros:** Mature products.
**Cons:** Higher cost tiers, less generous free allowances; all are equivalent
SaaS vendors with no self-hosting option.
**Rejected because:** Resend provides a free tier and the official SDK; the
abstraction makes any of these swappable.

## Consequences

### Positive
- Production-grade delivery with retries, timeouts, structured logging
- API key secured in environment/secrets only — never in source or logs
- Startup fails fast with a clear message when the key is missing (production)
- Self-hosted SMTP fallback preserved (no lock-in, constitution-compliant)
- Official maintained SDK (`resend>=2.35.0`)

### Negative
- Transactional email depends on an external API (outage = email unavailable;
  SMTP fallback remains for resilience)
- A paid tier may be required beyond the free quota at national scale

### Mitigations
- `RESEND_TIMEOUT_SECONDS` bounds request latency; retries absorb transient
  API outages; the notification circuit breaker bounds failure storms.
- Migration back to SMTP is a one-line configuration change.
