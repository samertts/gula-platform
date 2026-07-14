# Contributing to GULA Platform

## Quick Start

```bash
git clone https://github.com/samertts/gula-platform
cd gula-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env  # edit as needed
make up
```

## Development Workflow

1. Make changes
2. Run tests: `cd backend && python -m pytest tests/ -v`
3. Lint: `ruff check backend/app/`
4. Type check: `mypy backend/app/`
5. Verify syntax: `python -m py_compile backend/app/main.py`

## Quality Gates (pre-commit)

Every commit must pass:
- **pytest** — all tests green
- **ruff** — no errors (style warnings OK)
- **mypy** — no type errors
- **bandit** — no security issues

## Code Standards

- Python 3.11+ with `from __future__ import annotations`
- FastAPI async patterns
- SQLAlchemy 2.0 async style (`select()`, not `session.query()`)
- All mutations write to AuditLog
- All patient data queries filter by `lab_id`

## Architecture

See `ARCHITECTURE.md` for the monolith-first deployment model.
See `CLAUDE.md` for the comprehensive developer guide.
