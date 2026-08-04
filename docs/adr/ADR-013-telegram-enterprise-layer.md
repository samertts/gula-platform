# ADR-EX-001: Enterprise Telegram Delivery Layer (PROGRAM-COMM-002A)

- **Status:** Accepted
- **Date:** 2026-08-04
- **Deciders:** Platform Engineering
- **Supersedes/extends:** ADR-012 (Telegram Bot as Production Notification Provider)
- **Related:** ADR-011 (Resend email provider), `docs/architecture/FREE_FIRST_POLICY.md`, `backend/app/tasks/*` (TaskPayload/TaskWorker)

## Context

ADR-012 established the canonical single-message Telegram provider
(`shared/notifications/telegram.py`). OPERATIONS required the same provider to
serve as an enterprise gateway: webhook ingestion, media album/rich-message
delivery, broadcast/batch/scheduled fan-out, channels/forums/topics, and health
visibility — without breaking the existing public API or adding a heavy vendor
SDK.

Gap analysis (approved) identified that every requirement can be met by
composing **existing platform primitives**: the TaskPayload/TaskWorker queue,
the shared CircuitBreaker, the audit service, and the canonical telegram
transport. No new dependency is warranted.

## Decision

1. **Single canonical transport.** All Telegram API calls remain in
   `shared/notifications/telegram.py`. The orchestration layer
   (`backend/app/notifications/telegram_enterprise.py`) only composes
   outbox/queue + circuit breaker + metrics around it.
2. **Webhook ingestion is separate from sending.** `POST /webhooks/telegram/update`
   ingests updates (validated by the secret header, replay-guarded,
   rate-limited); it never sends messages. Outbound sends always go through
   the Communication Platform so observability/circuiting is guaranteed.
3. **Scheduling reuses TaskQueue.** Delayed/broadcast delivery encores a
   `TaskPayload(kind="telegram.deliver")`; the TaskWorker executes the
   registered `@task_handler("telegram.deliver")`. No cron or new worker.
4. **Security by default.** Constant-time secret compare; replay dedup by
   `update_id`; per-IP rate cap; per-chat flood guard; token/URL redacted
   from all logs/errors.
5. **Metrics are deps-free.** in-process counters + `append_prometheus_metrics()`
   rendered by the existing backend Prometheus endpoint — no
   `prometheus_client` dependency in `shared`.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| `python-telegram-bot` framework | Heavy handler/job-queue machinery; duplicates the platform's own task queue; ADR-012 already ruled it out |
| New dedicated Telegram worker process | TaskWorker already exists; new machinery violates reuse |
| Send replies directly inside the webhook route | Bypasses circuit breaking/metrics/audit; violates the sending boundary described above |
| `prometheus_client` in shared | Adds a hard dependency to a dependency-free shared library |

## Consequences

### Positive

- Webhook / broadcast / schedule / album / attachment / keyboard coverage
  with zero lock-in and full replaceability.
- Every delivery path flows through the same circuit breaker + task infra,
  keeping operational behavior predictable.
- Webhook ingress cannot cause accidental outbound sends.

### Negative

- Webhook mode requires the public HTTPS URL + secret to be configured
  correctly; startup guard enforces this in production.
- Telegram delivery reliability is still bounded by Telegram upstream
  availability; email remains the durable fallback (ADR-011).

## Compliance

- PROGRAM-CONSTITUTION-001 (Free First / Open Source First / No Vendor
  Lock-In / Zero Paid Dependency / Reuse Before Build / Local AI First): only
  free, standard, already-in-repo primitives are used; the provider remains
  swappable behind the `shared.notifications` abstraction, mirroring the
  Resend/SMTP pattern from ADR-011.