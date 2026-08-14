# Notifications — Alert & Messaging System

This module handles outbound notifications for the GULA Platform. It includes the core dispatch service, Telegram integration for critical alerts, and the free/self-hosted `ntfy` operational channel.

## Free operational alerts with ntfy

The root `docker-compose.yml` defines ntfy under the optional `monitoring` profile. Start it with:

```bash
docker compose --profile monitoring up -d ntfy
```

The backend can publish to the local service through:

```env
NTFY_BASE_URL=http://ntfy:80
NTFY_TOPIC=gula-ops
NTFY_TOKEN=
```

The shared sender exposes `send_ntfy(message, title, topic, priority, tags)`. The `NotificationService` also accepts `channel="ntfy"`. Use a private topic and enable ntfy authentication for production deployments.

## Privacy boundary

ntfy is intended for operational alerts only. Do not publish patient names, health identifiers, laboratory values, access tokens, passwords, or report contents. Send a short incident identifier and a link to an authenticated internal page instead. Callers remain responsible for removing PHI/PII before sending.

## Verification and user notifications

Email, SMS, and push remain separate adapters. For account verification, prefer WebAuthn/Passkeys and TOTP. Use email only for bounded verification and recovery flows, and treat SMS/WhatsApp as explicitly configured paid fallbacks rather than free defaults.
