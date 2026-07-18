# ADR-010: mTLS Decision

**Status:** Accepted
**Date:** 2026-07-18
**Constitutional Basis:** PLATFORM-CONSTITUTION.md §4, CLAUDE.md Security Invariants

## Context

mTLS (mutual TLS) was evaluated as a mechanism for service-to-service authentication within the GULA Platform. It would provide certificate-based, encrypted communication between microservices, the API gateway, and external integrations. The evaluation considered the current monolith-first deployment model, the device bridge integration, and future microservice decomposition.

## Decision

mTLS is **deferred** for internal service-to-service communication. The current architecture uses:

1. **API Gateway (nginx):** Terminates TLS from the internet; forwards to backend on Docker internal network (plain HTTP)
2. **Service-to-service:** JWT bearer tokens for authentication between internal services
3. **Device Bridge:** HMAC-signed payloads with API keys for lab instrument communication
4. **Future microservices:** Will adopt JWT-based auth with short-lived tokens; mTLS will be re-evaluated when microservices are decomposed from the monolith

## Rationale

- **Monolith architecture:** All backend services run in a single process; no inter-process TLS needed
- **Operational complexity:** mTLS adds certificate management, rotation, and revocation overhead without proportional benefit at current scale
- **Existing controls:** JWT + HMAC + network isolation provide sufficient security for the current deployment model
- **Future readiness:** The architecture supports adding mTLS when microservices are extracted, without breaking existing components

## Consequences

- No immediate implementation of mTLS
- API gateway retains TLS termination at the edge
- Internal service auth uses bearer tokens with short expiry
- mTLS requirement will be revisited with ADR when: (a) microservices are deployed across hosts, or (b) third-party integrations require certificate-based auth
- All service-to-service communication still requires authentication (no unauthenticated internal endpoints)

## Compliance

- All internal endpoints require valid JWT or HMAC authentication
- No service listens on an unauthenticated port
- API gateway is the only TLS termination point
