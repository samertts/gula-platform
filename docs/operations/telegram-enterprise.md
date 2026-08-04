# Telegram Enterprise Delivery — Operations Guide

Program: PROGRAM-COMM-002A. Companion to the final report
(`docs/ai/PROGRAM-COMM-002A_REPORT.md`) and ADR-013.

## 1. Modes

`TELEGRAM_MODE=auto` (default) resolves: if `TELEGRAM_WEBHOOK_URL` is set,
webhook mode wins; otherwise polling. Set explicitly to `polling` or `webhook`
to override.

## 2. Configuration

```ini
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_NOTIFICATIONS_ENABLED=true

# Webhook mode (recommended for production billable traffic)
TELEGRAM_WEBHOOK_URL=https://<public-host>/webhooks/telegram/update
TELEGRAM_WEBHOOK_SECRET_TOKEN=<openssl rand -hex 32>
TELEGRAM_WEBHOOK_MAX_CONNECTIONS=40

# Optional tuning
TELEGRAM_MODE=auto
TELEGRAM_RATE_PER_MINUTE=30
```

Secrets (token + webhook secret) must live in environment/platform Secrets —
never in the repo. The startup guard refuses production boot if a webhook URL
is set without a secret.

## 3. Registering the webhook

Once the backend is reachable, register the webhook so Telegram starts pushing
updates (polling and webhook are mutually exclusive):

```python
from shared.notifications.telegram import get_telegram_service
svc = get_telegram_service()
svc.set_webhook("https://<host>/webhooks/telegram/update",
                secret_token="<same secret as TELEGRAM_WEBHOOK_SECRET_TOKEN>")
svc.get_webhook_info()   # → pending_update_count, url, last error
```

To go back to long polling:

```python
svc.delete_webhook()
```

## 4. Health & observability

- `GET /health/deep` — includes a `telegram` component
  (`{ok, configured, network, error}`); an unreachable provider adds
  `telegram_provider_unreachable` to `issues` and can drop grade to F.
- Prometheus `/metrics` includes `telegram_*` counters (`telegram_sends_total`,
  `telegram_errors_total`, `telegram_latency`, `telegram_webhook_received`,
  `telegram_replay_blocked`, `telegram_flood_blocked`, `telegram_rate_limited`,
  `telegram_broadcast_total`, `telegram_media_albums_total`).

## 5. Sending from apps

```python
from app.notifications.telegram_enterprise import EnterpriseTelegramService

svc = EnterpriseTelegramService()

# immediate
svc.send(chat_id="@labops", text="⚠ CRITICAL: humidity < 15%", priority="high")

# broadcast with pacing
svc.broadcast([123, 456, "@labops"], "Shift change", interval_seconds=0.25)

# scheduled (task queue is the source of truth)
await svc.schedule(123, "Morning report", delay_seconds=3600)
await svc.schedule_broadcast([123, 456], "Reminder", deliver_at=UTC_next_06_00)
```

Arrays/media via the shared provider: `send_media_group`, `send_attachment`,
`send_audio/video/voice/animation`, `send_location`, `send_contact`,
`send_edit`, `send_delete`, `build_inline_keyboard`, `build_reply_keyboard`.

## 6. Capacity & rate limits

- Per-request timeout and exponential backoff on transient failures only
  (408/429/5xx/network). Permanent errors fail fast.
- `TELEGRAM_RATE_PER_MINUTE` paces outbound sends; Telegram network constraints
  are respected via the token bucket (`TelegramNetworkSpeed`).
- Uploads are capped at `MAX_MULTIPART_BYTES` (50 MiB).
- Broadcast pacing default 0.25s between recipients; batching 0.1s.

## 7. Rollback

Remove webhook config from the environment (or set `TELEGRAM_MODE=polling`) and
redeploy. All shared-provider methods remain available; no schema or breaking
API change ships with this layer.

## 8. Verification checklist

- [ ] `GET /health/deep` shows `telegram.configured=true` when token set
- [ ] `set_webhook` persists (`getWebhookInfo` returns the URL)
- [ ] fake update to `/webhooks/telegram/update` with correct secret → 200
- [ ] same update replayed → 200 `{replayed: true}` (dedup)
- [ ] wrong secret → 403
- [ ] `/metrics` shows `telegram_sends_total` incrementing after a live send
- [ ] production + webhook URL without secret → startup guard refuses to boot