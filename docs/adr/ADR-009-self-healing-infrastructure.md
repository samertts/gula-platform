# ADR-009: Self-Healing Infrastructure

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, Platform Architect, DevOps Lead

## Context

The GULA Platform serves medical laboratories where uptime and data integrity are critical. Database or cache failures should not cause complete system unavailability. The platform needs to detect failures, isolate faulty components, and recover automatically without human intervention.

## Decision

Implement a three-layer self-healing infrastructure: circuit breaker, auto-repair engine, and adaptive concurrency control.

### Layer 1: Circuit Breaker

- **Location:** `backend/app/core/self_healing.py`
- **Purpose:** Isolates failing DB/Redis, flips system to degraded mode
- **Behaviour:** After N consecutive failures, circuit opens and writes are rejected with clear error messages
- **Recovery:** Periodic health checks attempt to close the circuit
- **Middleware:** `DegradedModeMiddleware` rejects writes when DB circuit is open

### Layer 2: Auto-Repair Engine

- **Location:** `backend/app/core/auto_repair.py`
- **Purpose:** Automatic garbage collection, connection pool recycling, reconnection
- **Behaviour:** Runs on a timer, attempts to repair known failure modes
- **Scope:** Memory pressure, connection leaks, stale connections

### Layer 3: Adaptive Concurrency

- **Location:** `backend/app/main.py::_adaptive_concurrency_loop`
- **Purpose:** Dynamically adjusts `_MAX_CONCURRENT` based on DB latency
- **Behaviour:** Halves concurrency on 2 slow DB readings (>300ms), restores after 3 fast (<150ms)
- **Exemption:** Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are never shed

## Alternatives Considered

### 1. External Circuit Breaker (Istio/Envoy)

**Pros:** Service mesh level, no application code changes.
**Cons:** Infrastructure complexity, not available in current Docker Compose deployment.
**Rejected because:** Application-level circuit breaker is simpler to deploy and reason about.

### 2. Manual Incident Response Only

**Pros:** No automation complexity.
**Cons:** Delayed response, human error, unavailable during off-hours.
**Rejected because:** Medical laboratories need 24/7 availability.

### 3. Fixed Concurrency Limit

**Pros:** Simple, predictable.
**Cons:** Wastes capacity during normal operation, insufficient during overload.
**Rejected because:** Adaptive concurrency provides better resource utilisation.

## Consequences

### Positive
- System remains partially available during DB/Redis failures (degraded mode)
- Automatic recovery reduces mean time to repair (MTTR)
- Clinical writes are never shed even under load
- Health alerting (GREEN/YELLOW/RED) provides visibility into system state

### Negative
- Additional code complexity in the request path
- Degraded mode behaviour must be tested and documented
- Circuit breaker parameters need tuning for each deployment

### Neutral
- Self-healing complements, doesn't replace, monitoring and alerting
- Health endpoints (`/health`, `/health/ready`, `/health/deep`) provide visibility
- Watchdog runs every 60s with Telegram/Discord/Slack alerting

## References
- `backend/app/core/self_healing.py` — Circuit breaker and DegradedModeMiddleware
- `backend/app/core/auto_repair.py` — Auto-repair engine
- `backend/app/main.py` — Adaptive concurrency loop, health alert loop
- `QUALITY.md` — Quality gate matrix
- ADR-002: Monolith First Architecture
