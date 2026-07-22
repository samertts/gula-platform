# GULA Plugin Constitution

## Plugin Philosophy

GULA is designed as an extensible platform. Third-party developers, health authorities, and enterprise customers should be able to extend GULA without modifying the core platform. Plugins are the mechanism for safe, isolated extension.

## Plugin Types

| Type | Description | Examples |
|------|-------------|----------|
| **Integration** | Connect external systems | FHIR endpoint, IHE adapter, device bridge |
| **Analytics** | Custom dashboards and reports | Lab utilization report, regional disease map |
| **Workflow** | Custom clinical workflows | COVID-19 testing pathway, newborn screening |
| **AI** | Custom AI models | Radiology AI, predictive readmission model |
| **UI** | Custom frontend components | Custom patient summary widget, lab-specific dashboard |
| **Notification** | Custom notification channels | SMS provider, WhatsApp integration |

## Plugin Rules

1. **Plugins never modify core database schema.** Plugins may add their own tables with a unique prefix.

2. **Plugins use published APIs only.** No direct access to internal services, models, or private endpoints.

3. **Plugins are sandboxed.** A misbehaving plugin must not affect the stability or performance of the core platform.

4. **Plugins declare their permissions** at installation time. Users approve the permission grant.

5. **Plugins are versioned** with semantic versioning. Breaking changes require a major version bump.

6. **Plugins can be enabled/disabled per tenant.** Disabling a plugin does not delete its data.

## Plugin Marketplace

7. **GULA Plugin Registry** is the canonical source for published plugins. Plugins are reviewed before listing.

8. **Plugin review** includes security scan, code review, and compatibility verification.

9. **Plugin updates** follow the same review process as new installations.

## Developer SDK

10. **Plugin SDK** provides documented interfaces, testing utilities, and sandboxed runtime.

11. **SDK is versioned** and stable. Backward-incompatible SDK changes are coordinated with plugin developers.

12. **SDK documentation** includes tutorials, API reference, and best practices.
