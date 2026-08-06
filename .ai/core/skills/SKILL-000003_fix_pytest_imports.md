---
id: SKILL-000003
type: skill
title: "Fix Failing Pytest Imports"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [pytest, imports, python, testing, backend]
related_skills: [SKILL-000004, SKILL-000006]
related_playbooks: []
---

# SKILL-000003: Fix Failing Pytest Imports

## Problem
Pytest fails with ImportError or ModuleNotFoundError when running tests.
Common in the GULA backend after module restructuring or service extraction.

## Symptoms
```
ImportError: cannot import name 'evaluate_westgard' from '...'
ModuleNotFoundError: No module named 'app.quality_control'
E   ImportError: cannot import name '_get_permissions' from '...'
```

## Environment
- Python 3.12
- pytest (via .venv)
- Backend: `backend/app/` with capabilities pattern

## Root Cause
Service extraction moved functions between modules. Test files still
import from old locations. Common patterns:
- Function moved from route to service
- Helper moved from utils to service
- Class renamed or reorganized

## Solution

### Step 1: Identify broken imports
```bash
cd backend
.venv/bin/python -m pytest tests/ --collect-only 2>&1 | grep "ImportError\|ModuleNotFoundError"
```

### Step 2: Find correct import path
```bash
# Find where the function actually lives
grep -r "def evaluate_westgard" app/
grep -r "def _get_permissions" app/
```

### Step 3: Fix the import
```python
# Before (broken)
from app.quality_control.westgard import evaluate_westgard

# After (fixed)
from app.services.quality_control_service import evaluate_westgard
```

### Step 4: Verify
```bash
.venv/bin/python -m pytest tests/ --collect-only 2>&1 | grep "ImportError" | wc -l
# Should be 0
```

## Files Modified
- `backend/tests/unit/test_*.py` — import statements

## Verification
```bash
cd backend && .venv/bin/python -m pytest tests/unit/ -v
```

## Rollback
`git checkout -- tests/unit/test_*.py`

## Lessons Learned
- After service extraction, always run `pytest --collect-only` to check imports
- Grep for the function name to find its new location
- Keep imports organized: stdlib → third-party → local

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial from PROGRAM-BACKEND-001 |
