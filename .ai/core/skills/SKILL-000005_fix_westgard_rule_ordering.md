---
id: SKILL-000005
type: skill
title: "Fix Westgard Rule Ordering"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [westgard, quality-control, laboratory, clinical]
related_skills: [SKILL-000003]
related_playbooks: []
---

# SKILL-000005: Fix Westgard Rule Ordering

## Problem
Westgard quality control rules must be checked in a specific order.
If 2-2s is checked after 1-2s, it becomes unreachable because 1-2s
triggers first and short-circuits evaluation.

## Symptoms
- 2-2s rule never triggers
- QC flags are missed
- Test `test_westgard_2_2s_rule` fails
- Quality control service reports incorrect flags

## Environment
- Backend: `app/services/quality_control_service.py`
- Tests: `tests/unit/test_quality_control_service.py`

## Root Cause
In the multi-rule evaluation chain, 1-2s (1 two-standard-deviation
violation) is checked before 2-2s (2 consecutive two-SD violations).
Since 1-2s is a subset of 2-2s, it triggers first and returns,
making 2-2s unreachable.

## Solution
Check 2-2s BEFORE 1-2s in the evaluation chain:

```python
# Before (wrong order):
if check_1_2s(results):  # Triggers first, 2-2s never reached
    return "1-2s"
if check_2_2s(results):
    return "2-2s"

# After (correct order):
if check_2_2s(results):  # Check multi-consecutive first
    return "2-2s"
if check_1_2s(results):  # Then check single violation
    return "1-2s"
```

## Files Modified
- `backend/app/services/quality_control_service.py` — rule evaluation order
- `backend/tests/unit/test_quality_control_service.py` — test assertions

## Verification
```bash
cd backend && .venv/bin/python -m pytest tests/unit/test_quality_control_service.py -v -k "westgard"
```

## Rollback
`git checkout -- app/services/quality_control_service.py`

## Lessons Learned
- Westgard rules have strict precedence: 2-2s > 1-2s
- Multi-consecutive rules must be checked before single-violation rules
- Always test rule ordering with known control values

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial from PROGRAM-BACKEND-001 |
