# ADR-019: National Digital Health Ecosystem

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Integration Architect, Platform Architect

---

## Context

The GULA platform must interoperate with an increasingly diverse set of external systems: government health registries, hospital information systems (HIS), pharmacy systems, insurance platforms, national databases, and international health networks. Currently, each integration is built as a point-to-point connection with custom protocols, authentication, and data formats, creating a fragile and unscalable integration landscape.

**Requirements:**
- Protocol-agnostic integration supporting REST, FHIR, HL7 v2, ASTM, SOAP, and custom protocols
- Partner management with onboarding, credentialing, rate limiting, and monitoring
- API gateway with authentication, routing, transformation, and throttling
- Schema registry for contract enforcement and version management
- Event-driven integration with publish/subscribe capabilities
- Integration monitoring with error tracking, latency measurement, and alerting
- Support for both synchronous (API) and asynchronous (event) integration patterns

**Constraints:**
- Must not expose GULA internal services directly to external systems
- Must handle varying levels of partner reliability and availability
- Must support Iraqi data sovereignty — health data must not leave national infrastructure
- Must scale to hundreds of integration partners
- Must maintain backward compatibility for existing integrations

## Decision

Build a **National Digital Health Ecosystem** layer in `national/ecosystem/` using an adapter architecture that decouples external systems from GULA's internal services. Each integration is a plugin-style adapter that handles protocol translation, authentication, and data mapping.

### Architecture

```
+--------------------------------------------------------------+
|               National Digital Health Ecosystem               |
+--------------------------------------------------------------+
|                                                                |
|  +------------+  +------------+  +------------+  +----------+ |
|  | API Gateway|  | Event Bus  |  | Partner    |  | Schema   | |
|  |            |  | (Kafka)    |  | Portal     |  | Registry | |
|  +------+-----+  +------+-----+  +------+-----+  +----+-----+ |
|         |               |               |             |        |
|  +------+---------------+---------------+-------------+----+  |
|  |                  Adapter Framework                       |  |
|  |                                                          |  |
|  |  +----------+  +----------+  +----------+  +--------+  |  |
|  |  | FHIR R4  |  | HL7 v2   |  | ASTM     |  | Custom |  |  |
|  |  | Adapter  |  | Adapter  |  | Adapter  |  |Adapter |  |  |
|  |  +----------+  +----------+  +----------+  +--------+  |  |
|  |                                                          |  |
|  |  +----------+  +----------+  +----------+               |  |
|  |  | SOAP     |  | REST     |  | gRPC     |               |  |
|  |  | Adapter  |  | Adapter  |  | Adapter  |               |  |
|  |  +----------+  +----------+  +----------+               |  |
|  +----------------------+-----------------------------------+  |
|                         |                                      |
|  +----------------------+-----------------------------------+  |
|  |              Core Integration Pipeline                     | |
|  |  Auth -> Rate Limit -> Transform -> Route -> Monitor       | |
|  +----------------------+-----------------------------------+  |
|                         |                                      |
|  +----------------------+-----------------------------------+  |
|  |              National Platform Services                   | |
|  |  EHR | Data Platform | Operations | Intelligence | LIMS  | |
|  +----------------------------------------------------------+  |
|                                                                |
+--------------------------------------------------------------+
```

### Key Design Decisions

1. **Adapter pattern** — Every integration is implemented as an adapter that converts between the external system's protocol/format and GULA's canonical models. Adapters are hot-pluggable and independently deployable.

2. **Gateway as security boundary** — The API Gateway (built on existing nginx infrastructure) is the only entry point for external traffic. It handles authentication (OAuth 2.0, API keys, mTLS), rate limiting, and protocol termination.

3. **Schema registry** — All integration contracts are registered in a schema registry (Confluent Schema Registry or Apicurio). Schema evolution rules (backward/forward compatibility) protect against breaking changes.

4. **Partner portal** — A self-service portal (`national/ecosystem/partner_portal/`) allows partners to register, obtain credentials, view documentation, test integrations in a sandbox, and monitor their usage.

5. **Event-driven integration** — Asynchronous integrations use an event bus (Kafka) for publish/subscribe patterns. Partners consume events relevant to their system without polling.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | API gateway, REST/FHIR adapters, partner authentication | 8 weeks |
| **Phase 2** | Adapter framework, schema registry, monitoring | 8 weeks |
| **Phase 3** | Partner portal, self-service onboarding, sandbox environment | 6 weeks |
| **Phase 4** | Event-driven integration, HL7/ASTM/SOAP adapters, production scale | 8 weeks |

## Consequences

### Positive
- **Protocol-agnostic integration** — Any external system can connect regardless of protocol
- **Partner management** — Self-service onboarding, monitoring, and credentialing at scale
- **API governance** — Schema registry enforces contract compliance and prevents breaking changes
- **Security isolation** — Gateway pattern ensures external systems never touch internal services directly
- **Scalable** — Adapter pattern allows adding new integrations without modifying core platform
- **Monitored** — Full observability into every integration path

### Negative
- **Integration latency** — Adapter pattern adds protocol translation overhead (typically 5-50ms per call)
- **Adapter maintenance** — Each adapter must be maintained and updated as external systems evolve
- **Gateway bottleneck** — API gateway is a potential performance bottleneck and single point of failure
- **Initial complexity** — Setting up the full ecosystem framework requires significant up-front investment

### Risks
- **Partner reliability** — External systems may be unreliable, slow, or unavailable. Mitigated by: circuit breakers on all outbound calls, timeouts with graceful degradation, async fallback patterns.
- **Protocol proliferation** — Too many adapters could become unmanageable. Mitigated by: adapter certification process, deprecation policy for low-usage adapters, prioritizing standards-based protocols.
- **Security surface area** — Each integration expands the attack surface. Mitigated by: mandatory security review for each new adapter, regular penetration testing, strict network segmentation.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 4** — Security-first design; gateway enforces zero-trust
- **Engineering Constitution Section 5** — Modular adapter pattern supports separation of concerns
- **ADR-010** — SNDHS integration becomes a managed adapter within the ecosystem
- **ADR-016** — EHR platform exposes FHIR endpoints through the ecosystem gateway
- **ADR-017** — Data platform consumes and produces events through the event bus
- **Iraqi Data Sovereignty Regulations** — All data remains within national infrastructure
- **FHIR R4 / HL7 v2 / ASTM E1381** — Standards-based interoperability
