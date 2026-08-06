---
id: PLAYBOOK-000004
type: playbook
title: "Fix Python/uv Environment Issues"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [python, uv, venv, pip, backend]
related_skills: [SKILL-000003, SKILL-000006]
related_runbooks: []
estimated_duration: "10 minutes"
---

# PLAYBOOK-000004: Fix Python/uv Environment Issues

## Objective
Resolve Python virtual environment, uv, and pip issues.

## Prerequisites
- [ ] uv installed (`uv --version`)
- [ ] Python 3.12 available (`python3.12 --version`)

## Procedure

### Phase 1: Diagnose (2 min)
```bash
python3.12 --version         # Python available?
uv --version                # uv available?
ls backend/.venv/           # Venv exists?
source backend/.venv/bin/activate && python --version  # Venv works?
```

### Phase 2: Common Fixes (8 min)

**Fix 1: Recreate venv**
```bash
cd backend
rm -rf .venv
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

**Fix 2: Wrong Python version in venv**
```bash
cd backend
rm -rf .venv
uv venv --python 3.12
source .venv/bin/activate
python --version  # Should show 3.12.x
```

**Fix 3: pip conflicts with uv**
```bash
# Don't use pip when uv is available
uv pip install -r requirements.txt  # Instead of pip install
```

**Fix 4: Import errors after install**
```bash
source .venv/bin/activate
uv pip install -e .  # Reinstall in editable mode
```

**Fix 5: Ruff not found**
```bash
# Ruff is installed via snap
ruff --version  # /snap/bin/ruff
```

## Verification
```bash
cd backend
source .venv/bin/activate
python -c "import fastapi; print('OK')"
python -m pytest tests/unit/test_lab_service.py -v --tb=short | head -20
```

## Rollback
```bash
# Restore venv from backup if available
cp -r .venv.bak .venv
```

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation |
