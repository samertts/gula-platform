GULA Diagram Design Integration

Source

Repository:
https://github.com/cathrynlavery/diagram-design

Source skill:
skills/diagram-design

Purpose

This skill is imported as an external engineering foundation for
GULA architecture documentation, technical diagrams, ADRs,
security diagrams, data-flow diagrams, FHIR workflows,
laboratory workflows, deployment diagrams, and system documentation.

Status

EXTERNAL FOUNDATION

This is NOT a GULA-native skill yet.

Rules

1. GULA Constitution takes precedence.
2. GULA Architecture Rules take precedence.
3. GULA Security Policies take precedence.
4. GULA Design System takes precedence.
5. GULA documentation standards take precedence.
6. No external diagram may be treated as authoritative architecture
   without verification against the actual repository.
7. Generated diagrams must not invent components, dependencies,
   data flows, permissions, or infrastructure.
8. Architecture diagrams must be derived from verified repository
   evidence whenever they describe the actual GULA implementation.
9. Patient/clinical data must never be placed into diagrams.
10. Secrets, credentials, tokens, private keys, or sensitive identifiers
    must never appear in generated diagrams.

Intended GULA uses

- System architecture
- Deployment architecture
- Backend architecture
- Data flow
- FHIR workflows
- Laboratory workflows
- Identity flows
- Security boundaries
- Authorization matrices
- Offline synchronization
- Event-driven architecture
- ADR diagrams
- QA and verification documentation

Future

This skill will eventually be evaluated and adapted into:

.opencode/skills/gula/gula-diagrams/

Do not modify the imported skill into a GULA-native implementation
without completing the required audit.
