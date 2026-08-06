# Capability Registry

**Mission:** GAIOS-002 Phase 2
**Created:** 2026-08-04
**Status:** Active
**Registry ID:** CAPABILITY-000001

---

## Purpose

Every system capability receives a permanent immutable ID.
Capabilities document what the system CAN do, not how it does it.

---

## Registry

| ID | Capability | Module | Risk | Confidence |
|---|---|---|---|---|
| CAP-000001 | Lab Management | backend/app/routes/lab.py | LOW | 95% |
| CAP-000002 | Sample Management | backend/app/routes/samples.py | LOW | 95% |
| CAP-000003 | Test Results | backend/app/routes/test_results.py | LOW | 95% |
| CAP-000004 | Quality Control | backend/app/routes/quality_control.py | MEDIUM | 90% |
| CAP-000005 | Dashboard | backend/app/routes/dashboard.py | LOW | 95% |
| CAP-000006 | Statistics | backend/app/routes/stats.py | LOW | 90% |
| CAP-000007 | Admin Management | backend/app/routes/admin.py | HIGH | 85% |
| CAP-000008 | Mobile API | backend/app/routes/mobile.py | MEDIUM | 85% |
| CAP-000009 | Metrics | backend/app/routes/metrics.py | LOW | 90% |
| CAP-000010 | Authentication | backend/app/security/ | HIGH | 90% |
| CAP-000011 | FHIR Integration | backend/app/fhir/ | HIGH | 80% |
| CAP-000012 | Identity Platform | backend/app/niam/ | HIGH | 75% |
| CAP-000013 | National Integration | backend/app/national/ | HIGH | 70% |
| CAP-000014 | Event Bus | backend/app/events/ | MEDIUM | 80% |
| CAP-000015 | Audit Logging | backend/app/audit/ | HIGH | 90% |
| CAP-000016 | Multi-tenancy | backend/app/multi_tenancy/ | HIGH | 85% |
| CAP-000017 | RBAC/ABAC | backend/app/security/ | HIGH | 85% |
| CAP-000018 | Offline-first | frontend-v3/src/ | MEDIUM | 70% |
| CAP-000019 | Arabic-first UI | frontend-v3/src/ | MEDIUM | 80% |
| CAP-000020 | Encryption | shared/security/ | HIGH | 90% |

---

## Template

Each capability entry documents:
- **Purpose:** What the capability does
- **Inputs:** What it needs
- **Outputs:** What it produces
- **Constraints:** Limitations
- **Dependencies:** Required services
- **Supported Tools:** AI tools that can work with it
- **Limitations:** Known gaps
- **Risk Level:** LOW/MEDIUM/HIGH/CRITICAL
- **Confidence:** 0-100%
- **Verification:** How to verify it works
- **Related Skills:** Skills that use this capability
- **Related Playbooks:** Playbooks for this capability
- **Related ADR:** Architecture decisions
- **Version:** Current version

---

## References

- `.ai/core/registry/REGISTRY.md` — master registry
- `.ai/core/index/INDEX.md` — master index
- `docs/architecture/` — architecture docs
- `docs/adr/` — architecture decisions
