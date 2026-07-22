# GULA Architecture Principles

## Module Architecture

1. **Single Responsibility** — Every module, service, and component has one clearly defined responsibility. If a module needs to be described with "and" (e.g., "handles orders and notifications"), it should be split.

2. **Layered Architecture** — The backend follows a strict three-layer architecture: Routes (API contracts) → Services (business logic) → Models (data access). Business logic never lives in route handlers. Data access never lives in services.

3. **Dependency Direction** — Dependencies point inward. Routes depend on services. Services depend on models. Models depend on nothing within the application. No circular dependencies are permitted.

4. **Isolation** — Modules communicate through well-defined interfaces (APIs, events, service calls). No module directly accesses another module's database tables, internal services, or private state.

5. **Abstraction** — Internal implementation details are never exposed to external consumers. APIs present a stable contract regardless of internal refactoring.

## API Architecture

6. **Contract First** — API contracts are the foundation of integration. Backend implements the contract. Frontend consumes the contract. Both are validated against the contract.

7. **RESTful by Default** — APIs follow REST conventions with consistent resource naming, HTTP methods, status codes, and error formats. GraphQL and gRPC may supplement where justified, not replace.

8. **Versioning** — APIs are versioned through content negotiation or URL prefix. Backward-incompatible changes require a new version. Deprecated versions are supported for a minimum of six months.

9. **Idempotency** — Mutating APIs support idempotency keys. Duplicate requests with the same idempotency key produce the same result without side effects.

10. **Pagination** — List endpoints support cursor-based pagination (preferred for large datasets) and offset pagination (supported for simple lists, max 1000 items). See API Constitution (Article 14.17-18).

## Data Architecture

11. **Single Source of Truth** — Every data element has one authoritative location. Duplicates, caches, and derived data are clearly labeled as such and synchronized.

12. **Tenant Isolation** — Multi-tenant data is isolated at the database query level. Every query filters by tenant context. Cross-tenant access requires explicit authorization.

13. **Audit Trail** — Every data mutation that affects patient care, financial transactions, security-sensitive operations, or access to protected health information is recorded in an immutable audit log.

14. **Encryption** — Patient-identifiable data is encrypted at rest. Sensitive fields (national ID, clinical details) use column-level encryption. All data in transit uses TLS 1.3.

## Frontend Architecture

15. **Backend Authority** — The backend is the single source of truth for permissions, menus, navigation, field visibility, and available actions. The frontend never makes authorization decisions.

16. **Lazy Loading** — Code-splitting and lazy loading ensure that users only download what they need. Initial bundle size is optimized for the first meaningful paint.

17. **Offline Resilience** — The frontend degrades gracefully when offline. Critical workflows (result entry, patient lookup) are supported offline with synchronization when connectivity returns.

## Integration Architecture

18. **Standards-Based** — Integration with external systems follows HL7 FHIR, IHE, ASTM, and HL7 v2 standards. Proprietary adapters are isolated behind a standard integration layer.

19. **Protocol Adapters** — Every external protocol (ASTM, HL7 v2, proprietary) has a dedicated adapter that translates to the internal GULA domain model. Adapters are isolated in `services/device_bridge/`.

20. **Event-Driven** — Asynchronous integration uses the outbox pattern with guaranteed delivery. Events are persisted before publishing. At-least-once delivery semantics are enforced.
