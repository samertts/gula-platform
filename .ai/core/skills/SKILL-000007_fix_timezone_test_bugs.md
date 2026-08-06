---
id: SKILL-000007
type: skill
title: "Fix Python Timezone Test Bugs"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [timezone, datetime, python, testing, utc]
related_skills: [SKILL-000003]
related_playbooks: []
---

# SKILL-000007: Fix Python Timezone Test Bugs

## Problem
Tests fail intermittently due to timezone mismatches between
`datetime.now(UTC)` and `date.today()` in +03:00 timezone.

## Symptoms
```
assert datetime(2026, 8, 4, 14, 30, tzinfo=UTC) == date(2026, 8, 4)
# Fails because datetime has time component
```

Or date comparison fails near midnight when UTC and local date differ.

## Environment
- Python 3.12
- Timezone: +03:00 (Iraq)
- Tests: `test_metrics_service.py`

## Root Cause
Test uses `datetime.now(UTC)` for "today" but compares against
`date.today()` which returns local date. In +03:00 timezone,
UTC midnight = 03:00 local, so dates differ for 3 hours.

## Solution
Use consistent time representation:

```python
# Before (timezone mismatch):
from datetime import datetime, UTC
today = datetime.now(UTC).date()  # UTC date

# After (consistent):
from datetime import datetime
today = datetime.now().date()  # Local date
```

Or if UTC is required:
```python
today = datetime.now(UTC).date()
# Ensure assertion also uses UTC
```

## Files Modified
- `backend/tests/unit/test_metrics_service.py`

## Verification
```bash
cd backend && .venv/bin/python -m pytest tests/unit/test_metrics_service.py -v
```

## Rollback
`git checkout -- tests/unit/test_metrics_service.py`

## Lessons Learned
- Never mix `datetime.now(UTC)` and `date.today()` in comparisons
- Choose one: either all-UTC or all-local
- In +03:00 timezone, UTC and local dates differ 3 hours/day
- Run tests at different times of day to catch timezone bugs

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial from PROGRAM-BACKEND-001 |
