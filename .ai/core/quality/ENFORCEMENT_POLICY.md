# Enforcement Policy

**Mission:** PROGRAM-AUTOMATION-001
**Created:** 2026-08-04
**Status:** ACTIVE

---

## Purpose

Automatically reject invalid changes. Nothing bypasses the system.

---

## Automatic Rejection Rules

| Check | Policy | Enforcement |
|---|---|---|
| Broken Registry | REGISTRY.md must be valid and consistent | `enforce_policy.py` / CI |
| Broken Constitution | Constitution must exist and be referenced | `validate_constitution.py` / pre-commit |
| Broken References | No broken links, orphan objects, invalid refs | `validate_knowledge.py` / CI |
| Duplicate IDs | No duplicate artifact IDs | `validate_knowledge.py` / CI |
| Missing Rollback | Every non-trivial change needs rollback | Manual review + traceability |
| Missing Verification | Every change must be verified | Traceability log |
| Missing Documentation | Every change needs documentation | CI / review |
| Missing KUP | Knowledge changes need KUP | KUP workflow |
| Missing RFC | Architecture changes need RFC | RFC workflow |
| Constitution Violations | Never bypass the constitution | Pre-commit + CI |

---

## Enforcement Layers

| Layer | Tool | Scope |
|---|---|---|
| 1. Pre-commit | `.git/hooks/pre-commit` | Local, blocking |
| 2. Pre-push | `.git/hooks/pre-push` | Local, advisory |
| 3. CI | `.github/workflows/ai-governance-enforcement.yml` | Remote, blocking |
| 4. Scheduled | `health_reports.py` | Periodic |

---

## Policy Script

```bash
python3 scripts/enforce_policy.py        # Enforce all policies (exit 1 on FAIL)
python3 scripts/enforce_policy.py --json # JSON output
```

---

## Related

- `.ai/core/quality/STABILITY_POLICY.md` — Stability & change management
- `.ai/core/quality/TECHNICAL_DEBT.md` — Technical debt tracking
- `AI_OPERATING_CONSTITUTION.md` — Supreme authority
