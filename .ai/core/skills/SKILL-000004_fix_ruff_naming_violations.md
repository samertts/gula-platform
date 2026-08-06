---
id: SKILL-000004
type: skill
title: "Fix Ruff N806/N815/N817 Naming Violations"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [ruff, linting, naming, python, n806, n815, n817]
related_skills: [SKILL-000003]
related_playbooks: []
---

# SKILL-000004: Fix Ruff N806/N815/N817 Naming Violations

## Problem
Ruff reports N806 (variable in function should be lowercase), N815
(mixedCase variable in class scope), N817 (camelCase imported as
variable). These are naming convention violations.

## Symptoms
```
N806  variable `R` in function should be lowercase
N815  mixedCase variable `camelCase` in class scope
N817  camelCase `camelCase` imported as `alias`
```

## Root Cause
- N806: Mathematical conventions (R for result, X for matrix) or
  FHIR/camelCase field names used as variable names
- N815: FHIR resource fields use camelCase (e.g., `patientId`)
- N817: Multiple imports from same module aliased with different names

## Solution

### For N806 (math/FHIR variables)
```python
# If variable is truly needed as uppercase (math convention)
# Add per-file ignore:
# ruff: noqa: N806

# Or rename if possible:
R = compute_result()  # → result = compute_result()
```

### For N815 (FHIR camelCase in classes)
```python
# If class uses FHIR fields, add per-file ignore:
# ruff: noqa: N815

# Or use private attribute:
class Patient:
    _patientId: str  # internal
    patient_id: str  # public API
```

### For N817 (multiple imports)
```python
# Before (N817 violation):
from app.ehr.models import Patient as PatientModel
from app.ehr.models import Encounter as EncounterModel

# After (no violation):
from app.ehr.models import Patient, Encounter
# Use directly: Patient, Encounter
```

### Verify
```bash
cd backend && ruff check . | grep -c "N806\|N815\|N817"
# Should be 0
```

## Files Modified
- Source files with naming violations
- Per-file `# ruff: noqa:` comments where renaming isn't possible

## Verification
```bash
ruff check . --select N806,N815,N817
```

## Rollback
`git checkout -- <modified files>`

## Lessons Learned
- FHIR/camelCase fields require per-file ignores, not global
- Consolidate multiple imports into single statement
- Mathematical conventions (R, X, Y) are valid use cases for uppercase

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial from PROGRAM-BACKEND-001 |
