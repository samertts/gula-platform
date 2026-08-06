# Failure Database

**Mission:** GAIOS-002 Phase 4
**Created:** 2026-08-04
**Status:** Active
**Registry ID:** FAILURE-000001

---

## Purpose

Every failure receives a permanent immutable ID.
Failures document what went wrong, why, and how to prevent recurrence.

---

## Registry

| ID | Failure | Severity | Root Cause | Status |
|---|---|---|---|---|
| FAILURE-000001 | Bash arithmetic trap ((var++)) | LOW | set -e exits on false | Resolved |
| FAILURE-000002 | WSL2 PATH duplication (6 copies) | LOW | Shell config accumulation | Resolved |
| FAILURE-000003 | Broken test imports (14 files) | MEDIUM | Module restructuring | Resolved |
| FAILURE-000004 | Startup coupling (Redis/DB) | MEDIUM | Eager initialization | Resolved |
| FAILURE-000005 | Encryption test failures (2) | LOW | InvalidToken vs ValueError | Resolved |
| FAILURE-000006 | Westgard 2-2s rule unreachable | MEDIUM | Rule ordering bug | Resolved |
| FAILURE-000007 | Timezone test bugs | LOW | datetime.now(UTC) vs date.today() | Resolved |
| FAILURE-000008 | Docker compose broken in WSL | LOW | WSL2 limitation | Documented |

---

## Template

Each failure entry documents:
- **Symptoms:** What was observed
- **Environment:** Where it happened
- **Evidence:** Logs, screenshots, error messages
- **Root Cause:** Why it happened
- **Resolution:** How it was fixed
- **Verification:** How the fix was confirmed
- **Rollback:** How to undo the fix
- **Prevention:** How to prevent recurrence
- **Related Skills:** Skills that address this
- **Related Playbooks:** Playbooks for this
- **Related Incidents:** Incident reports
- **Confidence:** 0-100%

---

## Severity Levels

| Level | Description | Response Time |
|---|---|---|
| CRITICAL | System down, data loss | Immediate |
| HIGH | Major feature broken | 1 hour |
| MEDIUM | Feature degraded | 4 hours |
| LOW | Minor issue | 24 hours |

---

## References

- `.ai/core/incidents/` — Incident reports
- `.ai/core/lessons/` — Learned lessons
- `.ai/core/skills/` — Solutions
- `.ai/core/playbooks/` — Procedures
- `.ai/core/registry/REGISTRY.md` — master registry
