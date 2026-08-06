---
id: SKILL-000006
type: skill
title: "Optimize Pytest DDL Setup Time"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [pytest, performance, ddl, testing, conftest]
related_skills: [SKILL-000003]
related_playbooks: []
---

# SKILL-000006: Optimize Pytest DDL Setup Time

## Problem
Pytest session setup is slow because conftest.py creates all database
tables from all SQLAlchemy Base metadata, including dormant bounded
context tables that no tests use.

## Symptoms
- Auth test setup takes 145s+
- Total test run takes 200s+
- `conftest.py` `_session_engine` fixture is slow
- Many "table already exists" warnings

## Environment
- PostgreSQL 16
- SQLAlchemy with multiple bounded contexts (Base, FinBase, GovernanceBase, IdentityBase)
- 281 tables total, but tests only need ~40

## Root Cause
`_session_engine` fixture binds ALL metadata bases to the test engine.
13 dormant bounded context bases create tables that no test uses,
wasting DDL execution time.

## Solution
Reduce conftest.py `_session_engine` from 16→4 bases:

```python
# Before (16 bases, slow):
bases = [Base, FinBase, GovernanceBase, IdentityBase,
         NationalBase, EHRBase, WorkflowBase, ...]  # 13 more

# After (4 bases, fast):
bases = [Base, FinBase, GovernanceBase, IdentityBase]
```

Also auto-detect missing FK target tables and create stubs:

```python
# Auto-create stub tables for missing FK targets
for table in metadata.tables.values():
    for fk in table.foreign_keys:
        if fk.column.table.name not in metadata.tables:
            # Create stub table
            stub = Table(fk.column.table.name, metadata,
                        Column('id', String, primary_key=True))
```

## Files Modified
- `backend/tests/conftest.py` — `_session_engine` fixture

## Results
- Auth test setup: 145s → 68s (53% reduction)
- Total test run: 203s → 108s (47% faster)

## Verification
```bash
cd backend && time .venv/bin/python -m pytest tests/ -v
```

## Rollback
`git checkout -- tests/conftest.py`

## Lessons Learned
- Only bind metadata bases that tests actually use
- Auto-detect FK dependencies to avoid constraint errors
- Dormant bounded contexts should not pollute test setup
- Measure before and after to prove improvement

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial from PROGRAM-BACKEND-001 |
