# Known Bugs

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Track active/known bugs separate from resolved failures.
This is a living document of known issues.

---

## Active Bugs

| ID | Title | Severity | Module | Status | Discovered |
|---|---|---|---|---|---|
| (none tracked yet) | | | | | |

---

## Template

```markdown
| ID | Title | Severity | Module | Status | Discovered |
|---|---|---|---|---|---|
| BUG-NNNNNN | [Title] | [LOW/MEDIUM/HIGH/CRITICAL] | [Module] | [Open/In Progress/Won't Fix] | [Date] |
```

---

## Bug Fields

| Field | Description |
|---|---|
| ID | BUG-NNNNNN |
| Title | Short description |
| Severity | LOW/MEDIUM/HIGH/CRITICAL |
| Module | Affected module |
| Status | Open/In Progress/Won't Fix |
| Discovered | Date found |
| Steps to Reproduce | How to trigger |
| Expected | What should happen |
| Actual | What actually happens |
| Workaround | Temporary fix (if any) |
| Related Failures | FAILURE-NNNNNN |

---

## Severity Levels

| Level | Description | Response Time |
|---|---|---|
| CRITICAL | System down, data loss | Immediate |
| HIGH | Major feature broken | 1 hour |
| MEDIUM | Feature degraded | 4 hours |
| LOW | Minor issue | 24 hours |

---

## Rules

1. **Always track** — Every known bug gets an entry
2. **Never hide** — Don't suppress warnings
3. **Always document** — Steps to reproduce
4. **Always link** — Connect to failure records
5. **Always update** — Status changes tracked

---

## Related Knowledge

- `.ai/core/failures/` — Resolved failures
- `.ai/core/lessons/` — Learned lessons

---

## References

- `.ai/core/failures/README.md` — Failure database
