# GULA Platform

Arabic-first healthcare platform for Iraqi medical laboratories.

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11+) — Gunicorn + Uvicorn |
| Database | PostgreSQL 16 (SQLAlchemy async) |
| Cache | Redis 7 |
| Gateway | nginx (api-gateway) |
| Auth | JWT (HS256) + RBAC (9 roles x 13 permissions) |
| Frontend | React + Firebase (frontend-v2/) or tRPC SPA (client/) |
| Device Bridge | LabLink-Core (ASTM/HL7 instrument integration) |

## Quick Start

```bash
make up              # Start full stack
make health          # Check liveness
make logs-backend    # Tail backend logs
make shell           # Bash into backend container
```

## Development

```bash
# Run tests
cd backend && python -m pytest tests/ -v

# Lint
ruff check backend/app/

# Type check
mypy backend/app/
```

See `CLAUDE.md` for the full developer guide, architecture, migration policy, and quality gates.

## Architecture (Monolith-First)

```
Internet → nginx (TLS) → api-gateway → gula-backend (FastAPI) → PostgreSQL 16 + Redis 7
```

The backend monolith in `backend/app/` is the production deployment target.
A parallel microservices tree (`services/`) exists for future decomposition.

## Key Documents

- `CLAUDE.md` — Developer guide, architecture, invariants, commands
- `CHANGELOG.md` — Release history
- `docs/` — ADRs, SNDHS spec, architecture docs
- `ARCHITECTURE.md` — Architecture overview

## Project Status

Production-ready. Serving Iraqi medical laboratories.
