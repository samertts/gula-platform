# ADR-011: Notification Platform Architecture

**Status:** Accepted
**Date:** 2026-07-13
**Deciders:** Engineering Lead

## Context

GULA needs to send notifications across multiple channels (email, SMS, push, WhatsApp, Telegram) for clinical alerts, test results, password resets, and system events. Each channel has different API requirements, reliability characteristics, and configuration needs.

## Decision

Build a multi-channel notification platform with the following layers:
- **Template engine** (`shared/notifications/template.py`) — Manages channel-specific message templates with variable interpolation
- **Sender layer** (`shared/notifications/sender.py`) — Raw delivery to each channel with graceful degradation when APIs are unconfigured
- **Service layer** (`backend/app/notifications/service.py`) — Circuit-broken, auditable, application-level notification service with retry and failure tracking
- **Telegram gateway** (`backend/app/notifications/telegram.py`) — Circuit-broken Telegram integration via gateway pattern

## Alternatives Considered

- **Single monolithic sender** — Rejected due to channel diversity
- **External notification service** — Rejected due to cost and data sovereignty requirements

## Consequences

Positive:
- Channel-agnostic API for business logic
- Graceful degradation when individual channels are unavailable
- Template consistency across channels
- Circuit breaker protection against failing notification services

Negative:
- Multiple configuration surfaces (one per channel)
- Template management requires ongoing maintenance

## References

- `shared/notifications/` — Template engine and senders
- `backend/app/notifications/` — Service layer and gateways
